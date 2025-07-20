import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
import uvicorn
import logging
from typing import TypedDict, List

# --- LangChain/LangGraph Imports for Agent ---
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# NEW: Import for LangChain tools (though we are using StructuredTool, this might be needed for internal bindings)
from langchain.tools.render import format_tool_to_openai_function

from langgraph.graph import StateGraph, END

# --- Tool Imports ---
from tools.weather_info_tool import get_current_weather_tool, get_weather_forecast_tool
from tools.place_search_tool import search_places_of_interest_tool, search_restaurants_tool, search_accommodations_tool
from tools.expense_calculator_tool import calculate_total_cost_tool, calculate_hotel_cost_tool, calculate_daily_budget_tool
from tools.currency_conversion_tool import convert_currency_tool

# --- Prompt Imports ---
from prompt_library.prompt import SYSTEM_PROMPT

# --- 1. Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables.")
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")

app = FastAPI(
    title="GlobalGuide AI Travel Planner API", # <-- Changed this line
    description="Advanced AI-powered travel planning application using Groq LLM and LangGraph."
)

class TravelQuery(BaseModel):
    question: str

# --- 2. Initialize LLM and Tools ---
llm = ChatGroq(
    temperature=0.7,
    model_name="llama3-8b-8192", # Or "mixtral-8x7b-32768"
    api_key=GROQ_API_KEY
)

tools = [
    get_current_weather_tool,
    get_weather_forecast_tool,
    search_places_of_interest_tool,
    search_restaurants_tool,
    search_accommodations_tool,
    calculate_total_cost_tool,
    calculate_hotel_cost_tool,
    calculate_daily_budget_tool,
    convert_currency_tool
]

# --- MODIFIED LLM SETUP ---
# Bind tools directly to the LLM. LangChain will handle adding tool descriptions to the prompt.
llm_with_tools = llm.bind_tools(tools)

# The prompt will be constructed dynamically within the call_llm node,
# using the chat history directly. This avoids prompt template variable issues.


# --- 3. Define the Agent's State and Graph (LangGraph) ---

class AgentState(TypedDict):
    messages: List[dict]

def call_llm(state: AgentState) -> dict:
    logger.info("Agent: Calling LLM node.")
    
    current_messages = []
    # Always start with the system prompt
    current_messages.append({"role": "system", "content": SYSTEM_PROMPT})

    for msg_dict in state["messages"]:
        # Convert dict messages back to a format LLM expects (role-based dicts)
        # Or LangChain Message objects if binding tools works better with them directly
        if msg_dict.get('type') == 'human':
            current_messages.append(HumanMessage(content=msg_dict.get('content', '')))
        elif msg_dict.get('type') == 'ai':
            current_messages.append(AIMessage(content=msg_dict.get('content', ''), tool_calls=msg_dict.get('tool_calls', [])))
        elif msg_dict.get('type') == 'tool':
            # Tool messages need to be formatted correctly for the LLM input
            current_messages.append(ToolMessage(content=msg_dict.get('content', ''), tool_call_id=msg_dict.get('tool_call_id', '')))
        else:
            current_messages.append(msg_dict) # Fallback

    # Direct invoke on the llm_with_tools (which already has tools bound)
    llm_response = llm_with_tools.invoke(current_messages) # Pass the list of messages directly
    
    # Convert the LLM's response to a dictionary for state consistency
    return {"messages": state["messages"] + [llm_response.dict()]}

def call_tool(state: AgentState) -> dict:
    logger.info("Agent: Calling Tool node.")
    
    last_message_dict = state["messages"][-1]
    last_message = AIMessage(content=last_message_dict.get('content', ''), tool_calls=last_message_dict.get('tool_calls', []), id=last_message_dict.get('id'))

    tool_outputs = []

    if not last_message.tool_calls:
        logger.warning("Tool node received no tool calls in last message. This indicates a logic error or unexpected LLM behavior.")
        tool_outputs.append(ToolMessage(content="Error: Agent attempted to call a tool but no tool calls were found in LLM's response.", tool_call_id="error_no_call").dict())
        return {"messages": state["messages"] + tool_outputs}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        raw_tool_args = tool_call["args"]

        logger.info(f"Agent: Executing tool: '{tool_name}' with raw args: {raw_tool_args}")
        
        tool_obj = next((t for t in tools if t.name == tool_name), None)

        if tool_obj:
            try:
                if tool_obj.args_schema:
                    parsed_args = tool_obj.args_schema.model_validate(raw_tool_args).dict()
                else:
                    parsed_args = raw_tool_args

                output = tool_obj._run(**parsed_args)
                tool_outputs.append(ToolMessage(tool_call_id=tool_call["id"], content=output).dict())
                logger.info(f"Agent: Tool '{tool_name}' executed successfully. Output snippet: {output[:100]}...")
            except ValidationError as ve:
                error_msg = f"Validation Error for tool '{tool_name}' with args {raw_tool_args}: {ve.errors()}. LLM provided invalid arguments."
                tool_outputs.append(ToolMessage(tool_call_id=tool_call["id"], content=error_msg).dict())
                logger.error(f"Agent: {error_msg}")
            except Exception as e:
                error_msg = f"Error executing tool '{tool_name}' with args {raw_tool_args}: {e}"
                tool_outputs.append(ToolMessage(tool_call_id=tool_call["id"], content=error_msg).dict())
                logger.error(f"Agent: {error_msg}")
        else:
            error_msg = f"Tool '{tool_name}' not found or not correctly defined."
            tool_outputs.append(ToolMessage(tool_call_id=tool_call["id"], content=error_msg).dict())
            logger.error(f"Agent: {error_msg}")
    return {"messages": state["messages"] + tool_outputs}

# Define the LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("llm", call_llm)
workflow.add_node("tool", call_tool)

workflow.set_entry_point("llm")

def should_continue(state: AgentState) -> str:
    last_message_dict = state["messages"][-1]
    last_message = AIMessage(content=last_message_dict.get('content', ''), tool_calls=last_message_dict.get('tool_calls', []), id=last_message_dict.get('id'))

    if last_message.tool_calls:
        logger.info("Agent: LLM requested tool calls. Transitioning to 'tool' node.")
        return "tool"
    
    if last_message.type == "tool" and "Error:" in last_message.content:
        logger.warning(f"Agent: Tool execution error detected: {last_message.content}. Looping back to LLM for re-evaluation.")
        return "llm" 
    
    logger.info("Agent: LLM generated final answer. Ending graph.")
    return END

workflow.add_conditional_edges(
    "llm",
    should_continue,
    {"tool": "tool", END: END}
)

workflow.add_edge('tool', 'llm')

app_agent = workflow.compile()

logger.info("LangGraph agent compiled successfully.")

# --- 4. FastAPI Endpoint ---
@app.post("/query")
async def process_query(travel_query: TravelQuery):
    try:
        logger.info(f"API: Received query: {travel_query.question}")
        # Initialize the input state with the HumanMessage
        inputs = {"messages": [HumanMessage(content=travel_query.question).dict()]}
        
        final_response_content = "I could not generate a comprehensive travel plan. Please try again or rephrase your request."
        
        all_streamed_messages = []

        for s in app_agent.stream(inputs):
            if '__end__' in s:
                all_streamed_messages.extend(s['__end__']['messages'])
                break
            
            current_step_node = list(s.keys())[0] if s else None
            if current_step_node and current_step_node != '__end__':
                # Append only the new messages from the current step's output
                if 'messages' in s[current_step_node] and len(s[current_step_node]['messages']) > len(all_streamed_messages):
                    all_streamed_messages.extend(s[current_step_node]['messages'][len(all_streamed_messages):])


        found_final_ai_message = False
        for msg_dict in reversed(all_streamed_messages):
            if msg_dict.get('type') == 'ai':
                ai_message_instance = AIMessage(content=msg_dict.get('content', ''), tool_calls=msg_dict.get('tool_calls', []), id=msg_dict.get('id'))
                if ai_message_instance.content and not ai_message_instance.tool_calls:
                    final_response_content = ai_message_instance.content
                    found_final_ai_message = True
                    break
            elif msg_dict.get('type') == 'tool' and msg_dict.get('content') and "Error:" in msg_dict.get('content'):
                final_response_content = f"An error occurred during planning: {msg_dict['content']}. Please try again."
                found_final_ai_message = True
                break
        
        if not found_final_ai_message:
            last_msg_content = "No clear final response from AI."
            if all_streamed_messages:
                last_msg_dict_for_debug = all_streamed_messages[-1]
                last_msg_content = f"Type: {last_msg_dict_for_debug.get('type')}, Content: {last_msg_dict_for_debug.get('content')}, Tool Calls: {last_msg_dict_for_debug.get('tool_calls')}"
            
            final_response_content = (
                "The AI agent processed your request but could not formulate a clear, final answer in the expected format. "
                f"Last known internal message state: {last_msg_content}. "
                "This might indicate an ongoing thought process or an issue with final output generation. Please try rephrasing your request, or review backend logs for more details."
            )

        logger.info("API: Query processed, sending response.")
        return {"answer": final_response_content}
    
    except Exception as e:
        logger.exception("API: Error processing query:")
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. Run the FastAPI application (for direct execution) ---
if __name__ == "__main__":
    logger.info("API: Starting FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
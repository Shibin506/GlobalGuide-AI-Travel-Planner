import streamlit as st
import requests
import json

# Configuration for the FastAPI backend
FASTAPI_BASE_URL = "http://localhost:8000" # Ensure this matches where your FastAPI app is running

st.set_page_config(page_title="GlobalGuide AI Travel Planner", layout="centered")

st.title("✈️ GlobalGuide AI Travel Planner 🗺️")
st.markdown(
    """
    Welcome to your AI-powered travel planning assistant!
    Enter your travel request below, and GlobalGuide AI will generate a personalized itinerary for you.
    """
)

# User input for the travel query
user_query = st.text_area(
    "Tell me about your trip plans (e.g., 'Plan a 7-day trip to Bali for 2 people with a budget of $2000, focusing on beaches and local food.', 'A 3-day weekend in Paris focusing on art museums.', 'What's the weather like in Tokyo next week?')",
    height=150,
    placeholder="E.g., Plan a 5-day family trip to Tokyo, Japan in October, budget $3000, for 4 people, including theme parks and cultural sites."
)

# Button to submit the query
if st.button("Generate Travel Plan 🚀"):
    if user_query:
        with st.spinner("GlobalGuide AI is crafting your personalized travel plan... This may take a moment."):
            try:
                # Make a POST request to your FastAPI backend
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/query",
                    json={"question": user_query},
                    timeout=300 # Set a timeout (5 minutes) for potentially long LLM calls
                )

                if response.status_code == 200:
                    data = response.json()
                    st.subheader("✨ Your Personalized Travel Plan ✨")
                    # Use st.markdown to render the response, assuming it's in Markdown format
                    st.markdown(data.get("answer", "No plan generated. Please try again or rephrase your request."))
                else:
                    st.error(f"Error from backend: {response.status_code} - {response.text}")
                    st.json(response.json()) # Display full JSON for debugging if available
            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Could not connect to the FastAPI backend at {FASTAPI_BASE_URL}. Please ensure the backend server is running.")
            except requests.exceptions.Timeout:
                st.error("The request timed out. The AI took too long to generate a response. Please try again with a simpler query or check the backend logs.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter your travel request to generate a plan.")

st.markdown("---")
st.markdown("Powered by Groq LLM and LangGraph.")
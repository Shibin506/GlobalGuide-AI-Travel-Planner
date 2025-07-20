# GlobalGuide-AI-Travel-Planner

<img width="1495" height="966" alt="image" src="https://github.com/user-attachments/assets/a40ac565-d9ff-4786-8cd8-1ffa55ce5f5d" />


Markdown

# ✈️ GlobalGuide AI Travel Planner 🗺️

**Your Intelligent Travel Companion for Effortless Personal Trip Planning.**

---
## 🚀 Project Overview

The **GlobalGuide AI Travel Planner** is an advanced, AI-powered application designed to revolutionize personalized trip planning. Leveraging cutting-edge language models and real-time data, it seamlessly creates detailed, highly customized travel itineraries, making complex trip organization effortless for users. Built with a modern agentic workflow architecture, GlobalGuide AI goes beyond simple recommendations, offering comprehensive trip planning that includes attractions, accommodations, dining, activities, transportation, real-time weather forecasts, and detailed cost breakdowns.

---

## ✨ Key Features

* **Intelligent AI Agent:** At its core, the application is powered by **Groq LLM**, integrated within a sophisticated **agentic workflow architecture built with LangGraph**. This enables complex reasoning, dynamic tool selection, and multi-step problem-solving to generate truly personalized plans.
* **Comprehensive Real-Time Data Integration:**
    * **Live Weather Information:** Fetches current weather and 5-day forecasts for any destination using **OpenWeatherMap API**.
    * **Extensive Place Search & Discovery:** Utilizes the **Google Places API** to identify popular attractions, hidden gems, diverse dining options, and suitable accommodations based on user interests and location.
    * **Smart Financial Planning:** Includes an **Expense Calculator** for detailed cost breakdowns, a **Hotel Cost Estimator**, and a **Daily Budget Calculator**.
    * **Real-time Currency Conversion:** Provides accurate exchange rates for international trips via the **ExchangeRate-API**.
* **Robust & Scalable Architecture:**
    * **Agentic Workflow:** Employs **LangGraph** to orchestrate a dynamic, multi-step planning process, allowing the AI to autonomously decide which tools to use and when, based on the user's request and tool outputs. This demonstrates understanding of advanced AI system design.
    * **Dual Interface:** Features a high-performance **FastAPI backend** for API logic and AI processing, coupled with an interactive and user-friendly **Streamlit frontend** for a seamless web experience. This showcases full-stack development capability.
* **Modular & Extensible Design:** Tools are implemented as distinct `StructuredTool` classes, making the system highly modular, testable, and easily extensible with new functionalities.

---

## 🏗️ Architecture


graph TD
    A[User Query (Streamlit)] --> B(AI Agent);
    B -- LangGraph Orchestration --> C{Decide Action};
    C -- Tool Call --> D(Tool Execution);
    D -- API Calls (Weather, Places, Currency, etc.) --> E[Tool Output];
    E --> B; // Loop back to AI Agent with tool output for further reasoning
    C -- Final Answer --> F[Comprehensive Travel Plan];
    F --> A; // Sent back to User (Streamlit)
🛠️ Available Tools
The AI agent is equipped with a suite of specialized tools to fulfill diverse planning needs:
**
**🌤️ Weather Information:
****

get_current_weather: Real-time temperature, conditions, and descriptions for a location.

get_weather_forecast: 5-day weather predictions for trip planning. (Always 5 days as simplified for robustness).

**🏛️ Place Search & Discovery (via Google Places API):**

search_places_of_interest: Find popular tourist spots, landmarks, and hidden gems.

search_restaurants: Discover dining options with price ranges.

search_accommodations: Find hotels, hostels, and other lodging options.

**💰 Financial Planning:**

calculate_total_cost: Sums up a list of individual costs for trip expenses.

calculate_hotel_cost: Estimates total accommodation costs based on per-night price and number of nights.

calculate_daily_budget: Divides a total budget by the number of days to get a daily allowance.

**💱 Currency Conversion (via ExchangeRate-API):**

convert_currency: Provides real-time exchange rates to convert amounts between different currencies.

**🚀 Quick Start
Follow these steps to get GlobalGuide AI up and running on your local machine.

Prerequisites**
Python 3.10 or higher

API keys for external services: You'll need keys for Groq, OpenWeatherMap, Google Places, and ExchangeRate-API. (See Configuration below for details).

Installation
Clone the repository:

Bash

git clone [https://github.com/Shibin506/GlobalGuide-AI-Travel-Planner.git](https://github.com/Shibin506/GlobalGuide-AI-Travel-Planner.git)
cd GlobalGuide-AI-Travel-Planner
Create and activate a Python virtual environment:


Create a .env file in the root of your project directory (GlobalGuide-AI-Travel-Planner/) and populate it with your API keys.

# Required for weather data
OPENWEATHERMAP_API_KEY=your_openweathermap_key
# Required for place search (Google Places API)
GPLACES_API_KEY=your_google_places_key
# Required for currency conversion
EXCHANGE_RATE_API_KEY=your_exchange_rate_key
# Required for AI model (Groq)
GROQ_API_KEY=your_groq_key
# Optional: Tavily API for fallback search (if integrated)
TAVILY_API_KEY=your_tavily_key
Remember: Keep your .env file secret and never commit it to public repositories. It's listed in .gitignore.

Running the Application
GlobalGuide AI runs with a separate backend (FastAPI) and frontend (Streamlit). You will need two separate terminal windows.

Start the Backend Server (Terminal 1):

Navigate to your project's root directory.

Activate your virtual environment.

Run:

Bash

python main.py
The FastAPI server will be available at http://localhost:8000. Keep this terminal running.

Start the Streamlit Frontend (Terminal 2):

Open a new terminal window.

Navigate to your project's root directory.

Activate your virtual environment.

Run:

Bash

streamlit run streamlit_app.py
Your web browser should automatically open to http://localhost:8501 (or a similar port) to access the web interface.

📖 Usage Examples
Once both the backend and frontend are running, visit http://localhost:8501 in your browser and enter your travel queries.

Example 1: Comprehensive Trip Planning

Plan a 7-day trip to Bali, Indonesia for 2 people with a budget of $2000, focusing on beaches and local food.
Response includes: Day-by-day itinerary with locations, hotel recommendations, restaurant suggestions, transportation options, weather forecast, detailed cost breakdown, and currency conversion.

Example 2: Specific City Exploration

Plan a 3-day weekend trip to Paris, France focusing on art and culture.
Response includes: Museum and gallery recommendations, cultural activities, traditional French restaurants, metro and walking routes, and weather-appropriate activities.

Example 3: Simple Weather Query

What is the current weather in London and the 5-day forecast?
Response includes: Current conditions and a 5-day weather summary.

📞 API Endpoints
The FastAPI backend exposes the following primary endpoint:

POST /query

Description: Submits a travel planning request to the AI agent.

Request Body:

JSON

{
  "question": "Plan a 5-day trip to Tokyo, Japan"
}
Response Body:

JSON

{
  "answer": "Comprehensive travel plan in markdown format..."
}
🎥 Demo
(You can upload your Demo-video.gif to your GitHub repo's root and link it here, or directly embed it if GitHub supports it.)

Add link to your demo video here. For example:
https://github.com/Shibin506/GlobalGuide-AI-Travel-Planner/blob/main/Demo-video.gif
(Ensure this is the correct path to your GIF/video once uploaded)

🚀 Development & Contribution
We welcome contributions! If you'd like to extend this project, consider:

Adding New Tools: Create new StructuredTool classes in the tools/ directory for additional functionalities (e.g., flight search, public transport routes).

Enhancing Agent Reasoning: Refine prompts and LangGraph nodes for more sophisticated decision-making and error recovery.

Improving UI/UX: Enhance the Streamlit frontend with more interactive elements or visualizations.

**Development Setup
To set up your development environment:

Fork the repository.**

Create a feature branch: git checkout -b feature/your-awesome-feature

Commit your changes: git commit -m 'Add your awesome feature'

Push to the branch: git push origin feature/your-awesome-feature

Open a Pull Request to the main branch.

**📄 License**

This project is licensed under the MIT License. You can find the full license text in the LICENSE file in this repository.
**
🙏 Acknowledgments**

LangChain: For the powerful LLM framework.

LangGraph: For the robust agentic workflow capabilities.

Groq: For the fast and efficient LLM inference.

Streamlit: For the beautiful and easy-to-use web interface.

FastAPI: For the robust backend API development.

OpenWeatherMap, Google Places, ExchangeRate-API: For providing real-time data.

(Optional: Add any other libraries or resources that significantly helped you.)

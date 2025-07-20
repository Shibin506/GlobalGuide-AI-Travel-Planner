import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import BaseTool, StructuredTool # <-- Use BaseTool and StructuredTool
from pydantic import BaseModel, Field
import datetime # For accurate date filtering in forecast

# Load environment variables
load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

if not OPENWEATHERMAP_API_KEY:
    raise ValueError("OPENWEATHERMAP_API_KEY not found in environment variables. Please check your .env file.")

# --- Define Pydantic Schemas for Tool Inputs ---

class CurrentWeatherInput(BaseModel):
    """Input schema for the get_current_weather tool."""
    location: str = Field(description="The city or location to get current weather for (e.g., 'London, UK')")

class WeatherForecastInput(BaseModel):
    """Input schema for the get_weather_forecast tool (always 5 days)."""
    location: str = Field(description="The city or location to get the 5-day weather forecast for (e.g., 'Paris')")


# --- Internal Helper Functions (no @tool decorator here) ---

def _get_current_weather_func(location: str) -> str:
    """
    Internal function to fetch the current weather conditions.
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == "404":
            return f"Error: Location '{location}' not found. Please provide a valid city name."
        if data.get("cod") != 200:
            return f"Error fetching weather for {location}: {data.get('message', 'Unknown error from API')}"

        main_data = data["main"]
        weather_desc = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]

        report = (
            f"Current weather in {location}:\n"
            f"Temperature: {main_data['temp']}°C (Feels like: {main_data['feels_like']}°C)\n"
            f"Conditions: {weather_desc.capitalize()}\n"
            f"Humidity: {main_data['humidity']}%\n"
            f"Wind Speed: {wind_speed} m/s"
        )
        return report
    except requests.exceptions.RequestException as e:
        return f"Network error or invalid request for {location}: {e}. Check your internet connection or API key."
    except Exception as e:
        return f"An unexpected error occurred while processing weather for {location}: {e}"

def _get_weather_forecast_func(location: str) -> str:
    """
    Internal function to fetch the 5-day weather forecast.
    """
    days = 5 # Fixed to 5 days as per previous decision

    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": location,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == "404":
            return f"Error: Location '{location}' not found for forecast. Please provide a valid city name."
        if data.get("cod") != "200":
            return f"Error fetching forecast for {location}: {data.get('message', 'Unknown error from API')}"

        forecast_summary = f"Weather forecast for {location} for {days} days:\n"
        daily_forecasts = {}

        for item in data["list"]:
            date = item["dt_txt"].split(' ')[0]
            temp = item["main"]["temp"]
            desc = item["weather"][0]["description"]

            if date not in daily_forecasts:
                daily_forecasts[date] = {"min_temp": temp, "max_temp": temp, "descriptions": set()}
            else:
                daily_forecasts[date]["min_temp"] = min(daily_forecasts[date]["min_temp"], temp)
                daily_forecasts[date]["max_temp"] = max(daily_forecasts[date]["max_temp"], temp)
            daily_forecasts[date]["descriptions"].add(desc)

        today_str = datetime.date.today().isoformat()
        relevant_dates = [d for d in sorted(daily_forecasts.keys()) if d >= today_str][:days]

        if not relevant_dates:
            return f"Could not generate a valid forecast for {location} for {days} days. It might be too far in the past or the API did not return enough data."

        for date in relevant_dates:
            min_temp = daily_forecasts[date]["min_temp"]
            max_temp = daily_forecasts[date]["max_temp"]
            descriptions = ", ".join(sorted(list(daily_forecasts[date]["descriptions"])))
            forecast_summary += (
                f"  Date: {date}\n"
                f"  Min Temp: {min_temp:.1f}°C, Max Temp: {max_temp:.1f}°C\n"
                f"  Conditions: {descriptions.capitalize()}\n"
                "----------------------------------\n"
            )
        return forecast_summary.strip()

    except requests.exceptions.RequestException as e:
        return f"Network error or invalid request for {location}: {e}. Check your internet connection or API key."
    except Exception as e:
        return f"An unexpected error occurred while processing forecast for {location}: {e}"


# --- Define Tools as StructuredTool Classes ---

class GetCurrentWeatherTool(StructuredTool):
    name: str = "get_current_weather"
    description: str = """Fetches the current weather conditions for a specified city or location.
    Returns temperature, description, humidity, and wind speed.
    The location should be a city name, optionally followed by a country code (e.g., "London, UK")."""
    args_schema: type[BaseModel] = CurrentWeatherInput
    def _run(self, location: str) -> str:
        return _get_current_weather_func(location)
    async def _arun(self, location: str) -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

class GetWeatherForecastTool(StructuredTool):
    name: str = "get_weather_forecast"
    description: str = """Fetches the 5-day weather forecast for a specified city or location.
    Returns a summary of conditions for each day.
    The location should be a city name, optionally followed by a country code (e.g., "Paris").
    This tool always provides a 5-day forecast."""
    args_schema: type[BaseModel] = WeatherForecastInput
    def _run(self, location: str) -> str:
        return _get_weather_forecast_func(location)
    async def _arun(self, location: str) -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")


# --- Instantiate the tools for use ---
get_current_weather_tool = GetCurrentWeatherTool()
get_weather_forecast_tool = GetWeatherForecastTool()


# --- Testing Block (runs only when this file is executed directly) ---
if __name__ == "__main__":
    print("--- Testing Current Weather ---")
    london_weather = get_current_weather_tool._run(location="London, UK")
    print(london_weather)

    print("\n--- Testing Weather Forecast (5 days default) ---")
    tokyo_forecast = get_weather_forecast_tool._run(location="Tokyo")
    print(tokyo_forecast)

    print("\n--- Testing Invalid Location (Current Weather) ---")
    invalid_weather = get_current_weather_tool._run(location="InvalidCityName123")
    print(invalid_weather)

    print("\n--- Testing Invalid Location (Forecast) ---")
    invalid_forecast = get_weather_forecast_tool._run(location="NonExistentCityXYZ")
    print(invalid_forecast)
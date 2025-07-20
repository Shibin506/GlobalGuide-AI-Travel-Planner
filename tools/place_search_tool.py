import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import BaseTool, StructuredTool # <-- MODIFIED: Use BaseTool and StructuredTool
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

GPLACES_API_KEY = os.getenv("GPLACES_API_KEY")

if not GPLACES_API_KEY:
    raise ValueError("GPLACES_API_KEY not found in environment variables. Please check your .env file.")

# --- Pydantic Schemas for Tool Inputs ---
# These are the same as before, they define the expected input structure for the tools.

class PlaceSearchInput(BaseModel):
    """Input schema for place search tools."""
    search_string: str = Field(description="A descriptive string for the search, combining what and where (e.g., 'Italian restaurants in Rome', 'famous museums in London', 'budget hotels in Paris').")
    radius: int = Field(default=5000, description="Search radius in meters (default 5000 meters = 5km). Max 50000.")
    type_filter: str = Field(default="", description="Optional: specific Google Place type to filter results (e.g., 'restaurant', 'museum', 'lodging').")


# --- Internal Helper Function (no change) ---
def _perform_google_places_search(search_text_combined: str, category: str, radius: int, type_filter: str) -> str:
    """
    Internal helper function to perform the actual Google Places API (Text Search) call.
    Uses the combined search_text_combined string directly.
    """
    if radius > 50000:
        return "Error: Maximum search radius allowed is 50,000 meters."

    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": search_text_combined,
        "key": GPLACES_API_KEY,
        "radius": radius,
        "type": type_filter if type_filter else category
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "ZERO_RESULTS" or not data["results"]:
            return f"No results found for '{search_text_combined}' with type '{type_filter if type_filter else category}' within {radius/1000}km."
        elif data["status"] != "OK":
            return f"Error from Google Places API: {data.get('error_message', data['status'])}. Check API key or query."


        results_summary = f"Top {min(len(data['results']), 5)} results for '{search_text_combined}' (category: {type_filter if type_filter else category}):\n"
        for i, place in enumerate(data["results"]):
            if i >= 5:
                break
            name = place.get("name", "N/A")
            address = place.get("formatted_address", "N/A")
            rating = place.get("rating", "N/A")
            price_level = place.get("price_level", "N/A")

            price_str = ""
            if isinstance(price_level, int):
                price_str = "$" * price_level

            results_summary += (
                f"  {i+1}. Name: {name}\n"
                f"     Address: {address}\n"
                f"     Rating: {rating}/5\n"
                f"     Price Level: {price_str if price_str else 'N/A'}\n"
                "----------------------------------\n"
            )
        return results_summary.strip()

    except requests.exceptions.RequestException as e:
        return f"Network error or invalid request to Google Places API: {e}. Check internet connection or API key setup."
    except Exception as e:
        return f"An unexpected error occurred while searching for places: {e}"


# --- Define Tools as StructuredTool Classes ---

class SearchPlacesOfInterestTool(StructuredTool):
    name: str = "search_places_of_interest"
    description: str = """Searches for places of interest like attractions, landmarks, or general points of interest.
    Provides details like name, address, rating, and a brief description.
    Example search_string: 'best parks in New York', 'historical sites in Kyoto'."""
    args_schema: type[BaseModel] = PlaceSearchInput # Assign the Pydantic schema
    def _run(self, search_string: str, radius: int = 5000, type_filter: str = "") -> str:
        return _perform_google_places_search(search_string, "point_of_interest", radius, type_filter)
    async def _arun(self, search_string: str, radius: int = 5000, type_filter: str = "") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

class SearchRestaurantsTool(StructuredTool):
    name: str = "search_restaurants"
    description: str = """Searches for restaurants based on cuisine, type, or specific names.
    Provides details like name, address, rating, and price level.
    Example search_string: 'Italian food in Rome', 'cafes with wifi in Berlin', 'sushi near me in Tokyo'."""
    args_schema: type[BaseModel] = PlaceSearchInput
    def _run(self, search_string: str, radius: int = 5000, type_filter: str = "restaurant") -> str:
        if not type_filter:
            type_filter = "restaurant"
        return _perform_google_places_search(search_string, "restaurant", radius, type_filter)
    async def _arun(self, search_string: str, radius: int = 5000, type_filter: str = "restaurant") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

class SearchAccommodationsTool(StructuredTool):
    name: str = "search_accommodations"
    description: str = """Searches for hotels, hostels, or other lodging options.
    Provides details like name, address, and rating.
    Example search_string: 'boutique hotels in Paris', 'budget hostels in Berlin'."""
    args_schema: type[BaseModel] = PlaceSearchInput
    def _run(self, search_string: str, radius: int = 5000, type_filter: str = "lodging") -> str:
        if not type_filter:
            type_filter = "lodging"
        return _perform_google_places_search(search_string, "lodging", radius, type_filter)
    async def _arun(self, search_string: str, radius: int = 5000, type_filter: str = "lodging") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")


# --- Instantiate the tools for use ---
search_places_of_interest_tool = SearchPlacesOfInterestTool()
search_restaurants_tool = SearchRestaurantsTool()
search_accommodations_tool = SearchAccommodationsTool()


# --- Testing Block ---
if __name__ == "__main__":
    print("--- Testing Restaurant Search ---")
    # MODIFIED: Call the _run method of the instantiated tool
    restaurants_result = search_restaurants_tool._run(search_string="Italian restaurants in Rome, Italy")
    print(restaurants_result)

    print("\n--- Testing Hotels Search ---")
    hotels_result = search_accommodations_tool._run(search_string="luxury hotels in Paris, France", radius=10000)
    print(hotels_result)

    print("\n--- Testing Attractions Search ---")
    attractions_result = search_places_of_interest_tool._run(search_string="famous museums in London, UK")
    print(attractions_result)

    print("\n--- Testing No Results ---")
    no_results_result = search_restaurants_tool._run(search_string="alien spaceship diners on Mars")
    print(no_results_result)

    print("\n--- Testing Invalid Radius ---")
    invalid_radius_result = search_places_of_interest_tool._run(search_string="park in Delhi", radius=60000)
    print(invalid_radius_result)

    print("\n--- Testing Specific Type Filter ---")
    specific_type_result = search_places_of_interest_tool._run(search_string="coffee shops in Seattle", type_filter="cafe")
    print(specific_type_result)
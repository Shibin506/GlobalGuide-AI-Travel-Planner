from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import math

# --- Pydantic Schemas for Tool Inputs ---

class CalculateTotalCostInput(BaseModel):
    """Input schema for calculate_total_cost."""
    item_costs: list[float] = Field(description="A list of individual costs (numbers). E.g., [100.0, 50.5, 25.0]")
    currency: str = Field(description="The currency of the costs (e.g., 'USD', 'EUR', 'INR').")
    description: str = Field(default="various expenses", description="A brief description for the total calculation.")

class CalculateHotelCostInput(BaseModel):
    """Input schema for calculate_hotel_cost."""
    price_per_night: float = Field(description="The cost of the hotel per night.")
    num_nights: int = Field(description="The number of nights for the stay.")
    currency: str = Field(description="The currency of the hotel cost (e.g., 'USD', 'EUR', 'INR').")
    description: str = Field(default="hotel stay", description="A brief description for the hotel cost.")

class CalculateDailyBudgetInput(BaseModel):
    """Input schema for calculate_daily_budget."""
    total_budget: float = Field(description="The total budget available for the trip or a period.")
    num_days: int = Field(description="The number of days the budget needs to cover.")
    currency: str = Field(description="The currency of the budget (e.g., 'USD', 'EUR', 'INR').")
    description: str = Field(default="daily budget", description="A brief description for the daily budget.")


# --- Tool Functions (as StructuredTool classes) ---

class CalculateTotalCostTool(StructuredTool):
    name: str = "calculate_total_cost"
    description: str = """Calculates the sum of a list of individual costs.
    Useful for summing up various trip expenses like activities, food, or miscellaneous items.
    Returns the total cost with its currency.
    Requires 'item_costs' (list of numbers), 'currency' (string, e.g., 'USD'), and an optional 'description'."""
    args_schema: type[BaseModel] = CalculateTotalCostInput

    def _run(self, item_costs: list[float], currency: str, description: str = "various expenses") -> str:
        if not isinstance(item_costs, list) or not all(isinstance(x, (int, float)) for x in item_costs):
            return "Error: 'item_costs' must be a list of numbers."
        total = sum(item_costs)
        return f"Total cost for {description}: {total:.2f} {currency}"

    async def _arun(self, item_costs: list[float], currency: str, description: str = "various expenses") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

class CalculateHotelCostTool(StructuredTool):
    name: str = "calculate_hotel_cost"
    description: str = """Calculates the total cost of a hotel stay.
    Requires 'price_per_night' (number), 'num_nights' (integer), 'currency' (string, e.g., 'USD'),
    and an optional 'description'. Returns the total hotel cost."""
    args_schema: type[BaseModel] = CalculateHotelCostInput

    def _run(self, price_per_night: float, num_nights: int, currency: str, description: str = "hotel stay") -> str:
        if not isinstance(price_per_night, (int, float)) or price_per_night <= 0:
            return "Error: 'price_per_night' must be a positive number."
        if not isinstance(num_nights, int) or num_nights <= 0:
            return "Error: 'num_nights' must be a positive integer."
        total_cost = price_per_night * num_nights
        return f"Total cost for {description}: {total_cost:.2f} {currency}"

    async def _arun(self, price_per_night: float, num_nights: int, currency: str, description: str = "hotel stay") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

class CalculateDailyBudgetTool(StructuredTool):
    name: str = "calculate_daily_budget"
    description: str = """Calculates the daily budget by dividing a total budget by the number of days.
    Useful for breaking down a total trip budget into daily allowances.
    Requires 'total_budget' (number), 'num_days' (integer), 'currency' (string, e.g., 'USD'),
    and an optional 'description'. Returns the daily budget."""
    args_schema: type[BaseModel] = CalculateDailyBudgetInput

    def _run(self, total_budget: float, num_days: int, currency: str, description: str = "daily budget") -> str:
        if not isinstance(total_budget, (int, float)) or total_budget <= 0:
            return "Error: 'total_budget' must be a positive number."
        if not isinstance(num_days, int) or num_days <= 0:
            return "Error: 'num_days' must be a positive integer."
        if num_days == 0:
            return "Error: Cannot calculate daily budget with zero days."
        daily_budget = total_budget / num_days
        return f"Daily budget for {description}: {daily_budget:.2f} {currency}"

    async def _arun(self, total_budget: float, num_days: int, currency: str, description: str = "daily budget") -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

# --- Instantiate the tools for use ---
calculate_total_cost_tool = CalculateTotalCostTool()
calculate_hotel_cost_tool = CalculateHotelCostTool()
calculate_daily_budget_tool = CalculateDailyBudgetTool()

# --- Testing Block ---
if __name__ == "__main__":
    print("--- Testing Total Cost Calculation ---")
    total_result = calculate_total_cost_tool._run(
        item_costs=[50.0, 12.5, 30.0],
        currency="USD",
        description="food and activities"
    )
    print(total_result)

    print("\n--- Testing Hotel Cost Calculation ---")
    hotel_result = calculate_hotel_cost_tool._run(
        price_per_night=150.0,
        num_nights=7,
        currency="EUR",
        description="Paris hotel"
    )
    print(hotel_result)

    print("\n--- Testing Daily Budget Calculation ---")
    daily_budget_result = calculate_daily_budget_tool._run(
        total_budget=1000.0,
        num_days=5,
        currency="JPY",
        description="Tokyo trip"
    )
    print(daily_budget_result)

    print("\n--- Testing Invalid Input (Hotel Cost) ---")
    invalid_hotel_result = calculate_hotel_cost_tool._run(
        price_per_night=-100.0, # Invalid input
        num_nights=5,
        currency="USD"
    )
    print(invalid_hotel_result)

    print("\n--- Testing Zero Days (Daily Budget) ---")
    zero_days_result = calculate_daily_budget_tool._run(
        total_budget=500.0,
        num_days=0, # Invalid input
        currency="USD"
    )
    print(zero_days_result)
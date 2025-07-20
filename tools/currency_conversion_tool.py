import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

if not EXCHANGE_RATE_API_KEY:
    raise ValueError("EXCHANGE_RATE_API_KEY not found in environment variables. Please check your .env file.")

# --- Pydantic Schema for Tool Input ---

class CurrencyConversionInput(BaseModel):
    """Input schema for convert_currency."""
    amount: float = Field(description="The amount of money to convert.")
    from_currency: str = Field(description="The currency code to convert from (e.g., 'USD', 'EUR', 'JPY').")
    to_currency: str = Field(description="The currency code to convert to (e.g., 'GBP', 'CAD', 'INR').")

# --- Tool Function (as StructuredTool class) ---

class CurrencyConverterTool(StructuredTool):
    name: str = "convert_currency"
    description: str = """Converts a given amount from one currency to another using real-time exchange rates.
    Useful for budgeting and understanding costs in different currencies for international trips.
    Requires 'amount' (number), 'from_currency' (3-letter currency code, e.g., 'USD'),
    and 'to_currency' (3-letter currency code, e.g., 'EUR')."""
    args_schema: type[BaseModel] = CurrencyConversionInput

    def _run(self, amount: float, from_currency: str, to_currency: str) -> str:
        if not isinstance(amount, (int, float)) or amount <= 0:
            return "Error: 'amount' must be a positive number."

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if not (len(from_currency) == 3 and from_currency.isalpha()):
            return f"Error: Invalid 'from_currency' code '{from_currency}'. Must be a 3-letter alphabetic code (e.g., 'USD')."
        if not (len(to_currency) == 3 and to_currency.isalpha()):
            return f"Error: Invalid 'to_currency' code '{to_currency}'. Must be a 3-letter alphabetic code (e.g., 'EUR')."

        base_url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{from_currency}/{to_currency}"

        try:
            response = requests.get(base_url)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if data.get("result") == "error":
                error_type = data.get("error-type", "unknown error")
                if error_type == "unsupported-code":
                    return f"Error: One or both currency codes ('{from_currency}', '{to_currency}') are unsupported by the API. Check valid ISO codes."
                elif error_type == "invalid-key":
                    return "Error: Invalid API key for ExchangeRate-API. Please check your .env file."
                return f"Error converting currency: {error_type}. API response: {data.get('result')}"

            conversion_rate = data["conversion_rate"]
            converted_amount = amount * conversion_rate
            return f"{amount:.2f} {from_currency} is equal to {converted_amount:.2f} {to_currency} (Rate: 1 {from_currency} = {conversion_rate:.4f} {to_currency})"

        except requests.exceptions.HTTPError as e: # Catch HTTPError specifically
            if e.response.status_code == 404:
                # OpenWeatherMap sometimes uses 404 for invalid cities, ExchangeRate-API too for unsupported pairs
                return f"Error: Could not find exchange rate for '{from_currency}' to '{to_currency}'. One or both currency codes might be unsupported or incorrect. HTTP 404 Not Found."
            return f"Network error or invalid request to currency conversion API (HTTP Error): {e}. Check internet connection or API key."
        except requests.exceptions.RequestException as e:
            return f"Network error or invalid request to currency conversion API: {e}. Check internet connection or API key."
        except Exception as e:
            return f"An unexpected error occurred during currency conversion: {e}"

    async def _arun(self, amount: float, from_currency: str, to_currency: str) -> str:
        raise NotImplementedError("Asynchronous call not implemented for this tool.")

# --- Instantiate the tool for use ---
convert_currency_tool = CurrencyConverterTool()

# --- Testing Block ---
if __name__ == "__main__":
    print("--- Testing Currency Conversion (USD to EUR) ---")
    usd_to_eur = convert_currency_tool._run(amount=100.0, from_currency="USD", to_currency="EUR")
    print(usd_to_eur)

    print("\n--- Testing Currency Conversion (EUR to JPY) ---")
    eur_to_jpy = convert_currency_tool._run(amount=50.0, from_currency="EUR", to_currency="JPY")
    print(eur_to_jpy)

    print("\n--- Testing Invalid Currency Code ---")
    invalid_currency = convert_currency_tool._run(amount=10.0, from_currency="XYZ", to_currency="USD")
    print(invalid_currency)

    print("\n--- Testing Invalid Amount ---")
    invalid_amount = convert_currency_tool._run(amount=-5.0, from_currency="USD", to_currency="EUR")
    print(invalid_amount)

    print("\n--- Testing Invalid API Key (This will likely fail with a real invalid key) ---")
    # To test this, temporarily change your API key in .env to a clearly wrong one.
    # invalid_api_key_test = convert_currency_tool._run(amount=10.0, from_currency="USD", to_currency="EUR")
    # print(invalid_api_key_test)
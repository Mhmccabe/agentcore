"""
Strands Basics - Custom Tools
Define your own tools with the @tool decorator. Strands passes the docstring
and type hints to the model as the tool schema — keep them clear and accurate.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    agent("question about stocks")
        |
        v
    Strands Agent
        |
        v
    Claude Haiku 4.5  -->  "I need to call get_stock_price"
                                |
                                v
                        @tool get_stock_price(ticker)    <-- runs locally
                                |
                                v
                        Claude Haiku 4.5  -->  "I need portfolio value"
                                                    |
                                                    v
                                        @tool calculate_portfolio_value()
                                                    |
                                                    v
                                        Claude Haiku 4.5  -->  Final answer

    Strands handles the tool-call loop automatically.
    @tool uses the docstring + type hints as the schema sent to the model.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import random
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()


@tool
def get_stock_price(ticker: str) -> dict:
    """
    Get the current stock price for a given ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g. AMZN, GOOGL)

    Returns:
        A dict with ticker, price, and currency.
    """
    # Simulated prices — replace with a real market data API
    simulated_price = round(random.uniform(50, 500), 2)
    return {"ticker": ticker.upper(), "price": simulated_price, "currency": "USD"}


@tool
def calculate_portfolio_value(tickers: list[str], shares: list[int]) -> dict:
    """
    Calculate the total value of a stock portfolio.

    Args:
        tickers: List of stock ticker symbols
        shares: Number of shares held for each ticker (same order as tickers)

    Returns:
        A dict with individual holdings and total portfolio value.
    """
    holdings = []
    total = 0.0
    for ticker, qty in zip(tickers, shares):
        price = round(random.uniform(50, 500), 2)
        value = price * qty
        total += value
        holdings.append({"ticker": ticker, "shares": qty, "price": price, "value": value})
    return {"holdings": holdings, "total_value": round(total, 2), "currency": "USD"}


model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[get_stock_price, calculate_portfolio_value],
    system_prompt="You are a helpful financial assistant.",
))

response = agent("What's the current price of AMZN? And what would a portfolio of 10 AMZN and 5 GOOGL be worth?")
print(response)

"""
MCP - Server
Defines a Model Context Protocol server with all three MCP primitives:
Tools, Resources, and Prompts. Runs as a subprocess over stdio.

Architecture:
    server.py (this file)
         |
         | stdio (JSON-RPC)
         v
    MCP Protocol — three primitives:
         |
         +-- Tools      callable functions the model invokes
         |
         +-- Resources  URI-addressable data the model reads
         |                config://server
         |                data://cities
         |                weather://{city}   (template)
         |
         +-- Prompts    reusable prompt templates with arguments
                          weather_report(city, unit)
                          unit_conversion_help()

Run standalone to verify tools work:
    python server.py

Tools defined here:
    get_current_time()              -- no args, returns UTC time
    calculate(expression)           -- evaluates a math expression safely
    get_weather(city, unit)         -- simulated weather data
    convert_units(value, from, to)  -- unit conversion

Resources defined here:
    config://server                 -- server metadata and capabilities
    data://cities                   -- list of supported cities
    weather://{city}                -- live weather for a city (template)

Prompts defined here:
    weather_report(city, unit)      -- template for a weather report request
    unit_conversion_help()          -- template explaining supported conversions
"""
import logging
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("demo-server")


@mcp.tool()
def get_current_time() -> str:
    """Get the current UTC date and time."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@mcp.tool()
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression and return the result.

    Args:
        expression: A mathematical expression e.g. '2 ** 10' or '(3 + 4) * 5'
    """
    allowed = set("0123456789+-*/().,% ")
    if not all(c in allowed for c in expression):
        return "Error: only basic arithmetic operators are allowed."
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_weather(city: str, unit: str = "celsius") -> dict:
    """
    Get the current weather for a city (simulated).

    Args:
        city: The city name
        unit: Temperature unit — 'celsius' or 'fahrenheit'
    """
    simulated = {
        "london": {"temp_c": 14, "condition": "Cloudy"},
        "new york": {"temp_c": 22, "condition": "Sunny"},
        "tokyo": {"temp_c": 28, "condition": "Humid"},
        "sydney": {"temp_c": 19, "condition": "Partly cloudy"},
    }
    data = simulated.get(city.lower(), {"temp_c": 20, "condition": "Clear"})
    temp = data["temp_c"] if unit == "celsius" else round(data["temp_c"] * 9 / 5 + 32, 1)
    return {"city": city, "temperature": temp, "unit": unit, "condition": data["condition"]}


@mcp.tool()
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert a value between common units.

    Supported conversions:
        km <-> miles,  kg <-> lbs,  celsius <-> fahrenheit,  litres <-> gallons

    Args:
        value: The numeric value to convert
        from_unit: The source unit
        to_unit: The target unit
    """
    conversions = {
        ("km", "miles"): lambda v: v * 0.621371,
        ("miles", "km"): lambda v: v * 1.60934,
        ("kg", "lbs"): lambda v: v * 2.20462,
        ("lbs", "kg"): lambda v: v / 2.20462,
        ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
        ("litres", "gallons"): lambda v: v * 0.264172,
        ("gallons", "litres"): lambda v: v / 0.264172,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key not in conversions:
        return f"Unsupported conversion: {from_unit} -> {to_unit}"
    result = round(conversions[key](value), 4)
    return f"{value} {from_unit} = {result} {to_unit}"


# ---------------------------------------------------------------------------
# Resources — URI-addressable data sources
# ---------------------------------------------------------------------------

SIMULATED_WEATHER = {
    "london":   {"temp_c": 14, "condition": "Cloudy"},
    "new york": {"temp_c": 22, "condition": "Sunny"},
    "tokyo":    {"temp_c": 28, "condition": "Humid"},
    "sydney":   {"temp_c": 19, "condition": "Partly cloudy"},
}

SUPPORTED_CITIES = sorted(SIMULATED_WEATHER.keys())


@mcp.resource("config://server")
def server_config() -> str:
    """Static server metadata — name, version, and supported capabilities."""
    return (
        "name: demo-server\n"
        "version: 1.0.0\n"
        "tools: get_current_time, calculate, get_weather, convert_units\n"
        "resources: config://server, data://cities, weather://{city}\n"
        "prompts: weather_report, unit_conversion_help\n"
        f"started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


@mcp.resource("data://cities")
def list_cities() -> str:
    """List of cities for which weather data is available."""
    return "Supported cities:\n" + "\n".join(f"  - {c}" for c in SUPPORTED_CITIES)


@mcp.resource("weather://{city}")
def weather_resource(city: str) -> str:
    """Current weather for a city, addressed by URI template weather://{city}."""
    data = SIMULATED_WEATHER.get(city.lower(), {"temp_c": 20, "condition": "Clear"})
    temp_f = round(data["temp_c"] * 9 / 5 + 32, 1)
    return (
        f"city: {city}\n"
        f"condition: {data['condition']}\n"
        f"temperature_celsius: {data['temp_c']}\n"
        f"temperature_fahrenheit: {temp_f}"
    )


# ---------------------------------------------------------------------------
# Prompts — reusable prompt templates
# ---------------------------------------------------------------------------

@mcp.prompt()
def weather_report(city: str, unit: str = "celsius") -> str:
    """Generate a prompt asking for a friendly weather report for a city."""
    return (
        f"Please give me a friendly weather report for {city}. "
        f"Report the temperature in {unit}. "
        "Include what to wear and whether to carry an umbrella."
    )


@mcp.prompt()
def unit_conversion_help() -> str:
    """Generate a prompt that asks the agent to explain supported unit conversions."""
    return (
        "List all the unit conversions you support, give one example for each, "
        "and explain the formula used."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

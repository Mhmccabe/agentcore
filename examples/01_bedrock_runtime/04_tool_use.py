"""
Bedrock Runtime - Tool Use (Function Calling)
Defines tools the model can call, then handles the tool execution loop.
The model decides when to call a tool; your code executes it and returns the result.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    User query
        |
        v
    Converse API  -->  Claude Haiku
                            |
                            | stopReason="tool_use"
                            v
                       get_weather(city="London")   <-- your local function
                            |
                            | tool result
                            v
    Converse API  -->  Claude Haiku
                            |
                            | stopReason="end_turn"
                            v
                       Final answer to user

    The loop runs until stop_reason == "end_turn".
    Each iteration is a separate API call (billed separately).
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import boto3
from dotenv import load_dotenv
from utils.cost_tracker import SessionTotal, _calculate

load_dotenv()

MODEL_ID = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

client = boto3.client("bedrock-runtime", region_name="eu-west-1")

tools = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Get the current weather for a given city.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city name"},
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit",
                        },
                    },
                    "required": ["city"],
                }
            },
        }
    }
]


def get_weather(city: str, unit: str = "celsius") -> dict:
    # Simulated weather data — replace with a real API call
    return {"city": city, "temperature": 22, "unit": unit, "condition": "Sunny"}


def run_agent_loop(user_query: str) -> str:
    messages = [{"role": "user", "content": [{"text": user_query}]}]
    session = SessionTotal()

    while True:
        response = client.converse(
            modelId=MODEL_ID,
            messages=messages,
            toolConfig={"tools": tools},
            inferenceConfig={"maxTokens": 512},
        )

        usage = response["usage"]
        session.add(_calculate(MODEL_ID, usage["inputTokens"], usage["outputTokens"]))

        output_message = response["output"]["message"]
        messages.append(output_message)
        stop_reason = response["stopReason"]

        if stop_reason == "end_turn":
            session.print()
            return output_message["content"][0]["text"]

        # Model wants to call a tool
        if stop_reason == "tool_use":
            tool_results = []
            for block in output_message["content"]:
                if block["type"] == "toolUse":
                    tool_name = block["name"]
                    tool_input = block["input"]
                    tool_use_id = block["toolUseId"]

                    if tool_name == "get_weather":
                        result = get_weather(**tool_input)
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"json": result}],
                            }
                        }
                    )

            messages.append({"role": "user", "content": tool_results})


print(run_agent_loop("What's the weather like in London today?"))

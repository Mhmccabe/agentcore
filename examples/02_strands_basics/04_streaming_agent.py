"""
Strands Basics - Streaming
Stream tokens as the agent generates them using stream_async().
Cost is captured from the result event emitted at the end of the stream.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    agent.stream_async("prompt")
        |
        v
    Strands Agent (async generator)
        |
        v
    BedrockModel (streaming=True)
        |
        v
    Bedrock Runtime  -->  Claude Haiku 4.5
        |
        | EventStream
        v
    async for event:
        |
        +-- {init_event_loop}   internal setup
        +-- {start}             generation starts
        +-- {data: "token"}     Strands auto-prints to stdout
        +-- {data: "token"}     ...
        +-- {result: AgentResult}  <-- we capture usage here
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import asyncio
from strands import Agent
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import print_cost

load_dotenv()

MODEL_ID = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

model = BedrockModel(
    model_id=MODEL_ID,
    region_name="eu-west-1",
    streaming=True,
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant.",
)


async def main():
    print("Streaming response:\n")

    # Strands prints tokens to stdout automatically during streaming.
    # We loop only to capture the final result event for cost tracking.
    input_tokens = output_tokens = 0

    async for event in agent.stream_async(
        "Explain the difference between Bedrock Agents and AgentCore in 3 bullet points."
    ):
        if "result" in event:
            usage = event["result"].metrics.accumulated_usage
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)

    print_cost(MODEL_ID, input_tokens, output_tokens)


asyncio.run(main())

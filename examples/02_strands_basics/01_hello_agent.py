"""
Strands Basics - Hello Agent
The simplest possible Strands agent using Amazon Bedrock as the model provider.
Strands manages the conversation loop; you just call the agent like a function.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    agent("your prompt")
        |
        v
    Strands Agent
    (manages conversation state, tool loop, retries)
        |
        v
    BedrockModel
        |
        v
    Bedrock Runtime API  (eu-west-1)
        |
        v
    Claude Haiku 4.5
        |
        v
    AgentResult  -->  response.message["content"][0]["text"]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from strands import Agent
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    system_prompt="You are a helpful AWS expert who gives concise answers.",
))

response = agent("What is Amazon Bedrock AgentCore?")
print(response)

"""
AgentCore - Code Interpreter
AgentCore's Code Interpreter runs Python in a secure sandbox with pre-installed
data science libraries (pandas, numpy, matplotlib). Strands exposes it as a
built-in tool via strands_tools.

Prerequisites:
  Enable AgentCore in your AWS account and ensure your IAM role has
  bedrock-agentcore:StartCodeInterpreterSession permission.

Requires: bedrock-agentcore:StartCodeInterpreterSession,
          bedrock-agentcore:ExecuteCodeInterpreterCode permissions.

Architecture:
    agent("analyse this data")
         |
         v
    Strands Agent + Claude Haiku
         |
         | "I'll write Python to solve this"
         v
    @tool code_interpreter(code="...")
         |
         v
    AgentCore API  (AWS managed)
         |
         v
    Secure Sandbox (AWS)
    ┌─────────────────────────┐
    │  Python 3.x             │
    │  pandas, numpy          │
    │  matplotlib, scipy      │
    │  isolated, no network   │
    └─────────────────────────┘
         |
         | stdout + return value
         v
    Claude interprets results
         |
         v
    Answer with analysis
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from strands import Agent
from strands.models import BedrockModel
from strands_tools import code_interpreter
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[code_interpreter],
    system_prompt=(
        "You are a data analysis assistant. Use the code_interpreter tool "
        "to run Python code for calculations, data analysis, and visualisations."
    ),
))

print("=== Data analysis ===")
print(agent(
    "Generate a dataset of 50 random sales figures between 1000 and 10000, "
    "then calculate the mean, median, standard deviation, and identify any outliers."
))

print("\n=== Algorithm implementation ===")
print(agent(
    "Implement and run a bubble sort on [64, 34, 25, 12, 22, 11, 90] "
    "showing each swap step."
))

agent.print_session_total()

"""
Strands Basics - Built-in Tools
strands-agents-tools ships ready-made tools for common tasks.
This example uses the Python REPL, HTTP request, and shell tools.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    agent("question")
        |
        v
    Strands Agent + Claude Haiku 4.5
        |
        |-- python_repl  --> subprocess Python interpreter  (local)
        |                         |
        |                    stdout / result
        |
        |-- http_request --> internet / any URL             (outbound)
        |                         |
        |                    response body
        |
        +-- shell        --> local OS shell (zsh/bash)      (local)
                                  |
                             command output

    WARNING: shell and http_request run with your user's permissions.
    Only use with prompts you trust.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from strands import Agent
from strands.models import BedrockModel
from strands_tools import python_repl, http_request, shell
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[python_repl, http_request, shell],
    system_prompt=(
        "You are a technical assistant. Use the available tools to answer questions. "
        "When asked to calculate something, use the python_repl tool."
    ),
))

# The agent will use python_repl to compute this
print("=== Math via python_repl ===")
print(agent("Calculate the first 10 Fibonacci numbers and show their sum."))

print("\n=== Shell info ===")
print(agent("What is the current working directory and list its contents?"))

agent.print_session_total()

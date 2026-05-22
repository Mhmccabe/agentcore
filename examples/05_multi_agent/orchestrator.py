"""
Multi-Agent - Orchestrator pattern with Strands
Strands supports multi-agent systems where a top-level orchestrator delegates
to specialised sub-agents via the agent_as_tool() pattern.
Each sub-agent has its own model, tools, and system prompt.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    User prompt
         |
         v
    Orchestrator Agent  (Claude Sonnet 4.6)
         |
         |-- @tool research_topic
         |        |
         |        v
         |   Researcher Agent  (Claude Haiku)
         |        |
         |        v
         |   http_request --> internet
         |        |
         |        v
         |   structured summary
         |
         |-- @tool analyse_data
         |        |
         |        v
         |   Analyst Agent  (Claude Haiku)
         |        |
         |        v
         |   python_repl --> local Python
         |        |
         |        v
         |   quantitative insights
         |
         +-- @tool write_report
                  |
                  v
             Writer Agent  (Claude Haiku)
                  |
                  v
             Final report  -->  Orchestrator  -->  User

    Each sub-agent is a full Strands Agent exposed as a tool via as_tool().
    The orchestrator decides the order and whether to call each sub-agent.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from strands import Agent
from strands.models import BedrockModel
from strands_tools import python_repl, http_request
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

REGION = "eu-west-1"


def make_model(model_id: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0") -> BedrockModel:
    return BedrockModel(model_id=model_id, region_name=REGION)


# --- Specialist sub-agents ---

researcher = Agent(
    model=make_model(),
    tools=[http_request],
    system_prompt=(
        "You are a research specialist. Gather factual information on the topic given. "
        "Return a structured summary with key facts and sources."
    ),
)

analyst = Agent(
    model=make_model(),
    tools=[python_repl],
    system_prompt=(
        "You are a data analyst. Given research findings, perform quantitative analysis, "
        "identify trends, and produce clear insights with supporting calculations."
    ),
)

writer = Agent(
    model=make_model(),
    system_prompt=(
        "You are a technical writer. Transform research and analysis into a clear, "
        "well-structured report suitable for a technical audience."
    ),
)

# --- Orchestrator wires sub-agents together as tools ---

orchestrator = TrackedAgent(Agent(
    model=make_model("eu.anthropic.claude-sonnet-4-6"),  # Stronger model orchestrates
    tools=[
        researcher.as_tool(
            tool_name="research_topic",
            tool_description="Research a topic and return a factual summary.",
        ),
        analyst.as_tool(
            tool_name="analyse_data",
            tool_description="Perform quantitative analysis on provided information.",
        ),
        writer.as_tool(
            tool_name="write_report",
            tool_description="Write a structured technical report from research and analysis.",
        ),
    ],
    system_prompt=(
        "You are an orchestrator that produces comprehensive technical reports. "
        "Always: 1) research the topic, 2) analyse the findings, 3) write the final report."
    ),
))

print("=== Multi-agent report generation ===\n")
result = orchestrator(
    "Produce a brief technical report on the current state of large language model "
    "context window sizes and their practical implications."
)
print(result)

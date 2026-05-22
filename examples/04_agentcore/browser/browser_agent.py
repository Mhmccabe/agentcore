"""
AgentCore - Browser Tool
Gives agents real-time web access via a headless Playwright browser.

Two implementations exist:
  - LocalChromiumBrowser: runs Playwright locally (used here — no extra setup needed)
  - AgentCoreBrowser: runs in AWS AgentCore's managed sandbox (requires bedrock_agentcore SDK)

Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    agent("look up this URL")
         |
         v
    Strands Agent + Claude Sonnet 4.6
         |
         v
    @tool browser.browser(action="navigate", url=...)
         |
         v
    LocalChromiumBrowser (Playwright)
         |
         v
    Headless Chromium  (runs locally on your machine)
         |
         | fetches + renders page (executes JS)
         v
    Page content (full rendered DOM as text)
         |
         | large text chunk sent back to model context
         v
    Claude summarises / answers from page content

    NOTE: Full page DOM can be 100k+ tokens — use sparingly.
    Cost scales with page size, not just your question.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from strands import Agent
from strands.models import BedrockModel
from strands_tools.browser.local_chromium_browser import LocalChromiumBrowser
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

browser = LocalChromiumBrowser(launch_options={"headless": False})  # Set headless=True to run without opening a browser window

model = BedrockModel(
    model_id="eu.anthropic.claude-sonnet-4-6",  # Sonnet for complex web reasoning
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[browser.browser],
    system_prompt=(
        "You are a research assistant with web browsing capabilities. "
        "Use the browser to find accurate, up-to-date information. "
        "Always summarise what you find in a clear, structured way."
    ),
))

print("=== Web research ===")
print(agent(
    "Look up https://aws.amazon.com/bedrock/pricing/ and summarise "
    "the pricing model for Claude models."
))

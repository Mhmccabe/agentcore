"""
MCP - Client
Connects a Strands agent to the MCP server (server.py) over stdio and
demonstrates all three MCP primitives: Tools, Resources, and Prompts.

Architecture:
    client.py
         |
         | spawns subprocess
         v
    server.py  (MCP server, runs as child process)
         |
         | stdio (JSON-RPC messages)
         v
    MCPClient  (Strands wrapper)
         |
         +-- Tools      discovered at runtime, passed to Strands agent
         |
         +-- Resources  read directly via URI (not passed to agent)
         |                config://server    static server info
         |                data://cities      list of supported cities
         |                weather://{city}   live weather for a city
         |
         +-- Prompts    fetched as text, then fed to the agent
                          weather_report(city, unit)
                          unit_conversion_help()

Key point: the agent has no hardcoded knowledge of the tools.
It discovers them at runtime from the MCP server's tool manifest.

Usage:
    python client.py
"""
import sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
logging.getLogger("mcp").setLevel(logging.WARNING)

from pathlib import Path
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

SERVER_PATH = Path(__file__).parent / "server.py"
PYTHON = sys.executable

server_params = StdioServerParameters(
    command=PYTHON,
    args=[str(SERVER_PATH)],
)

model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-west-1",
)

mcp_client = MCPClient(lambda: stdio_client(server_params))

with mcp_client:
    # ------------------------------------------------------------------
    # Tools — discovered at runtime, injected into the Strands agent
    # ------------------------------------------------------------------
    tools = mcp_client.list_tools_sync()
    print(f"Discovered {len(tools)} tools from MCP server:")
    for t in tools:
        print(f"  - {t.tool_name}")
    print()

    agent = TrackedAgent(Agent(
        model=model,
        tools=tools,
        system_prompt="You are a helpful assistant with access to several utility tools.",
    ))

    print("=== Tool: Time ===")
    agent("What is the current UTC time?")

    print("\n=== Tool: Weather ===")
    agent("What is the weather like in London and Tokyo? Give me both in celsius.")

    print("\n=== Tool: Calculation ===")
    agent("What is 2 to the power of 16, divided by 3?")

    print("\n=== Tool: Unit conversion ===")
    agent("Convert 100 km to miles, and 75 kg to lbs.")

    # ------------------------------------------------------------------
    # Resources — read URI-addressable data directly (no agent needed)
    # ------------------------------------------------------------------
    print("\n=== Resources ===")

    resources = mcp_client.list_resources_sync().resources
    print(f"Discovered {len(resources)} resources:")
    for r in resources:
        print(f"  - {r.uri}  ({r.name})")
    print()

    config_content = mcp_client.read_resource_sync("config://server").contents
    print("config://server →")
    print(config_content[0].text if config_content else "(empty)")
    print()

    cities_content = mcp_client.read_resource_sync("data://cities").contents
    print("data://cities →")
    print(cities_content[0].text if cities_content else "(empty)")
    print()

    # Resource templates — parameterised URIs like weather://{city}
    templates = mcp_client.list_resource_templates_sync().resourceTemplates
    print(f"Discovered {len(templates)} resource template(s):")
    for t in templates:
        print(f"  - {t.uriTemplate}  ({t.name})")
    print()

    weather_content = mcp_client.read_resource_sync("weather://tokyo").contents
    print("weather://tokyo →")
    print(weather_content[0].text if weather_content else "(empty)")
    print()

    # ------------------------------------------------------------------
    # Prompts — fetch template text and feed it to the agent
    # ------------------------------------------------------------------
    print("=== Prompts ===")

    prompts = mcp_client.list_prompts_sync().prompts
    print(f"Discovered {len(prompts)} prompt(s):")
    for p in prompts:
        print(f"  - {p.name}")
    print()

    # Fetch the weather_report prompt and run it through the agent
    weather_prompt = mcp_client.get_prompt_sync("weather_report", {"city": "Sydney", "unit": "celsius"})
    prompt_text = weather_prompt.messages[0].content.text
    print(f"Prompt 'weather_report' → \"{prompt_text}\"")
    print()
    print("=== Prompt: weather_report (Sydney) ===")
    agent(prompt_text)

    # Fetch the unit_conversion_help prompt and run it through the agent
    help_prompt = mcp_client.get_prompt_sync("unit_conversion_help", {})
    help_text = help_prompt.messages[0].content.text
    print(f"\nPrompt 'unit_conversion_help' → \"{help_text}\"")
    print()
    print("=== Prompt: unit_conversion_help ===")
    agent(help_text)

    agent.print_session_total()

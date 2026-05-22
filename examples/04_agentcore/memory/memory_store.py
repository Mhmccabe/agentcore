"""
AgentCore - Memory Store
AgentCore Memory gives agents persistent memory across sessions.
This example shows creating a memory store, saving facts, and recalling them
in a Strands agent so it can personalise responses across conversations.

Prerequisites:
  1. Enable AgentCore in your AWS account
  2. Create a Memory Store (Bedrock > AgentCore > Memory) and copy its ID

Requires: bedrock-agentcore:CreateMemory, GetMemory, ListMemories permissions.

Architecture:
    Session 1                           Session 2
    ─────────────────────────           ─────────────────────────
    agent("remember: I like Python")    agent("what do I like?")
         |                                   |
         v                                   v
    Strands Agent                       Strands Agent
         |                                   |
         v                                   v
    @tool save_to_memory            @tool recall_from_memory
         |                                   |
         v                                   v
    bedrock-agentcore API           bedrock-agentcore API
         |                                   |
         v                                   v
    AgentCore Memory Store  ------->  AgentCore Memory Store
    (persists across sessions)        (retrieves stored memories)
         |                                   |
         v                                   v
    {"status": "saved"}             [{"content": "I like Python"}]
                                            |
                                            v
                                    Claude synthesises answer
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

MEMORY_STORE_ID = "YOUR_MEMORY_STORE_ID"  # replace with your Memory Store ID
REGION = "eu-west-1"
SESSION_ID = "demo-session-001"

memory_client = boto3.client("bedrock-agentcore", region_name=REGION)


@tool
def save_to_memory(content: str, description: str) -> dict:
    """
    Save a piece of information to long-term agent memory.

    Args:
        content: The information to remember
        description: A brief label describing what is being remembered

    Returns:
        Confirmation dict with memory ID.
    """
    response = memory_client.create_memory(
        memoryStoreId=MEMORY_STORE_ID,
        content={"text": content},
        namespace=SESSION_ID,
    )
    return {"status": "saved", "memoryId": response["memoryId"], "description": description}


@tool
def recall_from_memory(query: str) -> list[dict]:
    """
    Retrieve relevant memories from long-term memory.

    Args:
        query: A natural language query to search memories

    Returns:
        A list of relevant memory entries.
    """
    response = memory_client.list_memories(
        memoryStoreId=MEMORY_STORE_ID,
        namespace=SESSION_ID,
        maxResults=10,
    )
    memories = []
    for mem in response.get("memorySummaries", []):
        memories.append({
            "memoryId": mem["memoryId"],
            "content": mem.get("content", {}).get("text", ""),
            "createdAt": str(mem.get("createdAt", "")),
        })
    return memories


model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name=REGION,
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[save_to_memory, recall_from_memory],
    system_prompt=(
        "You are a personal assistant with persistent memory. "
        "Save important facts the user tells you. "
        "Recall memories when relevant to the conversation."
    ),
))

# Session 1 — save some facts
print("=== Session 1: saving preferences ===")
print(agent("My name is Alex and I prefer Python over JavaScript. Please remember that."))

# Session 2 — recall facts
print("\n=== Session 2: recalling preferences ===")
print(agent("What do you remember about my programming preferences?"))

agent.print_session_total()

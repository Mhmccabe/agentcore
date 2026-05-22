"""
LLM Wiki - Query
Asks questions against the wiki. The agent searches existing pages and
synthesises answers grounded in what the wiki actually contains.

Usage:
    python query.py "What is the relationship between Anthropic and AWS?"
    python query.py "Which AI companies have models on Amazon Bedrock?"
    python query.py "Who founded OpenAI?"

Architecture:
    "your question"
         |
         v
    Query Agent  (Claude Haiku 4.5)
         |
         +-- @tool search_wiki(query)
         |        |
         |        v
         |   grep wiki/*.md for matches
         |        |
         |        v
         |   [{entity, snippet}, ...]
         |
         +-- @tool read_wiki_page(entity)    <-- for each relevant hit
         |        |
         |        v
         |   full markdown content
         |        |
         |        | follow [[links]] to related pages
         |        v
         +-- @tool read_wiki_page(linked_entity)
         |
         v
    Claude synthesises answer from wiki content only
         |
         v
    Grounded answer + citations
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from strands import Agent
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent
from wiki_tools import list_wiki_pages, read_wiki_page, search_wiki

load_dotenv()

SYSTEM_PROMPT = """You are a wiki assistant. Answer questions using only the information
in the wiki pages available to you via the tools.

To answer a question:
1. Use search_wiki to find relevant pages
2. Use read_wiki_page to read the full content of relevant pages
3. Follow [[links]] to related entities and read those pages too
4. Synthesise an answer grounded entirely in the wiki content
5. If the wiki doesn't contain enough information, say so clearly

Always cite which wiki pages you used."""

model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",  # Haiku is sufficient for retrieval
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[list_wiki_pages, read_wiki_page, search_wiki],
    system_prompt=SYSTEM_PROMPT,
))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query.py \"your question here\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"Question: {question}\n")
    # Strands auto-prints the response during inference; no need to print(response) again
    agent(question)
    agent.print_session_total()

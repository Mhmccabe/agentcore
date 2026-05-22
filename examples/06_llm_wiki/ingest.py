"""
LLM Wiki - Ingest
Reads a markdown file, extracts entities and relationships, and creates or updates
wiki pages for each entity. Based on Andrej Karpathy's llm-wiki concept.

Usage:
    python ingest.py sample_inputs/01_aws_ai.md
    python ingest.py sample_inputs/02_ai_landscape.md   # merges with existing wiki

How it works:
    1. Agent reads the source text
    2. Identifies all named entities (people, orgs, products, concepts)
    3. For each entity, reads any existing wiki page
    4. Writes an updated page merging old knowledge with new facts
    5. Cross-links related entities using [[Entity Name]] syntax

Architecture:
    source.md
         |
         v
    Ingest Agent  (Claude Sonnet 4.6)
         |
         | 1. identify entities in source text
         v
    for each entity (in parallel):
         |
         +-- @tool read_wiki_page(entity)
         |        |
         |        v
         |   wiki/entity.md  (existing content or empty)
         |
         +-- @tool write_wiki_page(entity, merged_content)
                  |
                  v
             wiki/entity.md  (updated with new facts)

    wiki/ directory after ingestion:
    ┌──────────────────────────────────┐
    │  anthropic.md                    │
    │    ## Relationships              │
    │    - [[Claude]]: flagship model  │
    │    - [[AWS]]: distributes on...  │
    │                                  │
    │  claude.md                       │
    │    ## Relationships              │
    │    - [[Anthropic]]: created by   │  <-- bidirectional
    └──────────────────────────────────┘
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from pathlib import Path
from strands import Agent
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent
from wiki_tools import list_wiki_pages, read_wiki_page, write_wiki_page

load_dotenv()

SYSTEM_PROMPT = """You are a knowledge curator that builds and maintains a structured wiki.

When given source text your job is:

1. IDENTIFY all named entities: people, organisations, products, technologies, and concepts
   that are significant enough to deserve their own wiki page.

2. For EACH entity:
   a. Call read_wiki_page to get any existing content
   b. Extract all facts, relationships, and context from the source text
   c. Merge new information with existing content — never lose old facts
   d. Call write_wiki_page with the complete updated page

3. RELATIONSHIPS: every relationship must be listed on BOTH pages.
   If page A links to [[B]], then page B must also link back to [[A]].

4. FACTS must be specific and attributed — not vague generalisations.

5. After processing all entities, call list_wiki_pages to confirm what was written.

Wiki page format:
  # Entity Name
  **Type:** Person | Organisation | Product | Concept | Technology
  **Updated:** {today}

  ## Summary
  2-4 sentence overview.

  ## Key Facts
  - Specific, verifiable facts as bullet points.

  ## Relationships
  - [[Related Entity]]: one-line description of the relationship.

  ## Sources
  - Direct quote or close paraphrase from the source text.

  ## Change Log
  - {today}: what was added or changed.
"""

model = BedrockModel(
    model_id="eu.anthropic.claude-sonnet-4-6",
    region_name="eu-west-1",
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[list_wiki_pages, read_wiki_page, write_wiki_page],
    system_prompt=SYSTEM_PROMPT,
))


def ingest(text: str):
    prompt = f"""Process the following source text and update the wiki accordingly.

<source_text>
{text}
</source_text>

Extract all entities, read their existing wiki pages, and write updated pages."""

    # Strands auto-prints the response during inference; no need to print(response) again
    agent(prompt)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_text_file>")
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"File not found: {source_file}")
        sys.exit(1)

    print(f"Ingesting: {source_file.name}\n")
    ingest(source_file.read_text())
    agent.print_session_total()

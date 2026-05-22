"""
Shared wiki I/O tools used by both ingest.py and query.py.
"""
import re
from pathlib import Path
from datetime import date
from strands import tool

WIKI_DIR = Path(__file__).parent / "wiki"
WIKI_DIR.mkdir(exist_ok=True)
TODAY = date.today().isoformat()


def entity_to_path(entity_name: str) -> Path:
    slug = re.sub(r"[^\w\s-]", "", entity_name.lower()).strip()
    slug = re.sub(r"\s+", "_", slug)
    return WIKI_DIR / f"{slug}.md"


@tool
def list_wiki_pages() -> list[str]:
    """List all entity names currently in the wiki."""
    entities = []
    for f in sorted(WIKI_DIR.glob("*.md")):
        first_line = f.read_text().split("\n")[0]
        if first_line.startswith("# "):
            entities.append(first_line[2:].strip())
    return entities


@tool
def read_wiki_page(entity_name: str) -> str:
    """
    Read the current wiki page for an entity. Returns empty string if it doesn't exist.

    Args:
        entity_name: The name of the entity to read.
    """
    path = entity_to_path(entity_name)
    return path.read_text() if path.exists() else ""


@tool
def write_wiki_page(entity_name: str, content: str) -> dict:
    """
    Write or update the wiki page for an entity.

    Format the content as markdown with these sections:
      # Entity Name
      **Type:** Person | Organisation | Product | Concept | Technology
      **Updated:** YYYY-MM-DD

      ## Summary
      2-4 sentence overview.

      ## Key Facts
      - Bullet list of specific, verifiable facts.

      ## Relationships
      - [[Related Entity]]: one-line description of the relationship.

      ## Sources
      - Direct quote or paraphrase from the source text.

      ## Change Log
      - YYYY-MM-DD: what was added or updated.

    Use [[Entity Name]] syntax for all cross-references.

    Args:
        entity_name: The entity this page is about.
        content: Full markdown content following the format above.
    """
    path = entity_to_path(entity_name)
    path.write_text(content)
    return {"status": "written", "entity": entity_name, "file": path.name}


@tool
def search_wiki(query: str) -> list[dict]:
    """
    Search all wiki pages for mentions of a term or entity name.

    Args:
        query: The search term.
    """
    results = []
    for f in WIKI_DIR.glob("*.md"):
        content = f.read_text()
        if query.lower() in content.lower():
            first_line = content.split("\n")[0]
            entity = first_line[2:].strip() if first_line.startswith("# ") else f.stem
            idx = content.lower().find(query.lower())
            snippet = content[max(0, idx - 80) : idx + 160].strip()
            results.append({"entity": entity, "snippet": snippet})
    return results

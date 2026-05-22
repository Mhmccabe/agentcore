"""
Clean up — removes all generated wiki pages, resetting to initial state.
Usage: python clean.py
"""
from pathlib import Path

wiki_dir = Path(__file__).parent / "wiki"
pages = list(wiki_dir.glob("*.md"))

if not pages:
    print("Wiki is already empty.")
else:
    for page in pages:
        page.unlink()
    print(f"Deleted {len(pages)} wiki pages. Wiki reset to empty state.")

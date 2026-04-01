import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PAPERS_JSON_PATH = BASE_DIR / "data" / "processed" / "papers.json"


def load_papers():
    if not PAPERS_JSON_PATH.exists():
        return {"ai": [], "recsys": []}

    with open(PAPERS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
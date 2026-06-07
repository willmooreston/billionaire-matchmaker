import json
import random
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "data" / "billionaires.json"


def load() -> list[dict]:
    with open(_DATA_FILE) as f:
        return json.load(f)


def pick_random(exclude: frozenset = frozenset()) -> dict:
    pool = [b for b in load() if b["name"] not in exclude]
    return random.choice(pool if pool else load())

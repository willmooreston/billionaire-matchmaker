import json
import random
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "data" / "quotes.json"


def load() -> list[dict]:
    with open(_DATA_FILE) as f:
        return json.load(f)


def pick_random() -> dict:
    return random.choice(load())

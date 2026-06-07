import json
import os
import random

_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "charities.json")

with open(_DATA_FILE) as _f:
    _CHARITIES = json.load(_f)


def find_qualifying(net_worth_usd: int, exclude: frozenset = frozenset(), min_years: int = 100) -> dict | None:
    """Return a random charity whose annual revenue * min_years <= net_worth_usd."""
    all_qualifying = [c for c in _CHARITIES if net_worth_usd >= c["total_revenue"] * min_years]
    pool = [c for c in all_qualifying if c["ein"] not in exclude]
    return random.choice(pool if pool else all_qualifying) if all_qualifying else None


def format_revenue(revenue_usd: int) -> str:
    if revenue_usd >= 1_000_000_000:
        return f"${revenue_usd / 1_000_000_000:.1f}B"
    if revenue_usd >= 1_000_000:
        return f"${revenue_usd / 1_000_000:.1f}M"
    return f"${revenue_usd / 1_000:.0f}K"

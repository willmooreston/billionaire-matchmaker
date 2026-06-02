import random
import requests

PROPUBLICA_BASE = "https://projects.propublica.org/nonprofits/api/v2"

# NTEE major group codes that make for compelling posts
_NTEE_CATEGORIES = ["A", "B", "C", "D", "E", "F", "K", "L", "M", "O", "P", "Q", "R"]


def _search(ntee_code: str, per_page: int = 100) -> list[dict]:
    url = f"{PROPUBLICA_BASE}/search.json"
    resp = requests.get(
        url,
        params={"ntee[id]": ntee_code, "per_page": per_page},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("organizations", [])


def find_qualifying(net_worth_usd: int, min_years: int = 100) -> dict | None:
    """Return a random charity whose annual revenue, multiplied by min_years, is <= net_worth_usd."""
    categories = _NTEE_CATEGORIES.copy()
    random.shuffle(categories)

    for category in categories:
        orgs = _search(category)
        qualifying = [
            o for o in orgs
            if o.get("total_revenue") and o["total_revenue"] > 0
            and net_worth_usd >= o["total_revenue"] * min_years
        ]
        if qualifying:
            return random.choice(qualifying)

    return None


def format_revenue(revenue_usd: int) -> str:
    if revenue_usd >= 1_000_000_000:
        return f"${revenue_usd / 1_000_000_000:.1f}B"
    if revenue_usd >= 1_000_000:
        return f"${revenue_usd / 1_000_000:.1f}M"
    return f"${revenue_usd / 1_000:.0f}K"

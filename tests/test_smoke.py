import json
import os

import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "data")

_SAMPLE_BILLIONAIRE = {
    "name": "Elon Musk",
    "net_worth_usd": 200_000_000_000,
    "snapshot_year": 2025,
    "source_url": "https://www.forbes.com/profile/elon-musk/",
    "source_label": "Forbes",
}
_SAMPLE_CHARITY = {
    "name": "American Red Cross",
    "total_revenue": 2_000_000_000,
    "ein": "530196605",
}
_SAMPLE_QUOTE = {
    "text": "The rich will do anything for the poor but get off their backs.",
    "author": "Karl Marx",
    "year": "1867",
    "source": "Das Kapital",
}


# ── Data files ─────────────────────────────────────────────────────────────────

def test_billionaires_json_loads():
    with open(os.path.join(DATA_DIR, "billionaires.json")) as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) > 50


def test_billionaires_required_fields():
    with open(os.path.join(DATA_DIR, "billionaires.json")) as f:
        data = json.load(f)
    for b in data:
        assert "name" in b
        assert "net_worth_usd" in b
        assert "source_url" in b
        assert isinstance(b["net_worth_usd"], (int, float)) and b["net_worth_usd"] > 0


def test_quotes_json_loads():
    with open(os.path.join(DATA_DIR, "quotes.json")) as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) > 50


def test_quotes_required_fields():
    with open(os.path.join(DATA_DIR, "quotes.json")) as f:
        data = json.load(f)
    for q in data:
        assert "text" in q and len(q["text"]) > 0
        assert "author" in q and len(q["author"]) > 0
        assert "year" in q
        assert "source" in q


# ── Charities data file ────────────────────────────────────────────────────────

def test_charities_json_loads():
    with open(os.path.join(DATA_DIR, "charities.json")) as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) > 10


def test_charities_required_fields():
    with open(os.path.join(DATA_DIR, "charities.json")) as f:
        data = json.load(f)
    for c in data:
        assert "name" in c and len(c["name"]) > 0
        assert "ein" in c
        assert "total_revenue" in c and c["total_revenue"] > 0
        assert "source_url" in c


# ── Formatter ──────────────────────────────────────────────────────────────────

def test_post_within_300_chars():
    import formatter
    text, facets = formatter.build_post(_SAMPLE_BILLIONAIRE, _SAMPLE_CHARITY)
    assert len(text) <= 300, f"Post is {len(text)} chars (limit 300)"
    assert "Elon Musk" in text
    assert "American Red Cross" in text
    assert "#eattherich" in text
    assert isinstance(facets, list)


def test_post_long_charity_name_still_fits():
    import formatter
    charity = dict(_SAMPLE_CHARITY, name="National Association for the Advancement of Colored People Legal Defense and Educational Fund")
    text, _ = formatter.build_post(_SAMPLE_BILLIONAIRE, charity)
    assert len(text) <= 300, f"Post is {len(text)} chars with long charity name"


# ── Image generator ────────────────────────────────────────────────────────────

def test_image_is_valid_png_under_1mb():
    import image_generator
    img = image_generator.generate(_SAMPLE_QUOTE)
    assert isinstance(img, bytes)
    assert img[:4] == b"\x89PNG", "Not a valid PNG"
    assert 1_000 < len(img) < 1_000_000, f"Unexpected image size: {len(img)} bytes"


def test_image_alt_text():
    import image_generator
    alt = image_generator.alt_text(_SAMPLE_QUOTE)
    assert _SAMPLE_QUOTE["text"] in alt
    assert _SAMPLE_QUOTE["author"] in alt


# ── Charity matching ───────────────────────────────────────────────────────────

def test_find_qualifying_returns_charity():
    import charities
    charity = charities.find_qualifying(200_000_000_000)
    assert charity is not None
    assert "name" in charity
    assert "total_revenue" in charity
    assert 200_000_000_000 >= charity["total_revenue"] * 100


def test_find_qualifying_none_for_small_net_worth():
    import charities
    assert charities.find_qualifying(1) is None


# ── History / deduplication ────────────────────────────────────────────────────

def test_pick_random_excludes_known():
    import billionaires
    all_names = {b["name"] for b in billionaires.load()}
    one = next(iter(all_names))
    rest = all_names - {one}
    result = billionaires.pick_random(exclude=frozenset(rest))
    assert result["name"] == one


def test_pick_random_falls_back_when_all_excluded():
    import billionaires
    all_names = frozenset(b["name"] for b in billionaires.load())
    result = billionaires.pick_random(exclude=all_names)
    assert result is not None


def test_find_qualifying_excludes_known():
    import charities
    net_worth = 200_000_000_000
    all_qualifying = [c for c in charities._CHARITIES if net_worth >= c["total_revenue"] * 100]
    assert len(all_qualifying) >= 2
    keep = all_qualifying[0]
    exclude = frozenset(c["ein"] for c in all_qualifying[1:])
    result = charities.find_qualifying(net_worth, exclude=exclude)
    assert result["ein"] == keep["ein"]


def test_find_qualifying_falls_back_when_all_excluded():
    import charities
    net_worth = 200_000_000_000
    all_eins = frozenset(c["ein"] for c in charities._CHARITIES)
    result = charities.find_qualifying(net_worth, exclude=all_eins)
    assert result is not None

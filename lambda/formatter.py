from charities import format_revenue

_HASHTAGS = "\n\n#eattherich #taxtherich"
_TAG_LIST = ["eattherich", "taxtherich"]


def build_post(billionaire: dict, charity: dict) -> tuple[str, list[dict]]:
    """
    Returns (post_text, facets). Quote is now in the image, not the text.
    """
    net_worth = billionaire["net_worth_usd"]
    year = billionaire["snapshot_year"]
    revenue = charity["total_revenue"]
    years_funded = net_worth // revenue
    revenue_str = format_revenue(revenue)

    line1 = (
        f"{billionaire['name']} has a net worth of "
        f"${net_worth / 1_000_000_000:.0f}B as of {year} "
        f"(source: {billionaire['source_label']})."
    )
    charity_year = charity.get("snapshot_year", "")
    year_suffix = f", {charity_year} data" if charity_year else ""
    line2 = (
        f"That's {years_funded:,} years of funding for "
        f"{charity['name']} ({revenue_str}/yr budget{year_suffix})."
    )

    post_text = f"{line1}\n\n{line2}{_HASHTAGS}"
    facets = _build_facets(post_text, billionaire, charity)
    return post_text, facets


def _build_facets(text: str, billionaire: dict, charity: dict) -> list[dict]:
    encoded = text.encode("utf-8")
    facets = []
    facets += _find_facets(encoded, billionaire["name"], billionaire["source_url"])
    charity_name = charity["name"]
    charity_url = charity.get("source_url", "")
    if charity_url:
        facets += _find_facets(encoded, charity_name, charity_url)
    for tag in _TAG_LIST:
        facets += _find_tag_facets(encoded, tag)
    return facets


def _find_facets(encoded_text: bytes, search_str: str, uri: str) -> list[dict]:
    search_bytes = search_str.encode("utf-8")
    idx = encoded_text.find(search_bytes)
    if idx == -1:
        return []
    return [{
        "index": {"byteStart": idx, "byteEnd": idx + len(search_bytes)},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": uri}],
    }]


def _find_tag_facets(encoded_text: bytes, tag: str) -> list[dict]:
    search_bytes = f"#{tag}".encode("utf-8")
    idx = encoded_text.find(search_bytes)
    if idx == -1:
        return []
    return [{
        "index": {"byteStart": idx, "byteEnd": idx + len(search_bytes)},
        "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag}],
    }]

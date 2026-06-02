#!/usr/bin/env python3
"""One-time script: applies the 'bot' self-label to the Bluesky account.

Usage:
    python3 scripts/set_bot_label.py <handle> <app-password>

Example:
    python3 scripts/set_bot_label.py billionaire-match.bsky.social xxxx-xxxx-xxxx-xxxx
"""

import json
import sys
import requests

BSKY_HOST = "https://bsky.social"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    handle, app_password = sys.argv[1], sys.argv[2]

    # Authenticate
    session = requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": app_password},
        timeout=10,
    ).json()
    did = session["did"]
    jwt = session["accessJwt"]
    headers = {"Authorization": f"Bearer {jwt}"}

    # Fetch existing profile record
    existing = requests.get(
        f"{BSKY_HOST}/xrpc/com.atproto.repo.getRecord",
        params={"repo": did, "collection": "app.bsky.actor.profile", "rkey": "self"},
        headers=headers,
        timeout=10,
    ).json()

    record = existing.get("value", {})
    record["labels"] = {
        "$type": "com.atproto.label.defs#selfLabels",
        "values": [{"val": "bot"}],
    }

    # Write it back
    resp = requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.repo.putRecord",
        headers=headers,
        json={
            "repo": did,
            "collection": "app.bsky.actor.profile",
            "rkey": "self",
            "record": record,
        },
        timeout=10,
    )
    resp.raise_for_status()
    print("Bot label applied.")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()

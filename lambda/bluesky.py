from datetime import datetime, timezone
import requests

BSKY_HOST = "https://bsky.social"


def _create_session(handle: str, app_password: str) -> dict:
    resp = requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": app_password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _upload_blob(access_jwt: str, image_bytes: bytes) -> dict:
    resp = requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.repo.uploadBlob",
        headers={
            "Authorization": f"Bearer {access_jwt}",
            "Content-Type": "image/png",
        },
        data=image_bytes,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["blob"]


def post(handle: str, app_password: str, text: str, facets: list[dict],
         image_bytes: bytes, image_alt: str) -> dict:
    session = _create_session(handle, app_password)
    access_jwt = session["accessJwt"]
    did = session["did"]

    blob = _upload_blob(access_jwt, image_bytes)

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": created_at,
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{
                "alt": image_alt,
                "image": blob,
                "aspectRatio": {"width": IMAGE_W, "height": IMAGE_H},
            }],
        },
    }
    if facets:
        record["facets"] = facets

    resp = requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {access_jwt}"},
        json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()

    # Disable replies via threadgate (rkey must match the post)
    rkey = result["uri"].split("/")[-1]
    requests.post(
        f"{BSKY_HOST}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {access_jwt}"},
        json={
            "repo": did,
            "collection": "app.bsky.feed.threadgate",
            "rkey": rkey,
            "record": {
                "$type": "app.bsky.feed.threadgate",
                "post": result["uri"],
                "allow": [],
                "createdAt": created_at,
            },
        },
        timeout=10,
    ).raise_for_status()

    return result


IMAGE_W = 1200
IMAGE_H = 630

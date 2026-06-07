import json
import logging
import os

import boto3

import billionaires
import bluesky
import charities
import formatter
import history
import image_generator
import quotes

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_SSM_HANDLE = os.environ.get("SSM_PARAM_HANDLE", "/billionaire-matchmaker/bluesky-handle")
_SSM_PASSWORD = os.environ.get("SSM_PARAM_PASSWORD", "/billionaire-matchmaker/bluesky-app-password")


def _get_ssm(name: str) -> str:
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]


def lambda_handler(event, context):
    used_billionaires = history.get_used_ids("billionaire")
    used_charities = history.get_used_ids("charity")

    billionaire = billionaires.pick_random(exclude=used_billionaires)
    logger.info("Selected billionaire: %s ($%.0fB)", billionaire["name"], billionaire["net_worth_usd"] / 1e9)

    charity = charities.find_qualifying(billionaire["net_worth_usd"], exclude=used_charities)
    if charity is None:
        logger.error("No qualifying charity found for net worth $%.0fB", billionaire["net_worth_usd"] / 1e9)
        return {"statusCode": 500, "body": "No qualifying charity found"}

    logger.info("Selected charity: %s (revenue $%.0fM)", charity["name"], charity["total_revenue"] / 1e6)

    quote = quotes.pick_random()
    logger.info("Selected quote: %.60s…", quote["text"])

    post_text, facets = formatter.build_post(billionaire, charity)
    logger.info("Post text (%d chars):\n%s", len(post_text), post_text)

    img_bytes = image_generator.generate(quote)
    img_alt = image_generator.alt_text(quote)
    logger.info("Generated image: %d bytes", len(img_bytes))

    handle = _get_ssm(_SSM_HANDLE)
    app_password = _get_ssm(_SSM_PASSWORD)

    result = bluesky.post(handle, app_password, post_text, facets, img_bytes, img_alt)
    logger.info("Posted successfully: %s", json.dumps(result))

    history.record_pair(billionaire["name"], charity["ein"])

    return {
        "statusCode": 200,
        "body": json.dumps({
            "billionaire": billionaire["name"],
            "charity": charity["name"],
            "post_chars": len(post_text),
            "image_bytes": len(img_bytes),
            "uri": result.get("uri"),
        }),
    }

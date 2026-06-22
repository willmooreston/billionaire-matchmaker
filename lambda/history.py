import os
import time

import boto3
from boto3.dynamodb.conditions import Key

_TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "")
_TTL_DAYS = 14


def _table():
    return boto3.resource("dynamodb").Table(_TABLE_NAME)


def get_used_ids(entity_type: str) -> frozenset:
    """Return IDs posted in the last TTL_DAYS days."""
    if not _TABLE_NAME:
        return frozenset()
    now = int(time.time())
    response = _table().query(
        KeyConditionExpression=Key("entity_type").eq(entity_type),
        FilterExpression="#ttl > :now",
        ExpressionAttributeNames={"#ttl": "ttl"},
        ExpressionAttributeValues={":now": now},
    )
    return frozenset(item["entity_id"] for item in response.get("Items", []))


def record_pair(billionaire_name: str, charity_ein: str) -> None:
    """Persist both selections with a TTL so DynamoDB auto-expires them."""
    if not _TABLE_NAME:
        return
    table = _table()
    ttl = int(time.time()) + _TTL_DAYS * 86400
    for entity_type, entity_id in [
        ("billionaire", billionaire_name),
        ("charity", charity_ein),
    ]:
        table.put_item(Item={"entity_type": entity_type, "entity_id": entity_id, "ttl": ttl})

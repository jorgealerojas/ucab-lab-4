"""AWS Lambda adapter for SQS batch events."""

from __future__ import annotations

import logging
import os
from typing import Any

from processor import process_job, result_to_item


LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
_DYNAMODB = None


def get_dynamodb():
    global _DYNAMODB
    if _DYNAMODB is None:
        import boto3

        _DYNAMODB = boto3.client("dynamodb")
    return _DYNAMODB


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, list[dict[str, str]]]:
    table_name = os.environ["TABLE_NAME"]
    failures: list[dict[str, str]] = []
    dynamodb = get_dynamodb()

    for record in event.get("Records", []):
        message_id = str(record.get("messageId", ""))
        try:
            result = process_job(record["body"], "faas")
            dynamodb.put_item(TableName=table_name, Item=result_to_item(result))
            LOG.info(
                "processed job_id=%s message_id=%s checksum=%s",
                result["job_id"],
                message_id,
                result["checksum"],
            )
        except Exception:
            LOG.exception("failed message_id=%s", message_id or "unknown")
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}

"""Read-only HTTP API for the laboratory data product."""

from __future__ import annotations

import json
import os
from typing import Any

from processor import JOB_ID_PATTERN, SCHEMA_VERSION, item_to_result


_DYNAMODB = None


def get_dynamodb():
    global _DYNAMODB
    if _DYNAMODB is None:
        import boto3

        _DYNAMODB = boto3.client("dynamodb")
    return _DYNAMODB


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
        },
        "body": json.dumps(body, sort_keys=True, separators=(",", ":")),
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    job_id = (event.get("pathParameters") or {}).get("job_id", "")
    if not isinstance(job_id, str) or not JOB_ID_PATTERN.fullmatch(job_id):
        return response(
            400,
            {
                "schema_version": SCHEMA_VERSION,
                "error": "invalid_job_id",
                "message": "job_id must use 3-64 lowercase letters, digits or hyphens",
            },
        )

    result = get_dynamodb().query(
        TableName=os.environ["TABLE_NAME"],
        KeyConditionExpression="JobId = :job_id",
        ExpressionAttributeValues={":job_id": {"S": job_id}},
        ConsistentRead=True,
    )
    items = result.get("Items", [])
    if not items:
        return response(
            404,
            {
                "schema_version": SCHEMA_VERSION,
                "job_id": job_id,
                "error": "job_not_found",
            },
        )

    converted = sorted((item_to_result(item) for item in items), key=lambda item: item["model"])
    return response(
        200,
        {
            "schema_version": SCHEMA_VERSION,
            "job_id": job_id,
            "result_count": len(converted),
            "results": converted,
        },
    )

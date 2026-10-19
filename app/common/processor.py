"""Pure business logic shared by the IaaS and FaaS workers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "1.0"
JOB_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
Clock = Callable[[], datetime]


class InvalidJob(ValueError):
    """Raised when a queue message does not satisfy the lab contract."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_job(raw: str | bytes | Mapping[str, Any]) -> dict[str, Any]:
    """Parse and validate one job without depending on AWS services."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InvalidJob("the message body must be valid JSON") from exc
    elif isinstance(raw, Mapping):
        value = dict(raw)
    else:
        raise InvalidJob("the job must be a JSON object")

    if not isinstance(value, dict):
        raise InvalidJob("the job must be a JSON object")

    unknown = set(value) - {"job_id", "course", "work_units"}
    if unknown:
        raise InvalidJob(f"unknown fields: {', '.join(sorted(unknown))}")

    job_id = value.get("job_id")
    if not isinstance(job_id, str) or not JOB_ID_PATTERN.fullmatch(job_id):
        raise InvalidJob("job_id must use 3-64 lowercase letters, digits or hyphens")

    course = value.get("course")
    if not isinstance(course, str) or not (2 <= len(course.strip()) <= 40):
        raise InvalidJob("course must contain 2-40 characters")

    work_units = value.get("work_units")
    if isinstance(work_units, bool) or not isinstance(work_units, int):
        raise InvalidJob("work_units must be an integer")
    if not 1 <= work_units <= 5:
        raise InvalidJob("work_units must be between 1 and 5")

    return {
        "job_id": job_id,
        "course": course.strip(),
        "work_units": work_units,
    }


def process_job(
    raw: str | bytes | Mapping[str, Any],
    model: str,
    *,
    clock: Clock = utc_now,
) -> dict[str, Any]:
    """Produce a deterministic result plus execution metadata."""
    if model not in {"iaas", "faas"}:
        raise ValueError("model must be 'iaas' or 'faas'")

    job = parse_job(raw)
    canonical = json.dumps(job, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = canonical
    for _ in range(job["work_units"] * 250):
        digest = hashlib.sha256(digest).digest()

    processed_at = clock()
    if processed_at.tzinfo is None:
        raise ValueError("clock must return a timezone-aware datetime")

    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job["job_id"],
        "model": model,
        "status": "processed",
        "course": job["course"],
        "work_units": job["work_units"],
        "checksum": digest.hex()[:16],
        "processed_at": processed_at.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
    }


def result_to_item(result: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Convert a processed result to the low-level DynamoDB wire shape."""
    required = {
        "schema_version",
        "job_id",
        "model",
        "status",
        "course",
        "work_units",
        "checksum",
        "processed_at",
    }
    missing = required - set(result)
    if missing:
        raise ValueError(f"result is missing fields: {', '.join(sorted(missing))}")

    return {
        "JobId": {"S": str(result["job_id"])},
        "Model": {"S": str(result["model"])},
        "SchemaVersion": {"S": str(result["schema_version"])},
        "Status": {"S": str(result["status"])},
        "Course": {"S": str(result["course"])},
        "WorkUnits": {"N": str(result["work_units"])},
        "Checksum": {"S": str(result["checksum"])},
        "ProcessedAt": {"S": str(result["processed_at"])},
    }


def item_to_result(item: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    """Convert the DynamoDB wire shape to the public data-product schema."""
    return {
        "schema_version": item["SchemaVersion"]["S"],
        "job_id": item["JobId"]["S"],
        "model": item["Model"]["S"],
        "status": item["Status"]["S"],
        "course": item["Course"]["S"],
        "work_units": int(item["WorkUnits"]["N"]),
        "checksum": item["Checksum"]["S"],
        "processed_at": item["ProcessedAt"]["S"],
    }

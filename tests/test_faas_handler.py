from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from helpers import load_module


faas = load_module("faas_lambda", "app/faas/lambda_function.py")


class FakeDynamoDb:
    def __init__(self, fail_job_id=None):
        self.fail_job_id = fail_job_id
        self.puts = []

    def put_item(self, **kwargs):
        job_id = kwargs["Item"]["JobId"]["S"]
        if job_id == self.fail_job_id:
            raise RuntimeError("simulated failure")
        self.puts.append(kwargs)


def record(message_id, body):
    return {
        "messageId": message_id,
        "body": json.dumps(body) if isinstance(body, dict) else body,
    }


class FaaSHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        faas._DYNAMODB = None

    def test_successful_batch(self) -> None:
        db = FakeDynamoDb()
        event = {
            "Records": [
                record("m1", {"job_id": "job-001", "course": "Cloud", "work_units": 1}),
                record("m2", {"job_id": "job-002", "course": "Cloud", "work_units": 2}),
            ]
        }
        with patch.dict(os.environ, {"TABLE_NAME": "results"}), patch.object(
            faas, "get_dynamodb", return_value=db
        ):
            result = faas.lambda_handler(event, None)
        self.assertEqual(result, {"batchItemFailures": []})
        self.assertEqual(len(db.puts), 2)

    def test_partial_batch_failure_only_reports_bad_records(self) -> None:
        db = FakeDynamoDb(fail_job_id="job-003")
        event = {
            "Records": [
                record("m1", {"job_id": "job-001", "course": "Cloud", "work_units": 1}),
                record("m2", "not-json"),
                record("m3", {"job_id": "job-003", "course": "Cloud", "work_units": 1}),
            ]
        }
        with patch.dict(os.environ, {"TABLE_NAME": "results"}), patch.object(
            faas, "get_dynamodb", return_value=db
        ), self.assertLogs(level="ERROR") as captured:
            result = faas.lambda_handler(event, None)
        self.assertEqual(
            result,
            {"batchItemFailures": [{"itemIdentifier": "m2"}, {"itemIdentifier": "m3"}]},
        )
        self.assertEqual(len(db.puts), 1)
        self.assertEqual(len(captured.records), 2)

    def test_empty_event(self) -> None:
        with patch.dict(os.environ, {"TABLE_NAME": "results"}), patch.object(
            faas, "get_dynamodb", return_value=FakeDynamoDb()
        ):
            self.assertEqual(faas.lambda_handler({}, None), {"batchItemFailures": []})


if __name__ == "__main__":
    unittest.main()

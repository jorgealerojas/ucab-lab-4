from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from helpers import COMMON, load_module  # noqa: F401
from processor import process_job, result_to_item


api = load_module("data_api_lambda", "app/data_api/lambda_function.py")


class FakeDynamoDb:
    def __init__(self, items):
        self.items = items
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return {"Items": self.items}


def event(job_id):
    return {"pathParameters": {"job_id": job_id}}


class DataApiTests(unittest.TestCase):
    def setUp(self) -> None:
        api._DYNAMODB = None

    def invoke(self, job_id, items):
        db = FakeDynamoDb(items)
        with patch.dict(os.environ, {"TABLE_NAME": "results"}), patch.object(
            api, "get_dynamodb", return_value=db
        ):
            result = api.lambda_handler(event(job_id), None)
        return result, db

    def test_returns_sorted_results(self) -> None:
        job = {"job_id": "job-001", "course": "Cloud", "work_units": 1}
        items = [
            result_to_item(process_job(job, "iaas")),
            result_to_item(process_job(job, "faas")),
        ]
        result, db = self.invoke("job-001", items)
        body = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["result_count"], 2)
        self.assertEqual([entry["model"] for entry in body["results"]], ["faas", "iaas"])
        self.assertTrue(db.calls[0]["ConsistentRead"])

    def test_not_found(self) -> None:
        result, _ = self.invoke("job-404", [])
        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(json.loads(result["body"])["error"], "job_not_found")

    def test_invalid_job_id_does_not_query(self) -> None:
        result, db = self.invoke("INVALID", [])
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(db.calls, [])


if __name__ == "__main__":
    unittest.main()

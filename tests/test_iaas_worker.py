from __future__ import annotations

import json
import unittest

from helpers import load_module


worker_module = load_module("iaas_worker", "app/iaas/worker.py")


class FakeSqs:
    def __init__(self, messages=None):
        self.messages = messages or []
        self.deleted = []
        self.receive_calls = []

    def receive_message(self, **kwargs):
        self.receive_calls.append(kwargs)
        return {"Messages": self.messages}

    def delete_message(self, **kwargs):
        self.deleted.append(kwargs)


class FakeDynamoDb:
    def __init__(self, fail=False):
        self.fail = fail
        self.puts = []

    def put_item(self, **kwargs):
        if self.fail:
            raise RuntimeError("simulated write failure")
        self.puts.append(kwargs)


def message(body, suffix="1"):
    return {
        "Body": json.dumps(body) if not isinstance(body, str) else body,
        "ReceiptHandle": f"receipt-{suffix}",
        "MessageId": f"message-{suffix}",
    }


class IaasWorkerTests(unittest.TestCase):
    def test_success_writes_before_deleting(self) -> None:
        sqs = FakeSqs()
        db = FakeDynamoDb()
        worker = worker_module.Worker(sqs, db, "queue-url", "table")
        result = worker.process_message(
            message({"job_id": "job-001", "course": "Cloud", "work_units": 1})
        )
        self.assertEqual(result["model"], "iaas")
        self.assertEqual(len(db.puts), 1)
        self.assertEqual(sqs.deleted[0]["ReceiptHandle"], "receipt-1")

    def test_invalid_message_is_not_deleted(self) -> None:
        sqs = FakeSqs([message("not-json")])
        db = FakeDynamoDb()
        worker = worker_module.Worker(sqs, db, "queue-url", "table")
        with self.assertLogs("ucab-lab-4-iaas", level="ERROR"):
            self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(sqs.deleted, [])
        self.assertEqual(db.puts, [])

    def test_write_failure_is_not_deleted(self) -> None:
        sqs = FakeSqs(
            [message({"job_id": "job-001", "course": "Cloud", "work_units": 1})]
        )
        worker = worker_module.Worker(sqs, FakeDynamoDb(fail=True), "queue-url", "table")
        with self.assertLogs("ucab-lab-4-iaas", level="ERROR"):
            self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(sqs.deleted, [])

    def test_empty_poll(self) -> None:
        sqs = FakeSqs()
        worker = worker_module.Worker(sqs, FakeDynamoDb(), "queue-url", "table")
        self.assertEqual(worker.poll_once(), 0)
        self.assertEqual(sqs.receive_calls[0]["WaitTimeSeconds"], 10)


if __name__ == "__main__":
    unittest.main()

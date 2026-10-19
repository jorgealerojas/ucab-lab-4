from __future__ import annotations

import unittest
from datetime import datetime, timezone

from helpers import COMMON  # noqa: F401
from processor import InvalidJob, item_to_result, parse_job, process_job, result_to_item


FIXED_TIME = datetime(2026, 10, 18, 12, 30, 45, 123000, tzinfo=timezone.utc)


class ProcessorTests(unittest.TestCase):
    def test_parse_valid_json(self) -> None:
        self.assertEqual(
            parse_job('{"job_id":"job-001","course":" Cloud ","work_units":2}'),
            {"job_id": "job-001", "course": "Cloud", "work_units": 2},
        )

    def test_rejects_invalid_jobs(self) -> None:
        invalid = [
            "not json",
            "[]",
            '{"job_id":"UPPER","course":"Cloud","work_units":1}',
            '{"job_id":"job-1","course":"C","work_units":1}',
            '{"job_id":"job-1","course":"Cloud","work_units":0}',
            '{"job_id":"job-1","course":"Cloud","work_units":true}',
            '{"job_id":"job-1","course":"Cloud","work_units":1,"extra":1}',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(InvalidJob):
                parse_job(raw)

    def test_two_models_have_same_business_result(self) -> None:
        job = {"job_id": "job-042", "course": "Cloud", "work_units": 3}
        iaas = process_job(job, "iaas", clock=lambda: FIXED_TIME)
        faas = process_job(job, "faas", clock=lambda: FIXED_TIME)
        self.assertEqual(iaas["checksum"], faas["checksum"])
        self.assertEqual(iaas["processed_at"], "2026-10-18T12:30:45.123Z")
        self.assertEqual({iaas["model"], faas["model"]}, {"iaas", "faas"})

    def test_rejects_unknown_model_and_naive_clock(self) -> None:
        job = {"job_id": "job-042", "course": "Cloud", "work_units": 1}
        with self.assertRaises(ValueError):
            process_job(job, "paas")
        with self.assertRaises(ValueError):
            process_job(job, "iaas", clock=lambda: datetime(2026, 1, 1))

    def test_dynamodb_round_trip(self) -> None:
        result = process_job(
            {"job_id": "job-042", "course": "Cloud", "work_units": 2},
            "faas",
            clock=lambda: FIXED_TIME,
        )
        self.assertEqual(item_to_result(result_to_item(result)), result)


if __name__ == "__main__":
    unittest.main()

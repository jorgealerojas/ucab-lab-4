"""Long-polling SQS worker operated as a systemd service on EC2."""

from __future__ import annotations

import logging
import os
import signal
from typing import Any

from processor import InvalidJob, process_job, result_to_item


LOG = logging.getLogger("ucab-lab-4-iaas")


class Worker:
    def __init__(self, sqs: Any, dynamodb: Any, queue_url: str, table_name: str) -> None:
        self.sqs = sqs
        self.dynamodb = dynamodb
        self.queue_url = queue_url
        self.table_name = table_name

    def process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        result = process_job(message["Body"], "iaas")
        self.dynamodb.put_item(TableName=self.table_name, Item=result_to_item(result))
        self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        LOG.info(
            "processed job_id=%s message_id=%s checksum=%s",
            result["job_id"],
            message.get("MessageId", "unknown"),
            result["checksum"],
        )
        return result

    def poll_once(self) -> int:
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10,
            VisibilityTimeout=30,
        )
        messages = response.get("Messages", [])
        for message in messages:
            try:
                self.process_message(message)
            except (InvalidJob, KeyError, TypeError, ValueError):
                LOG.exception(
                    "rejected message_id=%s; it remains in SQS for retry",
                    message.get("MessageId", "unknown"),
                )
            except Exception:
                LOG.exception(
                    "processing failed message_id=%s; it remains in SQS for retry",
                    message.get("MessageId", "unknown"),
                )
        return len(messages)


def build_worker() -> Worker:
    import boto3

    queue_url = os.environ["QUEUE_URL"]
    table_name = os.environ["TABLE_NAME"]
    region = os.environ.get("AWS_REGION", "us-east-2")
    return Worker(
        boto3.client("sqs", region_name=region),
        boto3.client("dynamodb", region_name=region),
        queue_url,
        table_name,
    )


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    worker = build_worker()
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False
        LOG.info("shutdown requested")

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    LOG.info("worker started queue=%s table=%s", worker.queue_url, worker.table_name)
    while running:
        worker.poll_once()
    LOG.info("worker stopped")


if __name__ == "__main__":
    main()

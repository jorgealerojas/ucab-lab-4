#!/usr/bin/env python3
"""Invoke the IAM-protected HTTP API using the active AWS credentials."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def stack_output(stack_name: str, key: str, region: str) -> str:
    command = [
        "aws",
        "cloudformation",
        "describe-stacks",
        "--region",
        region,
        "--stack-name",
        stack_name,
        "--query",
        f"Stacks[0].Outputs[?OutputKey=='{key}'].OutputValue | [0]",
        "--output",
        "text",
    ]
    return subprocess.check_output(command, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id")
    parser.add_argument("--stack-name")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-2"))
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(repo_root, ".ucab-lab-4-stack")
    stack_name = args.stack_name
    if not stack_name:
        try:
            with open(state_file, encoding="utf-8") as stream:
                stack_name = stream.read().strip()
        except FileNotFoundError:
            parser.error("no stack name and no .ucab-lab-4-stack file")

    endpoint = stack_output(stack_name, "DataApiEndpoint", args.region)
    url = f"{endpoint}/jobs/{args.job_id}"

    try:
        import botocore.auth
        import botocore.awsrequest
        import botocore.exceptions
        import botocore.httpsession
        import botocore.session
    except ImportError:
        print("ERROR: botocore no esta instalado", file=sys.stderr)
        return 2

    session = botocore.session.get_session()
    credentials = session.get_credentials()
    if credentials is None:
        print("ERROR: no hay credenciales AWS activas", file=sys.stderr)
        return 2
    request = botocore.awsrequest.AWSRequest(method="GET", url=url)
    botocore.auth.SigV4Auth(credentials.get_frozen_credentials(), "execute-api", args.region).add_auth(request)
    try:
        response = botocore.httpsession.URLLib3Session(timeout=15).send(request.prepare())
    except botocore.exceptions.BotoCoreError as exc:
        print(f"ERROR: no se pudo consultar la API: {exc}", file=sys.stderr)
        return 1
    text = response.content.decode("utf-8", errors="replace")
    if not 200 <= response.status_code < 300:
        print(text, file=sys.stderr)
        return 1
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        print("ERROR: la API no devolvio JSON valido", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

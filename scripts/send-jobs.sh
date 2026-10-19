#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
require_command python3
load_stack_name

COUNT="${1:-6}"
if [[ ! "$COUNT" =~ ^[0-9]+$ ]] || ((COUNT < 1 || COUNT > 20)); then
  die "La cantidad debe estar entre 1 y 20"
fi
IAAS_QUEUE="$(stack_output IaasQueueUrl)"
FAAS_QUEUE="$(stack_output FaaSQueueUrl)"
BATCH_ID="$(date -u +%H%M%S)-$(python3 -c 'import secrets; print(secrets.token_hex(2))')"
JOBS_FILE="$REPO_ROOT/.ucab-lab-4-last-jobs"
: >"$JOBS_FILE"

echo "Enviando $COUNT trabajos identicos a ambos carriles..."
for ((i = 1; i <= COUNT; i++)); do
  job_id="job-$BATCH_ID-$(printf '%02d' "$i")"
  units="$(((i - 1) % 5 + 1))"
  body="$(python3 -c 'import json,sys; print(json.dumps({"job_id":sys.argv[1],"course":"computacion-en-la-nube","work_units":int(sys.argv[2])},separators=(",",":")))' "$job_id" "$units")"
  aws sqs send-message --region "$REGION" --queue-url "$IAAS_QUEUE" --message-body "$body" --output text --query MessageId >/dev/null
  aws sqs send-message --region "$REGION" --queue-url "$FAAS_QUEUE" --message-body "$body" --output text --query MessageId >/dev/null
  printf '%s\n' "$job_id" >>"$JOBS_FILE"
  echo "  enviado $job_id (work_units=$units)"
done
echo "IDs guardados en $JOBS_FILE"

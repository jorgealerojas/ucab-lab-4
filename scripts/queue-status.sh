#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name

for model in IaaS FaaS; do
  if [[ "$model" == "IaaS" ]]; then
    queue="$(stack_output IaasQueueUrl)"
  else
    queue="$(stack_output FaaSQueueUrl)"
  fi
  echo "$model"
  aws sqs get-queue-attributes \
    --region "$REGION" \
    --queue-url "$queue" \
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
    --query 'Attributes' \
    --output table
done
echo "Nota: los contadores de SQS son aproximados y pueden tardar en actualizarse."

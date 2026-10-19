#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name
JOBS_FILE="$REPO_ROOT/.ucab-lab-4-last-jobs"
[[ -s "$JOBS_FILE" ]] || die "No hay IDs recientes. Ejecute scripts/send-jobs.sh."
TABLE="$(stack_output ResultsTableName)"

printf '%-30s %-18s %s\n' JOB_ID MODELOS RESULTADOS
while IFS= read -r job_id; do
  models="$(aws dynamodb query \
    --region "$REGION" \
    --table-name "$TABLE" \
    --consistent-read \
    --key-condition-expression 'JobId = :job_id' \
    --expression-attribute-values "{\":job_id\":{\"S\":\"$job_id\"}}" \
    --query 'sort_by(Items,&Model.S)[].Model.S' \
    --output text)"
  count="$(wc -w <<<"$models" | tr -d ' ')"
  printf '%-30s %-18s %s/2\n' "$job_id" "${models:-pendiente}" "$count"
done <"$JOBS_FILE"

#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name
JOBS_FILE="$REPO_ROOT/.ucab-lab-4-last-jobs"
[[ -s "$JOBS_FILE" ]] || die "No hay IDs para verificar"
TABLE="$(stack_output ResultsTableName)"
deadline=$((SECONDS + 60))
while true; do
  failures=0
  summary=""
  while IFS= read -r job_id; do
    count="$(aws dynamodb query \
      --region "$REGION" \
      --table-name "$TABLE" \
      --consistent-read \
      --key-condition-expression 'JobId = :job_id' \
      --expression-attribute-values "{\":job_id\":{\"S\":\"$job_id\"}}" \
      --select COUNT --query Count --output text)"
    if [[ "$count" == "2" ]]; then
      summary+="OK $job_id: IaaS + FaaS"$'\n'
    else
      summary+="PENDIENTE $job_id: $count/2"$'\n'
      failures=$((failures + 1))
    fi
  done <"$JOBS_FILE"
  if ((failures == 0)); then
    printf '%s' "$summary"
    break
  fi
  if ((SECONDS >= deadline)); then
    printf '%s' "$summary" >&2
    die "$failures trabajos no completaron en 60 segundos"
  fi
  echo "Esperando ambos carriles: $failures trabajos pendientes..."
  sleep 5
done

first_job="$(head -n 1 "$JOBS_FILE")"
api_ok=false
for attempt in 1 2 3; do
  if python3 "$SCRIPT_DIR/query-data-product.py" "$first_job" >/dev/null; then
    api_ok=true
    break
  fi
  echo "API aun no disponible (intento $attempt/3); esperando..."
  sleep 5
done
[[ "$api_ok" == "true" ]] || die "La API no respondio correctamente"
echo "OK producto de datos accesible con IAM"
echo "Verificacion completa"

#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name
echo "Eliminando exactamente el stack $LAB_STACK..."
aws cloudformation delete-stack --region "$REGION" --stack-name "$LAB_STACK"
aws cloudformation wait stack-delete-complete --region "$REGION" --stack-name "$LAB_STACK"
rm -f "$STATE_FILE" "$REPO_ROOT/.ucab-lab-4-last-jobs"
echo "LIMPIEZA COMPLETA: $LAB_STACK ya no existe"

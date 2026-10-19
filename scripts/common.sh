#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$REPO_ROOT/.ucab-lab-4-stack"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Falta el comando requerido: $1"
}

load_stack_name() {
  if [[ -n "${STACK_NAME:-}" ]]; then
    LAB_STACK="$STACK_NAME"
  elif [[ -f "$STATE_FILE" ]]; then
    LAB_STACK="$(tr -d '[:space:]' <"$STATE_FILE")"
  else
    die "No se encontro $STATE_FILE. Ejecute primero scripts/deploy-lab.sh."
  fi
  [[ "$LAB_STACK" =~ ^ucab-lab-4-[a-f0-9]{12}$ ]] || die "Nombre de stack no valido: $LAB_STACK"
}

stack_output() {
  local key="$1"
  aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$LAB_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

run_ssm_command() {
  local commands_json="$1"
  local instance_id command_id status
  instance_id="$(stack_output InstanceId)"
  command_id="$(aws ssm send-command \
    --region "$REGION" \
    --instance-ids "$instance_id" \
    --document-name AWS-RunShellScript \
    --parameters "commands=$commands_json" \
    --query 'Command.CommandId' \
    --output text)"
  aws ssm wait command-executed \
    --region "$REGION" \
    --command-id "$command_id" \
    --instance-id "$instance_id" || true
  status="$(aws ssm get-command-invocation \
    --region "$REGION" \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query Status --output text)"
  aws ssm get-command-invocation \
    --region "$REGION" \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query StandardOutputContent --output text
  [[ "$status" == "Success" ]] || die "El comando SSM termino con estado $status"
}

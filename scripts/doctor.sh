#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name
[[ "$REGION" == "us-east-2" ]] || die "Region incorrecta: $REGION"

status="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$LAB_STACK" --query 'Stacks[0].StackStatus' --output text)"
[[ "$status" == "CREATE_COMPLETE" || "$status" == "UPDATE_COMPLETE" ]] || die "Stack en estado $status"
echo "OK stack: $LAB_STACK ($status)"

instance_id="$(stack_output InstanceId)"
ping_status="$(aws ssm describe-instance-information \
  --region "$REGION" \
  --filters "Key=InstanceIds,Values=$instance_id" \
  --query 'InstanceInformationList[0].PingStatus' --output text)"
[[ "$ping_status" == "Online" ]] || die "La instancia no esta Online en SSM: $ping_status"
echo "OK SSM: $instance_id Online"

run_ssm_command '["systemctl is-active ucab-iaas-worker.service","/opt/ucab-lab-4/venv/bin/python --version"]'
echo "OK worker IaaS: activo"

function_name="$(stack_output FaaSFunctionName)"
function_state="$(aws lambda get-function-configuration --region "$REGION" --function-name "$function_name" --query State --output text)"
[[ "$function_state" == "Active" ]] || die "Lambda no esta activa: $function_state"
echo "OK worker FaaS: $function_name Active"

echo "OK tabla: $(stack_output ResultsTableName)"
echo "OK API con IAM: $(stack_output DataApiEndpoint)"
echo "Entorno listo"

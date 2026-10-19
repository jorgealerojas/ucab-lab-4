#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"
STATE_FILE="$REPO_ROOT/.ucab-lab-4-stack"
BUILD_DIR="$(mktemp -d)"
ARTIFACT_BUCKET=""

cleanup() {
  rm -rf "$BUILD_DIR"
  if [[ -n "$ARTIFACT_BUCKET" ]]; then
    aws s3 rm "s3://$ARTIFACT_BUCKET" --recursive --region "$REGION" >/dev/null 2>&1 || true
    aws s3api delete-bucket --bucket "$ARTIFACT_BUCKET" --region "$REGION" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for cmd in aws python3 zip tar; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: falta $cmd" >&2; exit 1; }
done
[[ "$REGION" == "us-east-2" ]] || { echo "ERROR: use us-east-2; region actual: $REGION" >&2; exit 1; }
[[ ! -f "$STATE_FILE" ]] || { echo "ERROR: ya existe un laboratorio registrado en $STATE_FILE" >&2; exit 1; }

aws sts get-caller-identity --region "$REGION" >/dev/null
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
SUFFIX="$(python3 -c 'import secrets; print(secrets.token_hex(6))')"
STACK_NAME="ucab-lab-4-$SUFFIX"
ARTIFACT_BUCKET="ucab-lab-4-$ACCOUNT_ID-$SUFFIX"

echo "Identificador generado: $STACK_NAME"
echo "Empaquetando el codigo..."
"$SCRIPT_DIR/package-artifacts.sh" "$BUILD_DIR"

echo "Creando almacen temporal de artefactos..."
aws s3api create-bucket \
  --bucket "$ARTIFACT_BUCKET" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
aws s3 cp "$BUILD_DIR/faas-worker.zip" "s3://$ARTIFACT_BUCKET/faas-worker.zip" --region "$REGION" --only-show-errors
aws s3 cp "$BUILD_DIR/data-api.zip" "s3://$ARTIFACT_BUCKET/data-api.zip" --region "$REGION" --only-show-errors
aws s3 cp "$BUILD_DIR/iaas-worker.tar.gz" "s3://$ARTIFACT_BUCKET/iaas-worker.tar.gz" --region "$REGION" --only-show-errors

echo "Creando el laboratorio; normalmente tarda entre 4 y 8 minutos..."
if ! aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$REPO_ROOT/infra/lab-stack.yaml" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    ArtifactBucket="$ARTIFACT_BUCKET" \
    IaasArtifactKey=iaas-worker.tar.gz \
    FaaSArtifactKey=faas-worker.zip \
    ApiArtifactKey=data-api.zip; then
  echo "ERROR: el despliegue fallo. Revise CloudFormation y elimine el stack $STACK_NAME." >&2
  exit 1
fi

printf '%s\n' "$STACK_NAME" >"$STATE_FILE"
echo "LABORATORIO LISTO: $STACK_NAME"
echo "Ejecute: ./scripts/doctor.sh"

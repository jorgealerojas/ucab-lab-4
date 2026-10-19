#!/usr/bin/env bash

set -Eeuo pipefail
# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_command aws
load_stack_name
run_ssm_command '["sudo systemctl start ucab-iaas-worker.service","systemctl is-active ucab-iaas-worker.service"]'
echo "Worker IaaS restaurado. Debe comenzar a drenar su cola."

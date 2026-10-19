PYTHON ?= python3
BUILD_DIR ?= build

.PHONY: test package python-check ruff-check bash-check cfn-check docs-check shellcheck validate clean

test:
	$(PYTHON) -m unittest discover -s tests -v

package:
	./scripts/package-artifacts.sh $(BUILD_DIR)

python-check:
	$(PYTHON) -m compileall -q app scripts tests

ruff-check:
	@if command -v ruff >/dev/null 2>&1; then ruff check app tests scripts/query-data-product.py; else echo "ruff no instalado; comprobacion omitida"; fi

bash-check:
	@for file in scripts/*.sh; do bash -n "$$file"; done

cfn-check:
	cfn-lint infra/lab-stack.yaml

docs-check:
	$(PYTHON) -m unittest tests.test_repository -v

shellcheck:
	@if command -v shellcheck >/dev/null 2>&1; then shellcheck scripts/*.sh; else echo "shellcheck no instalado; comprobacion omitida"; fi

validate: test python-check ruff-check bash-check cfn-check docs-check shellcheck package

clean:
	rm -rf $(BUILD_DIR) app/common/__pycache__ app/iaas/__pycache__ app/faas/__pycache__ app/data_api/__pycache__ scripts/__pycache__ tests/__pycache__

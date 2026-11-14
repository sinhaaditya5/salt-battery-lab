# Salt Battery Lab: common entry points. Run `make help` for the list.
SHELL      := /bin/bash
PYTHON     ?= python3.12
VENV       ?= .venv
PY         := $(VENV)/bin/python
LAB_PATH   := /Volumes/Aditya ssd/Salt-Battery-Lab
CORE_TESTS := tests/test_params.py tests/test_sim_models.py tests/test_docs_lint.py \
              tests/test_s11_dft.py tests/test_project_salt.py tests/test_salt_designs.py

.DEFAULT_GOAL := help
.PHONY: help setup fetch-assets check test test-all firmware-test assets rebuild rebuild-fast clean link

help: ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create the venv and install the pinned CI requirements
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements/ci.txt

fetch-assets: ## Download MACE-MP weights and Freerouting (SHA-256 verified)
	scripts/fetch_assets.sh

link: ## Expose this clone at the lab path the scripts expect (needs sudo outside macOS)
	@if [ "$$(cd "$(LAB_PATH)" 2>/dev/null && pwd -P)" = "$$(pwd -P)" ]; then echo "lab path already points here"; \
	else sudo mkdir -p "$$(dirname "$(LAB_PATH)")" && sudo ln -sfn "$$(pwd -P)" "$(LAB_PATH)" && echo "linked $(LAB_PATH) -> $$(pwd -P)"; fi

check: ## Repository integrity gate (secrets, sizes, JSON/CSV/Python validity)
	$(PYTHON) scripts/check_repo.py

test: ## Core test suites (no CAD/DFT/Blender/KiCad toolchain needed)
	$(PY) -m pytest $(CORE_TESTS)

test-all: ## Every suite, including CAD (needs build123d/OCP)
	$(PY) -m pytest

firmware-test: ## SCM-1 firmware host unit tests (C11, -Werror)
	$(MAKE) -C pcb/scell_monitor/firmware test

assets: ## Regenerate README imagery in docs/assets (banner, turntable GIF, renders, charts)
	$(PY) scripts/make_readme_assets.py

rebuild-fast: ## Rebuild every output, reusing ML-potential runs and renders (~15 min)
	./run_all.sh --fast

rebuild: ## Full rebuild, including the uMLIP screen (~1 h) and Blender renders
	./run_all.sh

clean: ## Remove caches and host test binaries
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
	$(MAKE) -C pcb/scell_monitor/firmware clean

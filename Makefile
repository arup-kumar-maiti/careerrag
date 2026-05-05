.PHONY: setup install check test clean

PYTHON := $(shell command -v python3 || command -v python)

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install dryclean -e ".[dev]"
	.venv/bin/dryclean init

install:
	.venv/bin/pip install -e ".[dev]"

check:
	.venv/bin/dryclean run

test:
	.venv/bin/pytest tests/

clean:
	rm -rf *.egg-info/ .mypy_cache/ .pytest_cache/ .ruff_cache/ build/ dist/

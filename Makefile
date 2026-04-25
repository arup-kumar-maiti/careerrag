.PHONY: setup

PYTHON := $(shell command -v python3 || command -v python)

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install dryclean
	.venv/bin/dryclean init
	@echo "Run 'source .venv/bin/activate' to activate the environment"

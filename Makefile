VIRTUAL_ENV ?= venv

lint: install
	$(VIRTUAL_ENV)/bin/flake8 merkle_drop tests
	$(VIRTUAL_ENV)/bin/black --check merkle_drop tests
	$(VIRTUAL_ENV)/bin/mypy --ignore-missing-imports merkle_drop tests

test: install
	$(VIRTUAL_ENV)/bin/pytest tests

compile: install-requirements
	$(VIRTUAL_ENV)/bin/deploy-tools compile --evm-version petersburg -d ./contracts/contracts
	cp build/contracts.json merkle_drop/contracts.json
	cp build/contracts.json tests/helper/contracts.json


build: compile
	$(VIRTUAL_ENV)/bin/python setup.py sdist

install-requirements: .installed

install: install-requirements compile
	$(VIRTUAL_ENV)/bin/pip install -c constraints.txt -e .

.installed: constraints.txt requirements.txt $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/pip install -c constraints.txt pip wheel setuptools
	$(VIRTUAL_ENV)/bin/pip install -c constraints.txt -r requirements.txt
	@echo "This file controls for make if the requirements in your virtual env are up to date" > $@

$(VIRTUAL_ENV):
	python3 -m venv $@

.PHONY: install install-requirements test lint compile build

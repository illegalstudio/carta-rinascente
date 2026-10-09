PYTHON ?= .venv/bin/python
SYSTEM_PYTHON ?= python3

.PHONY: setup build test check package release release-dry-run

setup:
	$(SYSTEM_PYTHON) -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

build:
	$(PYTHON) -m src all

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	$(PYTHON) -m src all --check-reproducible

package:
	$(PYTHON) -m src.distribution

# Propose a version, confirm, verify, commit release files, then tag and push.
release:
	$(PYTHON) -m src.release

# Inspect the proposed release without changing files, tags or remote state.
release-dry-run:
	$(PYTHON) -m src.release --dry-run

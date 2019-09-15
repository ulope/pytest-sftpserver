.PHONY: help lint style isort black flake8

help:
	@echo Available targets
	@echo - lint:  Run lint / style checks on code
	@echo - style: Apply isort / black on the code to enforce style rules

lint: ISORT_CHECK_PARAMS := --diff --check-only
lint: BLACK_CHECK_PARAMS := --check --diff
lint: isort black flake8

style: isort black

isort:
	isort $(ISORT_CHECK_PARAMS) --recursive pytest_sftpserver tests

black:
	black $(BLACK_CHECK_PARAMS) pytest_sftpserver tests

flake8:
	flake8 pytest_sftpserver tests

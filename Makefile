prepare:
	@black .
	@isort .
	@mypy
	@pylint action
	@flake8 .
	@bandit -r action
	@echo Good to Go!

check:
	@black . --check
	@isort . --check
	@mypy
	@flake8 .
	@pylint action
	@bandit -r action
	@echo Good to Go!

test:
	@pytest --cov action

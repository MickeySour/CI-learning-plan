.PHONY: lint format-check test build run

lint:
	ruff check .

format-check:
	ruff format --check .

format:
	ruff format .

test:
	pytest --tb=short

coverage:
	pytest --cov=app --cov-report=html

build:
	python -m build

run:
	uvicorn app.main:app --reload

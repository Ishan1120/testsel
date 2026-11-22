.PHONY: help install up down psql test lint fmt collect

.DEFAULT_GOAL := help

help:
	@echo "Available make targets:"
	@echo "  install   Install package in editable mode with development dependencies"
	@echo "  up        Start PostgreSQL in the background using Docker Compose"
	@echo "  down      Stop Docker Compose services"
	@echo "  psql      Open a psql session to the local PostgreSQL database"
	@echo "  test      Run test suite with pytest"
	@echo "  lint      Run ruff check and ruff format in check mode"
	@echo "  fmt       Format code and apply safe fixes with ruff"
	@echo "  collect   Run testsel collector for all repositories in configs/repos.yaml"

install:
	pip install -e ".[dev]"

up:
	docker compose up -d --wait postgres

down:
	docker compose down

psql:
	docker compose exec postgres psql -U testsel -d testsel

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff check --fix .
	ruff format .

collect:
	testsel collect-all --config configs/repos.yaml

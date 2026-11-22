# Agent Guidance for Testsel Monorepo

This repository is a predictive test selection monorepo designed for automated AI agents and developers. Follow these boundaries and practices.

## Repository Layout & Ownership
- `src/testsel/collector/`: GitHub API ingestion and JUnit parsing (Owner: Person A, Phase 1).
- `src/testsel/features/`: Feature engineering from commits, PRs, and test runs (Owner: Person A, Phase 3).
- `src/testsel/evaluation/`: Evaluation metrics, time splits, baseline heuristics (Owner: Person A, Phase 2).
- `src/testsel/training/`: ML training pipelines and hyperparameter tuning (Owner: Person A, Phase 3).
- `src/testsel/serving/`: Inference engine and test ranking logic (Owner: Person B, Phase 4).
- `src/testsel/api/`: FastAPI webhook server and GitHub App handlers (Owner: Person B, Phase 4).
- `src/testsel/worker/`: Asynchronous background task workers (Owner: Person B, Phase 4).
- `src/testsel/shared/`: Shared models, DB store, configuration (Shared ownership).
- `web/`: Frontend dashboard (Owner: Person B, Phase 5).
- `db/`: SQL schemas and database migrations (Shared ownership).
- `infra/`: Docker, k8s, monitoring configurations (Owner: Person B).

## Essential Commands
Agents must verify code changes with the following commands:
- Run tests: `make test` (or `pytest -q`)
- Run linting: `make lint` (or `ruff check . && ruff format --check .`)
- Autoformat code: `make fmt` (or `ruff check --fix . && ruff format .`)
- Start local database: `make up` (or `docker compose up -d postgres`)
- Stop services: `make down` (or `docker compose down`)

## Strict Conventions & Security
- **Never commit secrets**: Do not create or commit real credentials, GitHub tokens, or live database passwords. Use `.env.example` placeholders.
- **Never commit data**: The `data/` folder and `_existing/` directory are gitignored. Do not stage bulk data or archives.
- **Typing & Formatting**: Target Python 3.12. Use strict type annotations, `from __future__ import annotations`, and comply with Ruff rules (E, F, I, B, UP).

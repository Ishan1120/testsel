# Agent Guidelines for testsel

This document defines conventions and guardrails for autonomous agents and AI assistants working in this repository.

## Repository Layout & Responsibilities
- `src/testsel/shared/`: Shared config, DB store, database models. Co-owned by Person A and Person B.
- `src/testsel/collector/`: GitHub client, JUnit XML parser, workflow collection loop (Owner: Person A, Phase 1).
- `src/testsel/features/`: Feature engineering from code diffs and test history (Owner: Person A, Phase 3).
- `src/testsel/evaluation/`: Time-split evaluation, ranking metrics (APFD, recall@k), baselines (Owner: Person A, Phase 2).
- `src/testsel/training/`: Model training pipelines using LightGBM / MLflow (Owner: Person A, Phase 3).
- `src/testsel/serving/`: Model inference and scoring service (Owner: Person B, Phase 4).
- `src/testsel/api/`: FastAPI webhook receiver and management API (Owner: Person B, Phase 4).
- `src/testsel/worker/`: Asynchronous background task consumer (Owner: Person B, Phase 4).
- `web/`: React frontend dashboard (Phase 5).
- `db/`: Schema definitions and SQL migrations.

## Safety & Boundaries
- **NEVER commit real credentials, GitHub tokens, or passwords.** Only use `.env.example` placeholders.
- **NEVER commit large datasets or binary artifacts.** Place them under `data/`, which is excluded by `.gitignore`.
- **Do not run global package installations.** Always operate within the project virtual environment (`.venv`).
- **Do not run git push or remote commands directly** unless explicitly instructed by the user.

## Code Standards & Verification Commands
- Before completing tasks, always execute:
  ```bash
  make lint  # runs ruff check . and ruff format --check .
  make test  # runs pytest -q
  ```
- Maximum line length is 100 characters.
- Maintain type annotations and docstrings on all public functions and classes.
- At the end of every task, update docs/PROGRESS.md: tick finished items, add a dated log line, refresh Next up.

# Development Guide

This guide covers local environment setup, developer workflows, repository layout, task automation, and troubleshooting for `testsel`.

## Prerequisites
- **Python 3.12+**
- **Docker & Docker Compose** (for local PostgreSQL 16)
- **Git** (Git Bash recommended on Windows)
- **Make** (optional; standard command-line equivalents are documented below)

---

## Quickstart

### On Windows (Git Bash)
```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/Scripts/activate

# 2. Install package in editable mode with development dependencies
make install
# (Or directly: pip install -e ".[dev]")

# 3. Setup pre-commit git hooks
pre-commit install

# 4. Configure local environment variables
cp .env.example .env

# 5. Start local PostgreSQL database container
make up
# (Or directly: docker compose up -d --wait postgres)

# 6. Run linters and test suite
make lint
make test
```

### On macOS / Linux
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install package in editable mode with development dependencies
make install
# (Or directly: pip install -e ".[dev]")

# 3. Setup pre-commit git hooks
pre-commit install

# 4. Configure local environment variables
cp .env.example .env

# 5. Start local PostgreSQL database container
make up
# (Or directly: docker compose up -d --wait postgres)

# 6. Run linters and test suite
make lint
make test
```

---

## Make Commands Reference

| Target | Command | Purpose |
| :--- | :--- | :--- |
| `make help` | `make help` | Display available targets |
| `make install`| `pip install -e ".[dev]"` | Install package in editable mode with dev dependencies |
| `make up` | `docker compose up -d --wait postgres` | Start PostgreSQL 16 container with health check |
| `make down` | `docker compose down` | Stop and remove running containers |
| `make psql` | `docker compose exec postgres psql -U testsel -d testsel` | Connect interactive psql shell to local database |
| `make test` | `pytest -q` | Run test suite with pytest |
| `make lint` | `ruff check . && ruff format --check .` | Check linting and formatting rules |
| `make fmt` | `ruff check --fix . && ruff format .` | Auto-format and apply safe fixes |
| `make collect`| `testsel collect-all --config configs/repos.yaml` | Run data collection pipeline |

---

## Repository Layout

```text
testsel/
├── .github/              # CI/CD workflows, issue/PR templates, CODEOWNERS
├── configs/              # Repository scraping and environment configurations
├── data/                 # Local data directory for artifacts (gitignored)
├── db/                   # PostgreSQL schema and migration scripts
├── docs/                 # Architecture diagrams, ADRs, dataset notes, progress logs
├── infra/                # Dockerfiles, docker-compose, and K8s manifests
├── notebooks/            # Exploration and ML experimentation notebooks
├── scripts/              # Utility and data extraction scripts
├── src/testsel/          # Main application package
│   ├── api/              # FastAPI webhook & REST endpoints
│   ├── collector/        # GitHub API crawler & JUnit XML parser
│   ├── evaluation/       # Time-split evaluation & ranking metrics
│   ├── features/         # Feature engineering pipeline
│   ├── serving/          # Real-time ML inference service
│   ├── shared/           # Database store, models, and shared utilities
│   ├── training/         # Model training & registry scripts
│   ├── worker/           # Asynchronous task workers
│   └── cli.py            # Console entrypoint (`testsel`)
├── tests/                # Unit, integration, and fixture test suites
├── web/                  # React visualization dashboard (future phase)
├── docker-compose.yml    # Local services (PostgreSQL 16, collector)
├── Makefile              # Developer task automation
└── pyproject.toml        # Project dependencies and tool configurations
```

---

## Team Workflow & Ownership

### Branching & Commits
- Use descriptive branch prefixes: `feat/<description>`, `fix/<description>`, `docs/<description>`, `chore/<description>`.
- Write commit messages adhering to [Conventional Commits](https://www.conventionalcommits.org/):
  `feat: add PR diff parsing`, `fix: handle empty JUnit testsuite tag`.

### Pull Request Rules
- Keep pull requests focused and under ~400 lines of code.
- Require review and approval from your teammate prior to merging.
- Use **Squash and Merge** to maintain a linear git history on `main`.
- Update [docs/PROGRESS.md](PROGRESS.md) whenever starting or finishing a roadmap milestone.

### Ownership Matrix

| Component / Directory | Owner | Phase | Responsibility |
| :--- | :--- | :--- | :--- |
| `src/testsel/collector/` | **Person A** | Phase 1 | GitHub API client, JUnit parsing, scraper |
| `src/testsel/evaluation/`| **Person A** | Phase 2 | Ranking metrics (APFD), time splits |
| `src/testsel/features/`  | **Person A** | Phase 3 | Diff parsing, change frequencies, code churn |
| `src/testsel/training/`  | **Person A** | Phase 3 | LightGBM ranking models, MLflow |
| `src/testsel/serving/`   | **Person B** | Phase 4 | Low-latency inference server |
| `src/testsel/api/`       | **Person B** | Phase 4 | FastAPI webhook ingestion |
| `src/testsel/worker/`    | **Person B** | Phase 4 | Task queue and async processing |
| `web/`                   | **Person B** | Phase 5 | React management dashboard |
| `infra/` & `.github/`    | **Person B** | All | CI/CD, deployment, Docker |
| `src/testsel/shared/`    | **Both**    | All | Models, configuration, database store |
| `db/`                    | **Both**    | All | Schema design and migrations |

---

## Troubleshooting

- **Port 5432 already in use**:
  If a local PostgreSQL instance is running on your host machine, stop it or update the external port mapping in `docker-compose.yml` (e.g. `"5433:5432"`) and update `DATABASE_URL` in your `.env`.
- **Docker not running or permission errors**:
  Ensure Docker Desktop is running before executing `make up`. On Linux, ensure your user belongs to the `docker` group (`sudo usermod -aG docker $USER`).
- **Pre-commit download errors / Pip network timeouts**:
  On Windows systems where IPv6 connectivity is misconfigured, Python network libraries may attempt IPv6 first and time out when downloading hooks or packages. If this occurs, ensure `.venv/Lib/site-packages/sitecustomize.py` forces IPv4 resolution via `socket.AF_INET`.
- **OneDrive file sync warning**:
  Developing inside a cloud-synced OneDrive directory may cause file locks or race conditions during rapid file creation, `.venv` writes, or git operations. If file locks or latency occur, consider excluding `.venv` and `data/` from OneDrive sync or moving the repository directory outside the OneDrive sync path.

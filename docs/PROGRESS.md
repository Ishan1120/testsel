# Project Progress & Roadmap Tracking

> **How to update this file**:
> Update this document in every pull request that finishes or starts a task. Keep entries concise and factual. Tick finished checkboxes (`- [x]`), record a dated entry in the Log table, and update the "Current phase" and "Next up" sections accordingly.

- **Last updated**: 2026-11-22
- **Current phase**: Phase 0 (Setup) completed; transitioning to Phase 1 (Data pipeline)

---

## Phase Overview

| Phase | Name | Status | Planned Timeline |
| :---: | :--- | :---: | :--- |
| **0** | Setup & Foundation | **Done** | Month 1 |
| **1** | Data Pipeline | **In progress** | Month 1–2 |
| **2** | Baselines & Evaluation | **Not started** | Month 2 |
| **3** | ML Models | **Not started** | Month 3 |
| **4** | Backend Service | **Not started** | Month 4 |
| **5** | Frontend Dashboard | **Not started** | Month 5 |
| **6** | Production Hardening | **Not started** | Month 6 |
| **7** | Presentation & Showcase | **Not started** | Month 6–7 |

---

## Phase Checklists

### Phase 0: Setup & Foundation
- [x] Monorepo skeleton and standard folder layout
- [x] CI workflow (`.github/workflows/ci.yml`) with automated lint and test checks
- [x] Pre-commit hooks configuration (`.pre-commit-config.yaml`)
- [x] Docker Compose with PostgreSQL 16 container and health check
- [x] Migrated collector scaffold with 18 passing unit tests
- [x] ADR 0001 (Core Technology Stack Choices)
- [x] Developer documentation, architecture diagrams, and contribution guides
- [ ] Branch protection rules configured on `main` (require PR, CI green, 1 review)
- [ ] Issue labels and GitHub Project board setup
- [ ] Real GitHub usernames configured in `.github/CODEOWNERS`
- [ ] Teammate clones repo and verifies quickstart locally

### Phase 1: Data Pipeline
- [ ] First real collection on 2 to 3 target repos
- [ ] Verify `PostgresStore` against a live PostgreSQL 16 database
- [ ] Collect earlier run attempts to label flaky tests
- [ ] Support pull request runs from forks
- [ ] Grow collection to 20+ active repositories
- [ ] Dataset export pipeline (JSON / Parquet)
- [ ] Freeze dataset v1 with DVC

### Phase 2: Baselines & Evaluation
- [ ] Temporal split harness (train on past runs, evaluate on future commits)
- [ ] Implement ranking evaluation metrics (APFD, Recall@Top-K, First-Failure-to-Rank)
- [ ] Baseline models: Random ordering, Recent Failure Frequency heuristic, Changed File test mapping
- [ ] Automated benchmark evaluation reporting and comparison

### Phase 3: ML Models
- [ ] Feature extraction pipeline (code churn, test history, author signals, file distances)
- [ ] LightGBM ranking model implementation (LambdaRank / binary classification)
- [ ] Hyperparameter tuning and cross-validation
- [ ] MLflow experiment tracking and model registry integration
- [ ] Model artifact serialization and versioning

### Phase 4: Backend Service
- [ ] FastAPI service for GitHub App webhook events
- [ ] Asynchronous task worker queue (Redis / Celery or background tasks)
- [ ] Model serving component with low-latency inference (< 5s)
- [ ] GitHub Check Run integration to publish test ordering
- [ ] End-to-end integration tests for webhook-to-check-run pipeline

### Phase 5: Frontend Dashboard
- [ ] React + Vite + TypeScript dashboard skeleton (`web/`)
- [ ] PR test risk and ranking visualization view
- [ ] Historical CI time saved and flaky test analytics
- [ ] API integration between frontend dashboard and FastAPI backend

### Phase 6: Production Hardening
- [ ] Kubernetes manifests (`infra/k8s/`) and ingress setup
- [ ] Prometheus metrics and Grafana monitoring dashboard (`infra/monitoring/`)
- [ ] Database backup and migration management (Alembic / dbmate)
- [ ] Security audit: rate limiting, token encryption, secret scanning

### Phase 7: Presentation & Showcase
- [ ] End-to-end demo recorded and documentation polish
- [ ] Performance benchmarking report (time saved vs. test failure recall)
- [ ] Project showcase slide deck and presentation

---

## Next Up
- **Person A**: Run first live CI data collection against 2–3 target repos and verify `PostgresStore` live persistence.
- **Person B**: Configure GitHub repository settings (branch protection, issue labels) and verify Docker Compose environment with teammate.

---

## Blocked or Needs a Decision
*(None currently)*

---

## Log

| Date | Change |
| :--- | :--- |
| 2026-11-22 | Phase 0 skeleton pushed, CI green |

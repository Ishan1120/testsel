# ADR 0001: Technology Stack Choices for Testsel

## Status
Accepted

## Context
Testsel is a monorepo that predicts test failure risk on pull requests to enable predictive test selection in CI pipelines. The platform requires both an offline data ingestion and ML training loop, and a low-latency real-time online inference service integrated via GitHub webhooks and check runs. Two developers are collaborating on the repository across distinct development phases. We need explicit, decoupled, and industry-standard technology choices for core components.

## Decision
We select the following core stack components:

- **Python 3.12**: Modern standard typing, superior runtime performance, and broad support across data science and production serving ecosystems.
- **PostgreSQL 16**: Proven ACID-compliant relational storage for workflow runs, test execution histories, commit metadata, and relational queries.
- **FastAPI**: Asynchronous, lightweight ASGI web framework providing native OpenAPI docs and fast response times for incoming GitHub webhooks.
- **LightGBM**: Fast, memory-efficient gradient boosting library well-suited for tabular code-change and test-history failure prediction models.
- **MLflow**: Lightweight model tracking, experiment metric logging, and artifact registry without requiring heavy external SaaS dependencies.
- **DVC**: Git-friendly data and feature store versioning without bloating the primary Git repository with large Parquet extracts or model weights.
- **React**: Component-driven UI library for the developer web dashboard (`web/`) displaying test selection metrics and run audit logs.
- **Docker & Docker Compose**: Reproducible local developer environments and containerized CI/CD parity across Windows, macOS, and Linux.

## Consequences
- Team members need Docker and Python 3.12 installed locally.
- Development is structured to keep offline ML pipelines (data collection, feature extraction, training) modularized from online services (API, worker, serving).
- Inter-service contracts will be maintained under `src/testsel/shared/` to prevent schema drift.

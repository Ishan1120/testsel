# Testsel Architecture

## Overview
Testsel is a predictive test selection system consisting of two main operational loops:
1. **Online Serving Pipeline**: Ingests GitHub webhook events when pull requests update, enqueues ranking requests, runs inference to score test failure probability, and reports test selection decisions back to GitHub Check Runs.
2. **Offline Ingestion & Training Pipeline**: Continuously collects workflow runs, changed files, and JUnit XML test artifacts, builds time-split tabular datasets, trains ML ranking models, and registers model candidates for serving.

## System Flow Diagram

```mermaid
flowchart TD
    subgraph OnlineServing["Online Serving Pipeline (Phase 4)"]
        GH["GitHub Webhook Event"] -->|pull_request event| API["FastAPI Webhook Service (src/testsel/api)"]
        API -->|enqueue task| Q[("Job Queue / Redis")]
        Q -->|consume task| W["Worker Service (src/testsel/worker)"]
        W -->|fetch PR diff & context| SC["Shared Store / Context (src/testsel/shared)"]
        W -->|score test risk| INF["Inference Engine (src/testsel/serving)"]
        INF -->|rank test suite| W
        W -->|post check run status & test list| CR["GitHub Check Run / PR Status"]
    end

    subgraph OfflinePipeline["Offline Ingestion & Training Pipeline (Phases 1-3)"]
        GHA["GitHub Actions API"] -->|historical runs & JUnit artifacts| COL["Collector (src/testsel/collector)"]
        COL -->|store runs, files, results| DB[("PostgreSQL Database (db/schema.sql)")]
        DB -->|extract dataset| EVAL["Evaluation & Baselines (src/testsel/evaluation)"]
        DB -->|extract code & test changes| FEAT["Feature Engineering (src/testsel/features)"]
        FEAT -->|training dataset| TRN["Model Training Pipeline (src/testsel/training)"]
        TRN -->|log experiments & artifacts| REG[("MLflow Model Registry")]
        REG -.->|load production model| INF
    end
```

## Module Boundaries
- `src/testsel/collector/`: GitHub client, rate-limiting token pool, safe JUnit XML / zip extraction, and ingestion loop.
- `src/testsel/shared/`: Database connection management, domain models (`TestResult`, `ChangedFile`, `RunRecord`), and shared configuration.
- `src/testsel/features/`: Extraction of code metrics, commit features, and historical test failure rates.
- `src/testsel/evaluation/`: Time-split data splits, test selection baseline heuristics (e.g. Test-All, Random, File-match, Historical-fail), and ranking evaluation metrics (Recall@K, Saved CI time).
- `src/testsel/training/`: Offline training scripts, LightGBM rankers, and hyperparameter tuning.
- `src/testsel/serving/`: Model loading, inference ranking, and test filtering rules.
- `src/testsel/api/`: FastAPI webhook receivers and GitHub App verification.
- `src/testsel/worker/`: Async task queue workers executing scoring jobs.
- `web/`: React single-page application dashboard for audit metrics and savings visualization.

-- testsel schema. Applied automatically by docker-compose on first start,
-- or manually with: testsel init-db

CREATE TABLE IF NOT EXISTS repos (
    id          SERIAL PRIMARY KEY,
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (owner, name)
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id          SERIAL PRIMARY KEY,
    repo_id     INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    number      INTEGER NOT NULL,
    title       TEXT,
    author      TEXT,
    created_at  TIMESTAMPTZ,
    UNIQUE (repo_id, number)
);

-- One row per workflow run (latest attempt as reported by GitHub).
CREATE TABLE IF NOT EXISTS ci_runs (
    run_id        BIGINT PRIMARY KEY,           -- GitHub run id
    repo_id       INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    pr_id         INTEGER REFERENCES pull_requests(id) ON DELETE SET NULL,
    head_sha      TEXT NOT NULL,
    base_sha      TEXT,
    run_attempt   INTEGER NOT NULL DEFAULT 1,
    workflow_name TEXT,
    event         TEXT,
    conclusion    TEXT,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    collected_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ci_runs_repo_started ON ci_runs (repo_id, started_at);

-- Files changed at THIS run's head commit versus the PR base, so features
-- match what a model would have seen when that commit was pushed.
CREATE TABLE IF NOT EXISTS run_files (
    run_id     BIGINT NOT NULL REFERENCES ci_runs(run_id) ON DELETE CASCADE,
    filename   TEXT NOT NULL,
    status     TEXT,
    additions  INTEGER,
    deletions  INTEGER,
    patch      TEXT,
    PRIMARY KEY (run_id, filename)
);

-- Normalized test identity per repo: "<classname>::<name>".
CREATE TABLE IF NOT EXISTS tests (
    id        SERIAL PRIMARY KEY,
    repo_id   INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    test_id   TEXT NOT NULL,
    UNIQUE (repo_id, test_id)
);

CREATE TABLE IF NOT EXISTS test_results (
    run_id      BIGINT NOT NULL REFERENCES ci_runs(run_id) ON DELETE CASCADE,
    test_pk     INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    outcome     TEXT NOT NULL CHECK (outcome IN ('pass', 'fail', 'error', 'skip')),
    duration_s  DOUBLE PRECISION,
    error_type  TEXT,
    PRIMARY KEY (run_id, test_pk)
);
CREATE INDEX IF NOT EXISTS test_results_test ON test_results (test_pk);

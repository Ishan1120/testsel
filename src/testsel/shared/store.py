"""Storage layer: a small interface, a Postgres implementation, and an in-memory
implementation used by tests so the collector can be verified without a database."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from testsel.shared.models import ChangedFile, RunRecord, TestResult

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "db" / "schema.sql"


class Store(Protocol):
    def upsert_repo(self, owner: str, name: str) -> int: ...

    def upsert_pr(
        self,
        repo_id: int,
        number: int,
        title: str | None,
        author: str | None,
        created_at: str | None,
    ) -> int: ...

    def has_run(self, run_id: int) -> bool: ...

    def save_run(
        self,
        repo_id: int,
        pr_id: int | None,
        run: RunRecord,
        files: Sequence[ChangedFile],
        results: Sequence[TestResult],
    ) -> None: ...


class PostgresStore:
    """Requires psycopg 3 (declared in pyproject)."""

    def __init__(self, database_url: str):
        import psycopg  # imported lazily so tests do not need it

        self._conn = psycopg.connect(database_url)

    def close(self) -> None:
        self._conn.close()

    def init_schema(self, schema_path: Path = SCHEMA_PATH) -> None:
        with self._conn.transaction():
            self._conn.execute(schema_path.read_text())

    def upsert_repo(self, owner: str, name: str) -> int:
        with self._conn.transaction():
            row = self._conn.execute(
                """INSERT INTO repos (owner, name) VALUES (%s, %s)
                   ON CONFLICT (owner, name) DO UPDATE SET owner = EXCLUDED.owner
                   RETURNING id""",
                (owner, name),
            ).fetchone()
        return row[0]

    def upsert_pr(self, repo_id, number, title, author, created_at) -> int:
        with self._conn.transaction():
            row = self._conn.execute(
                """INSERT INTO pull_requests (repo_id, number, title, author, created_at)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (repo_id, number) DO UPDATE
                     SET title = EXCLUDED.title, author = EXCLUDED.author
                   RETURNING id""",
                (repo_id, number, title, author, created_at),
            ).fetchone()
        return row[0]

    def has_run(self, run_id: int) -> bool:
        row = self._conn.execute("SELECT 1 FROM ci_runs WHERE run_id = %s", (run_id,)).fetchone()
        return row is not None

    def save_run(self, repo_id, pr_id, run, files, results) -> None:
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO ci_runs (run_id, repo_id, pr_id, head_sha, base_sha, run_attempt,
                       workflow_name, event, conclusion, started_at, completed_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (run_id) DO NOTHING""",
                (
                    run.run_id,
                    repo_id,
                    pr_id,
                    run.head_sha,
                    run.base_sha,
                    run.run_attempt,
                    run.workflow_name,
                    run.event,
                    run.conclusion,
                    run.started_at,
                    run.completed_at,
                ),
            )
            if files:
                cur.executemany(
                    """INSERT INTO run_files (run_id, filename, status, additions, deletions, patch)
                       VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    [
                        (
                            run.run_id,
                            f.filename,
                            f.status,
                            f.additions,
                            f.deletions,
                            f.patch,
                        )
                        for f in files
                    ],
                )
            for r in results:
                cur.execute(
                    """INSERT INTO tests (repo_id, test_id) VALUES (%s, %s)
                       ON CONFLICT (repo_id, test_id) DO UPDATE SET test_id = EXCLUDED.test_id
                       RETURNING id""",
                    (repo_id, r.test_id),
                )
                test_pk = cur.fetchone()[0]
                cur.execute(
                    """INSERT INTO test_results (run_id, test_pk, outcome, duration_s, error_type)
                       VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    (run.run_id, test_pk, r.outcome, r.duration_s, r.error_type),
                )


class InMemoryStore:
    """Same behaviour as PostgresStore, for tests and quick experiments."""

    def __init__(self) -> None:
        self.repos: dict[tuple[str, str], int] = {}
        self.prs: dict[tuple[int, int], dict] = {}
        self.runs: dict[int, dict] = {}
        self.run_files: dict[int, list[ChangedFile]] = {}
        self.results: dict[int, list[TestResult]] = {}

    def upsert_repo(self, owner: str, name: str) -> int:
        return self.repos.setdefault((owner, name), len(self.repos) + 1)

    def upsert_pr(self, repo_id, number, title, author, created_at) -> int:
        key = (repo_id, number)
        if key not in self.prs:
            self.prs[key] = {"id": len(self.prs) + 1}
        self.prs[key].update(title=title, author=author, created_at=created_at)
        return self.prs[key]["id"]

    def has_run(self, run_id: int) -> bool:
        return run_id in self.runs

    def save_run(self, repo_id, pr_id, run, files, results) -> None:
        if run.run_id in self.runs:
            return
        self.runs[run.run_id] = {"repo_id": repo_id, "pr_id": pr_id, "run": run}
        self.run_files[run.run_id] = list(files)
        self.results[run.run_id] = list(results)

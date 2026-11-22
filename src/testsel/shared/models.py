from __future__ import annotations

from dataclasses import dataclass

OUTCOMES = ("pass", "fail", "error", "skip")


@dataclass(frozen=True)
class TestResult:
    __test__ = False  # stop pytest trying to collect this class

    test_id: str
    outcome: str  # one of OUTCOMES
    duration_s: float | None = None
    error_type: str | None = None


@dataclass(frozen=True)
class ChangedFile:
    filename: str
    status: str | None = None
    additions: int | None = None
    deletions: int | None = None
    patch: str | None = None


@dataclass(frozen=True)
class RunRecord:
    run_id: int
    head_sha: str
    base_sha: str | None
    run_attempt: int
    workflow_name: str | None
    event: str | None
    conclusion: str | None
    started_at: str | None
    completed_at: str | None

"""Collect (PR, run, changed files, test results) tuples for one repository."""

from __future__ import annotations

import logging
import re
import zipfile
from collections import Counter
from collections.abc import Iterator
from typing import Protocol

from testsel.collector.junit import UnsafeArchiveError, extract_results_from_zip
from testsel.shared.models import ChangedFile, RunRecord
from testsel.shared.store import Store

log = logging.getLogger(__name__)

DEFAULT_ARTIFACT_PATTERN = r"(junit|test[-_ ]?results?|pytest|test[-_ ]?report|surefire)"
COLLECTED_CONCLUSIONS = {"success", "failure"}
MAX_PATCH_CHARS = 50_000


class GitHubSource(Protocol):
    def iter_workflow_runs(self, owner: str, repo: str, since: str) -> Iterator[dict]: ...
    def list_artifacts(self, owner: str, repo: str, run_id: int) -> list[dict]: ...
    def download_artifact(self, owner: str, repo: str, artifact_id: int) -> bytes | None: ...
    def get_pull(self, owner: str, repo: str, number: int) -> dict | None: ...
    def iter_compare_files(self, owner: str, repo: str, base: str, head: str) -> Iterator[dict]: ...


def collect_repo(
    gh: GitHubSource,
    store: Store,
    owner: str,
    repo: str,
    since: str,
    max_runs: int = 500,
    artifact_pattern: str = DEFAULT_ARTIFACT_PATTERN,
) -> Counter:
    """Idempotent: runs already stored are skipped, so you can re-run it daily."""
    stats: Counter = Counter()
    pattern = re.compile(artifact_pattern, re.IGNORECASE)
    repo_id = store.upsert_repo(owner, repo)
    pr_cache: dict[int, int | None] = {}

    for run in gh.iter_workflow_runs(owner, repo, since):
        if stats["seen"] >= max_runs:
            break
        stats["seen"] += 1
        run_id = run["id"]

        if run.get("conclusion") not in COLLECTED_CONCLUSIONS:
            stats["skipped_conclusion"] += 1
            continue
        if store.has_run(run_id):
            stats["already_have"] += 1
            continue

        prs = run.get("pull_requests") or []
        if not prs:  # fork PRs are not linked by GitHub; skipped in v1
            stats["skipped_no_pr"] += 1
            continue
        pr_ref = prs[0]
        number = pr_ref["number"]
        base_sha = (pr_ref.get("base") or {}).get("sha")
        head_sha = run["head_sha"]

        results = _results_for_run(gh, owner, repo, run_id, pattern, stats)
        if results is None:
            stats["skipped_no_results"] += 1
            continue

        pr_id = _ensure_pr(gh, store, owner, repo, repo_id, number, pr_cache)
        files = _changed_files(gh, owner, repo, base_sha, head_sha)

        record = RunRecord(
            run_id=run_id,
            head_sha=head_sha,
            base_sha=base_sha,
            run_attempt=run.get("run_attempt") or 1,
            workflow_name=run.get("name"),
            event=run.get("event"),
            conclusion=run.get("conclusion"),
            started_at=run.get("run_started_at") or run.get("created_at"),
            completed_at=run.get("updated_at"),
        )
        store.save_run(repo_id, pr_id, record, files, results)
        stats["saved_runs"] += 1
        stats["saved_results"] += len(results)

    log.info("%s/%s: %s", owner, repo, dict(stats))
    return stats


def _results_for_run(gh, owner, repo, run_id, pattern, stats):
    """Return parsed results, or None when the run has no usable test report."""
    artifacts = [
        a
        for a in gh.list_artifacts(owner, repo, run_id)
        if pattern.search(a["name"]) and not a.get("expired")
    ]
    if not artifacts:
        return None
    merged = {}
    for art in artifacts:
        blob = gh.download_artifact(owner, repo, art["id"])
        if blob is None:
            stats["artifact_unavailable"] += 1
            continue
        try:
            for r in extract_results_from_zip(blob):
                merged[r.test_id] = r
        except (UnsafeArchiveError, zipfile.BadZipFile) as exc:
            log.warning("run %s artifact %s rejected: %s", run_id, art["id"], exc)
            stats["artifact_rejected"] += 1
    return list(merged.values()) or None


def _ensure_pr(gh, store, owner, repo, repo_id, number, cache) -> int | None:
    if number in cache:
        return cache[number]
    pull = gh.get_pull(owner, repo, number)
    if pull is None:
        cache[number] = None
    else:
        cache[number] = store.upsert_pr(
            repo_id,
            number,
            pull.get("title"),
            (pull.get("user") or {}).get("login"),
            pull.get("created_at"),
        )
    return cache[number]


def _changed_files(gh, owner, repo, base_sha, head_sha) -> list[ChangedFile]:
    if not base_sha:
        return []
    out = []
    for f in gh.iter_compare_files(owner, repo, base_sha, head_sha):
        patch = f.get("patch")
        out.append(
            ChangedFile(
                filename=f["filename"],
                status=f.get("status"),
                additions=f.get("additions"),
                deletions=f.get("deletions"),
                patch=patch[:MAX_PATCH_CHARS] if patch else None,
            )
        )
    return out

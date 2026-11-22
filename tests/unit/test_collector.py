import io
import zipfile

from testsel.collector.collector import collect_repo
from testsel.shared.store import InMemoryStore

REPORT = b"""<testsuite>
<testcase classname="t.a" name="test_ok" time="0.1"/>
<testcase classname="t.a" name="test_bad" time="0.2"><failure type="AssertionError"/></testcase>
</testsuite>"""


def zip_of(xml: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("junit.xml", xml)
    return buf.getvalue()


def run_dict(run_id, **over):
    base = {
        "id": run_id,
        "head_sha": f"head{run_id}",
        "name": "CI",
        "event": "pull_request",
        "conclusion": "failure",
        "run_attempt": 1,
        "run_started_at": "2026-01-02T00:00:00Z",
        "updated_at": "2026-01-02T00:10:00Z",
        "pull_requests": [{"number": 7, "base": {"sha": "basesha"}}],
    }
    base.update(over)
    return base


class FakeGitHub:
    def __init__(self):
        self.runs = [
            run_dict(1),
            run_dict(2, conclusion="cancelled"),
            run_dict(3, pull_requests=[]),  # fork PR
            run_dict(4),  # no artifact
            run_dict(5, conclusion="success"),
        ]
        self.artifacts = {
            1: [{"id": 11, "name": "pytest-junit", "expired": False}],
            4: [{"id": 41, "name": "coverage-html", "expired": False}],
            5: [
                {"id": 51, "name": "test-results", "expired": False},
                {"id": 52, "name": "test-results-old", "expired": False},
            ],
        }
        self.blobs = {11: zip_of(REPORT), 51: zip_of(REPORT), 52: None}
        self.calls = {"download": 0, "compare": 0}

    def iter_workflow_runs(self, owner, repo, since):
        yield from self.runs

    def list_artifacts(self, owner, repo, run_id):
        return self.artifacts.get(run_id, [])

    def download_artifact(self, owner, repo, artifact_id):
        self.calls["download"] += 1
        return self.blobs[artifact_id]

    def get_pull(self, owner, repo, number):
        return {
            "title": "Fix bug",
            "user": {"login": "alice"},
            "created_at": "2026-01-01T00:00:00Z",
        }

    def iter_compare_files(self, owner, repo, base, head):
        self.calls["compare"] += 1
        yield {
            "filename": "src/app.py",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "patch": "@@ -1 +1 @@",
        }


def test_collect_saves_only_usable_runs():
    gh, store = FakeGitHub(), InMemoryStore()
    stats = collect_repo(gh, store, "o", "r", "2026-01-01")

    assert set(store.runs) == {1, 5}
    assert stats["saved_runs"] == 2
    assert stats["skipped_conclusion"] == 1
    assert stats["skipped_no_pr"] == 1
    assert stats["skipped_no_results"] == 1
    assert stats["artifact_unavailable"] == 1  # test-results-old returned None

    outcomes = {r.test_id: r.outcome for r in store.results[1]}
    assert outcomes == {"t.a::test_ok": "pass", "t.a::test_bad": "fail"}
    assert store.run_files[1][0].filename == "src/app.py"
    assert store.runs[1]["run"].base_sha == "basesha"
    assert len(store.prs) == 1  # PR 7 fetched once and shared by both runs


def test_collect_is_idempotent():
    gh, store = FakeGitHub(), InMemoryStore()
    collect_repo(gh, store, "o", "r", "2026-01-01")
    downloads_after_first = gh.calls["download"]
    stats = collect_repo(gh, store, "o", "r", "2026-01-01")

    assert stats["saved_runs"] == 0
    assert stats["already_have"] == 2
    assert len(store.runs) == 2
    assert gh.calls["download"] == downloads_after_first  # stored runs are never re-downloaded


def test_max_runs_limits_work():
    gh, store = FakeGitHub(), InMemoryStore()
    stats = collect_repo(gh, store, "o", "r", "2026-01-01", max_runs=1)
    assert stats["seen"] == 1
    assert set(store.runs) == {1}


def test_corrupt_artifact_is_rejected_not_fatal():
    gh, store = FakeGitHub(), InMemoryStore()
    gh.blobs[11] = b"this is not a zip"
    stats = collect_repo(gh, store, "o", "r", "2026-01-01")
    assert stats["artifact_rejected"] == 1
    assert 1 not in store.runs and 5 in store.runs

import json

import pytest

from testsel.collector.github_client import GitHubClient, GitHubError, NotFound


class FakeResp:
    def __init__(self, status=200, body=None, headers=None, links=None, text=""):
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.links = links or {}
        self.text = text or json.dumps(body)

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get(self, url, params=None, headers=None, stream=False, timeout=None):
        self.requests.append({"url": url, "params": params, "headers": headers})
        return self.responses.pop(0)


def client(tmp_path, responses, tokens=("tok1",)):
    sleeps = []
    c = GitHubClient(list(tokens), tmp_path, FakeSession(responses), sleep=sleeps.append)
    return c, sleeps


def test_etag_cache_revalidates_with_304(tmp_path):
    c, _ = client(
        tmp_path,
        [
            FakeResp(200, {"a": 1}, {"ETag": 'W/"x"', "X-RateLimit-Remaining": "50"}),
            FakeResp(304, None, {"X-RateLimit-Remaining": "50"}),
        ],
    )
    assert c.get_json("/repos/o/r/pulls/1")[0] == {"a": 1}
    assert c.get_json("/repos/o/r/pulls/1")[0] == {"a": 1}  # served from cache
    assert c._session.requests[1]["headers"]["If-None-Match"] == 'W/"x"'


def test_pagination_follows_next_link(tmp_path):
    c, _ = client(
        tmp_path,
        [
            FakeResp(
                200,
                {"workflow_runs": [{"id": 1}]},
                links={"next": {"url": "https://api.github.com/page2"}},
            ),
            FakeResp(200, {"workflow_runs": [{"id": 2}]}),
        ],
    )
    runs = list(c.paginate("/repos/o/r/actions/runs", key="workflow_runs"))
    assert [r["id"] for r in runs] == [1, 2]


def test_rate_limit_rotates_to_second_token(tmp_path):
    c, sleeps = client(
        tmp_path,
        [
            FakeResp(403, {"message": "API rate limit exceeded"}, {"X-RateLimit-Remaining": "0"}),
            FakeResp(200, {"ok": True}, {"X-RateLimit-Remaining": "4999"}),
        ],
        tokens=("tok1", "tok2"),
    )
    assert c.get_json("/x")[0] == {"ok": True}
    auth = [r["headers"]["Authorization"] for r in c._session.requests]
    assert auth[0] != auth[1]  # switched token, no sleeping needed
    assert sleeps == []


def test_5xx_retries_with_backoff(tmp_path):
    c, sleeps = client(tmp_path, [FakeResp(502, text="bad gateway"), FakeResp(200, {"ok": 1})])
    assert c.get_json("/x")[0] == {"ok": 1}
    assert sleeps == [2.0]


def test_404_raises_not_found(tmp_path):
    c, _ = client(tmp_path, [FakeResp(404, {"message": "Not Found"})])
    with pytest.raises(NotFound):
        c.get_json("/x")


def test_other_errors_raise(tmp_path):
    c, _ = client(tmp_path, [FakeResp(422, {"message": "bad"})])
    with pytest.raises(GitHubError):
        c.get_json("/x")


def test_requires_a_token(tmp_path):
    with pytest.raises(ValueError):
        GitHubClient([], tmp_path)

"""Thin GitHub REST client built for bulk collection.

Features: token pool with rotation, primary rate-limit waiting, retry with
exponential backoff on 5xx / secondary limits, and an on-disk ETag cache so
re-running the collector costs almost no rate limit (304 responses are free).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import requests

log = logging.getLogger(__name__)

API = "https://api.github.com"
MAX_ARTIFACT_BYTES = 100 * 1024 * 1024


class GitHubError(RuntimeError):
    pass


class NotFound(GitHubError):
    pass


class Gone(GitHubError):
    """Resource expired (artifacts and logs are deleted after the retention window)."""


class _Token:
    def __init__(self, value: str):
        self.value = value
        self.remaining: int | None = None
        self.reset_at: float = 0.0


class GitHubClient:
    def __init__(
        self,
        tokens: list[str] | tuple[str, ...],
        cache_dir: Path,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 5,
    ):
        if not tokens:
            raise ValueError("at least one GitHub token is required (set GITHUB_TOKENS)")
        self._tokens = [_Token(t) for t in tokens]
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = session or requests.Session()
        self._sleep = sleep
        self._max_retries = max_retries

    # ---- token pool -------------------------------------------------------
    def _pick_token(self) -> _Token:
        now = time.time()
        usable = [
            t for t in self._tokens if t.remaining is None or t.remaining > 0 or t.reset_at <= now
        ]
        if usable:
            return max(usable, key=lambda t: t.remaining if t.remaining is not None else 10**9)
        soonest = min(self._tokens, key=lambda t: t.reset_at)
        wait = max(soonest.reset_at - now, 0) + 1
        log.warning("all tokens rate limited; sleeping %.0fs", wait)
        self._sleep(wait)
        soonest.remaining = None
        return soonest

    @staticmethod
    def _update_limits(tok: _Token, resp: requests.Response) -> None:
        rem = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")
        if rem is not None:
            tok.remaining = int(rem)
        if reset is not None:
            tok.reset_at = float(reset)

    # ---- core request -----------------------------------------------------
    def _request(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        stream: bool = False,
    ) -> requests.Response:
        backoff = 2.0
        for attempt in range(self._max_retries + 1):
            tok = self._pick_token()
            h = {
                "Authorization": f"Bearer {tok.value}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                **(headers or {}),
            }
            try:
                resp = self._session.get(url, params=params, headers=h, stream=stream, timeout=60)
            except requests.RequestException as exc:
                if attempt == self._max_retries:
                    raise GitHubError(f"network error for {url}: {exc}") from exc
                self._sleep(backoff)
                backoff *= 2
                continue
            self._update_limits(tok, resp)

            if resp.status_code in (200, 304):
                return resp
            if resp.status_code == 404:
                raise NotFound(url)
            if resp.status_code == 410:
                raise Gone(url)
            limited = resp.status_code in (403, 429) and (
                tok.remaining == 0
                or "retry-after" in resp.headers
                or "rate limit" in resp.text.lower()
            )
            if limited:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    self._sleep(float(retry_after) + 1)
                else:
                    tok.remaining = 0  # _pick_token will rotate or wait for reset
                continue
            if resp.status_code >= 500 and attempt < self._max_retries:
                self._sleep(backoff)
                backoff *= 2
                continue
            raise GitHubError(f"{resp.status_code} for {url}: {resp.text[:200]}")
        raise GitHubError(f"retries exhausted for {url}")

    # ---- cached JSON GET --------------------------------------------------
    def _cache_path(self, url: str, params: dict | None) -> Path:
        key = hashlib.sha256((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
        return self._cache_dir / key[:2] / f"{key}.json"

    def get_json(self, path: str, params: dict | None = None) -> tuple[object, str | None]:
        """Return (decoded body, next-page URL or None). Uses ETag revalidation."""
        url = path if path.startswith("http") else f"{API}{path}"
        cache_file = self._cache_path(url, params)
        headers = {}
        cached = None
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
        resp = self._request(url, params, headers)
        if resp.status_code == 304 and cached is not None:
            return cached["body"], cached.get("next")
        body = resp.json()
        nxt = resp.links.get("next", {}).get("url")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"etag": resp.headers.get("ETag"), "body": body, "next": nxt})
        )
        return body, nxt

    def paginate(self, path: str, params: dict | None = None, key: str | None = None) -> Iterator:
        params = {"per_page": 100, **(params or {})}
        url: str | None = path
        first = True
        while url:
            body, nxt = self.get_json(url, params if first else None)
            first = False
            items = body[key] if key else body
            yield from items
            url = nxt

    # ---- domain methods used by the collector -----------------------------
    def iter_workflow_runs(self, owner: str, repo: str, since: str) -> Iterator[dict]:
        params = {"event": "pull_request", "status": "completed", "created": f">={since}"}
        yield from self.paginate(f"/repos/{owner}/{repo}/actions/runs", params, key="workflow_runs")

    def list_artifacts(self, owner: str, repo: str, run_id: int) -> list[dict]:
        body, _ = self.get_json(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts", {"per_page": 100}
        )
        return body["artifacts"]

    def download_artifact(self, owner: str, repo: str, artifact_id: int) -> bytes | None:
        """Download an artifact zip; returns None if it expired or is too large."""
        url = f"{API}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
        try:
            resp = self._request(url, stream=True)
        except (Gone, NotFound):
            return None
        size = int(resp.headers.get("Content-Length") or 0)
        if size > MAX_ARTIFACT_BYTES:
            resp.close()
            return None
        buf = bytearray()
        for chunk in resp.iter_content(1 << 16):
            buf.extend(chunk)
            if len(buf) > MAX_ARTIFACT_BYTES:
                resp.close()
                return None
        return bytes(buf)

    def get_pull(self, owner: str, repo: str, number: int) -> dict | None:
        try:
            body, _ = self.get_json(f"/repos/{owner}/{repo}/pulls/{number}")
        except NotFound:
            return None
        return body  # type: ignore[return-value]

    def iter_compare_files(self, owner: str, repo: str, base: str, head: str) -> Iterator[dict]:
        """Files changed between base and head, i.e. what a model sees for this commit."""
        page = 1
        while True:
            try:
                body, _ = self.get_json(
                    f"/repos/{owner}/{repo}/compare/{base}...{head}",
                    {"per_page": 100, "page": page},
                )
            except NotFound:  # force-pushed away or garbage collected
                return
            files = body.get("files", [])  # type: ignore[union-attr]
            yield from files
            if len(files) < 100:
                return
            page += 1

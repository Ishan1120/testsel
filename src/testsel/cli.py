from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from testsel.collector.collector import DEFAULT_ARTIFACT_PATTERN, collect_repo
from testsel.collector.github_client import GitHubClient
from testsel.shared.config import Settings
from testsel.shared.store import PostgresStore


def _split_repo(full_name: str) -> tuple[str, str]:
    owner, _, name = full_name.partition("/")
    if not owner or not name:
        raise SystemExit(f"repo must look like owner/name, got {full_name!r}")
    return owner, name


def _cmd_init_db(args, settings: Settings) -> int:
    store = PostgresStore(settings.database_url)
    store.init_schema(Path(args.schema))
    print("schema applied")
    return 0


def _cmd_collect(args, settings: Settings) -> int:
    owner, name = _split_repo(args.repo)
    gh = GitHubClient(settings.github_tokens, settings.data_dir / "cache")
    store = PostgresStore(settings.database_url)
    stats = collect_repo(gh, store, owner, name, args.since, args.max_runs, args.artifact_pattern)
    print(dict(stats))
    return 0


def _cmd_collect_all(args, settings: Settings) -> int:
    cfg = yaml.safe_load(Path(args.config).read_text())
    defaults = cfg.get("defaults", {})
    gh = GitHubClient(settings.github_tokens, settings.data_dir / "cache")
    store = PostgresStore(settings.database_url)
    for entry in cfg["repos"]:
        owner, name = _split_repo(entry["name"])
        merged = {**defaults, **entry}
        collect_repo(
            gh,
            store,
            owner,
            name,
            since=merged["since"],
            max_runs=merged.get("max_runs", 500),
            artifact_pattern=merged.get("artifact_pattern", DEFAULT_ARTIFACT_PATTERN),
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="testsel")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="apply db/schema.sql")
    p.add_argument("--schema", default="db/schema.sql")
    p.set_defaults(func=_cmd_init_db)

    p = sub.add_parser("collect", help="collect one repository")
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--since", required=True, help="YYYY-MM-DD")
    p.add_argument("--max-runs", type=int, default=200)
    p.add_argument("--artifact-pattern", default=DEFAULT_ARTIFACT_PATTERN)
    p.set_defaults(func=_cmd_collect)

    p = sub.add_parser("collect-all", help="collect every repo in a YAML config")
    p.add_argument("--config", default="configs/repos.yaml")
    p.set_defaults(func=_cmd_collect_all)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return args.func(args, Settings.from_env())


if __name__ == "__main__":
    sys.exit(main())

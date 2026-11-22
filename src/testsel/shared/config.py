from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    github_tokens: tuple[str, ...]
    data_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        tokens = tuple(
            t.strip() for t in os.environ.get("GITHUB_TOKENS", "").split(",") if t.strip()
        )
        return cls(
            database_url=os.environ.get(
                "DATABASE_URL", "postgresql://testsel:testsel@localhost:5432/testsel"
            ),
            github_tokens=tokens,
            data_dir=Path(os.environ.get("DATA_DIR", "data")),
        )

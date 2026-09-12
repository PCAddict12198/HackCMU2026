"""Paths + environment. OWNER: engine (P2)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(os.environ.get("TASTESPACE_ROOT") or Path(__file__).resolve().parents[2])
load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(REPO_ROOT / ".env.local", override=False)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    build_dir: Path
    data_tier: str
    xai_api_key: str | None
    grok_model: str | None
    # "low" halves Ask latency on grok-4.6 (9.5 s -> 4.7 s) with the same tool choices;
    # GROK_REASONING_EFFORT=default sends no setting. grok-4.6 rejects "none".
    grok_reasoning_effort: str | None = "low"

    @property
    def artifact_path(self) -> Path:
        return self.build_dir / "tastespace.json"

    @property
    def report_path(self) -> Path:
        return self.build_dir / "report.md"

    @property
    def grok_configured(self) -> bool:
        return bool(self.xai_api_key and self.grok_model)


def get_settings() -> Settings:
    return Settings(
        data_dir=Path(os.environ.get("TASTESPACE_DATA_DIR") or REPO_ROOT / "data"),
        build_dir=Path(os.environ.get("TASTESPACE_BUILD_DIR") or REPO_ROOT / "build"),
        data_tier=os.environ.get("DATA_TIER") or "core",
        xai_api_key=os.environ.get("XAI_API_KEY") or None,
        grok_model=os.environ.get("GROK_MODEL") or None,
        grok_reasoning_effort=_effort(os.environ.get("GROK_REASONING_EFFORT")),
    )


def _effort(value: str | None) -> str | None:
    if not value:
        return "low"
    return None if value.strip().lower() == "default" else value.strip().lower()

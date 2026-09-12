"""Engine tests use ONLY backend/tests/fixtures/data (never data/), so they pass no matter how far P1's
real dataset has progressed. OWNER: engine (P2)."""

from pathlib import Path

import pytest
from tastespace.api import Runtime
from tastespace.build import build_state
from tastespace.config import Settings
from tastespace_contracts.validate import load_dataset

FIXTURE_DATA = Path(__file__).parent / "fixtures" / "data"


@pytest.fixture(scope="session")
def fx_dataset():
    return load_dataset(FIXTURE_DATA, "core")


@pytest.fixture(scope="session")
def fx_state(fx_dataset):
    return build_state(fx_dataset)


@pytest.fixture
def fx_settings(tmp_path) -> Settings:
    return Settings(data_dir=FIXTURE_DATA, build_dir=tmp_path, data_tier="core", xai_api_key=None, grok_model=None)


@pytest.fixture
def fx_runtime(fx_settings, fx_state) -> Runtime:
    fx_state.save(fx_settings.artifact_path)
    return Runtime(fx_settings)

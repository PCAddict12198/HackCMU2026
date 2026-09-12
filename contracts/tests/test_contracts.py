"""Contract self-checks + canonical fixture validation. OWNER: integrator.

Every file in contracts/fixtures/api/ must validate against its pydantic model: this is the real
guarantee that P3's mock mode and P2's API agree (TS JSON imports widen literals, so tsc can't)."""

import json
import typing
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError
from tastespace_contracts import CONTRACT_VERSION
from tastespace_contracts.api_models import (
    AskResponse,
    ExplainResponse,
    HealthResponse,
    RecipeResponse,
    ShiftResponse,
    SpaceResponse,
    TwinsResponse,
)
from tastespace_contracts.errors import ERROR_STATUS, ErrorCode, ErrorResponse
from tastespace_contracts.taxonomy import (
    CUISINE_IDS,
    CUISINE_REGION,
    DIM_GROUP,
    DIM_IDS,
    REGION_MACRO,
    cuisine_distance,
)
from tastespace_contracts.ui_actions import UiAction

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "contracts" / "fixtures" / "api"
FIXTURE_MODELS = {
    "health.json": HealthResponse,
    "space.json": SpaceResponse,
    "space_large.json": SpaceResponse,
    "twins.json": TwinsResponse,
    "shift.json": ShiftResponse,
    "explain.json": ExplainResponse,
    "recipe.json": RecipeResponse,
    "ask.json": AskResponse,
}


def test_version_files_agree():
    assert (ROOT / "contracts" / "VERSION").read_text().strip() == CONTRACT_VERSION


def test_taxonomy_is_consistent():
    assert set(DIM_GROUP) == set(DIM_IDS) and len(DIM_IDS) == 17
    assert set(CUISINE_REGION) == set(CUISINE_IDS)
    assert all(r in REGION_MACRO for r in CUISINE_REGION.values())
    assert cuisine_distance("japanese", "chinese") == 0.4 and cuisine_distance("thai", "indian") == 0.7
    assert cuisine_distance("japanese", "mexican") == 1.0 and set(ERROR_STATUS) == set(typing.get_args(ErrorCode))


@pytest.mark.parametrize("name,model", sorted(FIXTURE_MODELS.items()))
def test_api_fixture_validates(name, model):
    model.model_validate(json.loads((FIXTURES / name).read_text()))


def test_ask_fixture_exercises_every_ui_action():
    data = AskResponse.model_validate(json.loads((FIXTURES / "ask.json").read_text()))
    union = typing.get_args(typing.get_args(UiAction)[0])
    all_types = {typing.get_args(m.model_fields["type"].annotation)[0] for m in union}
    assert {a.type for a in data.ui_actions} == all_types


def test_errors_fixture_covers_every_code():
    data = json.loads((FIXTURES / "errors.json").read_text())
    assert set(data) == set(ERROR_STATUS)
    for code, body in data.items():
        assert ErrorResponse.model_validate(body).error.code == code


def test_ui_action_contract_examples():
    ta = TypeAdapter(UiAction)
    ta.validate_python({"type": "set_shift", "dish_id": "x", "deltas": {"rich": -0.8, "sour": 1.2}})
    with pytest.raises(ValidationError):
        ta.validate_python({"type": "set_shift", "dish_id": "x", "deltas": {"rich": -3}})
    with pytest.raises(ValidationError):
        ta.validate_python({"type": "open_panel", "panel": "settings"})

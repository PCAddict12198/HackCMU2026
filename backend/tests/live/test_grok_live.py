"""Opt-in LIVE smoke test against xAI. Never runs in CI or `make check`.

    GROK_LIVE=1 uv run pytest backend/tests/live -q

Uses the fixture space (6 dishes) and the real model from .env. Assertions are deliberately loose:
the model is non-deterministic, but tool use, grounding and the closed vocabulary must hold.
"""

import json
import os

import pytest
from tastespace.config import get_settings
from tastespace.grok.agent import run_ask
from tastespace.grok.client import xai_chat_factory
from tastespace.grok.ingredient_mapper import map_ingredients
from tastespace_contracts.api_models import AskRequest
from tastespace_contracts.ui_actions import referenced_dish_ids

pytestmark = pytest.mark.skipif(os.environ.get("GROK_LIVE") != "1", reason="live xAI test; set GROK_LIVE=1")


@pytest.fixture(scope="module")
def factory():
    settings = get_settings()
    if not settings.grok_configured:
        pytest.skip("XAI_API_KEY / GROK_MODEL not set")
    return xai_chat_factory(settings)


def ask(state, factory, text):
    return run_ask(state, AskRequest(messages=[{"role": "user", "content": text}]), factory)


def test_twin_question_uses_find_twins(fx_state, factory):
    res = ask(fx_state, factory, "What is the flavor twin of the noodle soup?")
    assert any(t.tool == "find_twins" and t.ok for t in res.tool_trace), res.tool_trace
    traced = json.dumps([t.model_dump() for t in res.tool_trace])
    for action in res.ui_actions:
        assert all(d in fx_state.dishes and d in traced for d in referenced_dish_ids(action))


def test_shift_question_moves_the_right_way(fx_state, factory):
    res = ask(fx_state, factory, "Something like the noodle soup but much more sour")
    shifts = [t for t in res.tool_trace if t.tool == "shift_taste" and t.ok]
    assert shifts, res.tool_trace
    changes = {c["dim"]: c["delta"] for c in shifts[0].args["changes"]}
    assert changes.get("sour", 0) > 0


def test_mapper_stays_in_the_closed_vocabulary(fx_dataset, factory):
    mapping = map_ingredients(["flaky sea salt", "caster sugar", "unobtainium"], fx_dataset.ingredients, factory)
    assert set(mapping.values()) <= set(fx_dataset.ingredients)
    assert mapping.get("flaky sea salt") == "salt" and "unobtainium" not in mapping

"""Provider failures must say WHY (e.g. a mistyped GROK_MODEL), not just the exception class."""

from types import SimpleNamespace

import pytest
from tastespace.errors import TasteSpaceError
from tastespace.grok.agent import run_ask
from tastespace.grok.errors import provider_error_message
from tastespace.grok.ingredient_mapper import map_ingredients
from tastespace_contracts.api_models import AskRequest


class FakeRpcError(Exception):
    """Shaped like grpc._channel._InactiveRpcError."""

    def code(self):
        return SimpleNamespace(name="INVALID_ARGUMENT")

    def details(self):
        return "Model not found: GROK_MODEL=grok-4.6"


class BrokenChat:
    def add_user(self, text):
        pass

    def add_assistant(self, text):
        pass

    def sample(self):
        raise FakeRpcError()

    def parse(self, shape):
        raise FakeRpcError()


def broken_factory(system_prompt, tools=None):
    return BrokenChat()


def test_grpc_details_are_surfaced():
    assert provider_error_message(FakeRpcError()) == "INVALID_ARGUMENT: Model not found: GROK_MODEL=grok-4.6"
    assert provider_error_message(ValueError("boom")) == "ValueError: boom"


def test_ask_failure_reports_the_reason(fx_state):
    with pytest.raises(TasteSpaceError) as exc:
        run_ask(fx_state, AskRequest(messages=[{"role": "user", "content": "hi"}]), broken_factory)
    assert exc.value.code == "grok_failed" and "Model not found" in exc.value.message
    assert "Model not found" in exc.value.details["reason"]


def test_mapper_failure_reports_the_reason(fx_dataset):
    with pytest.raises(TasteSpaceError) as exc:
        map_ingredients(["dragonfruit"], fx_dataset.ingredients, broken_factory)
    assert "Model not found" in exc.value.message

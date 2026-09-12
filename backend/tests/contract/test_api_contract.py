"""Engine -> Web boundary: every endpoint answers with its contract model or the contract error."""

import pytest
from fastapi.testclient import TestClient
from tastespace.api import Runtime, create_app
from tastespace_contracts.api_models import (
    AskResponse,
    ExplainResponse,
    HealthResponse,
    RecipeResponse,
    ShiftResponse,
    SpaceResponse,
    TwinsResponse,
)
from tastespace_contracts.errors import ErrorResponse

from ..fakes.fake_grok import fake_factory, text_turn


@pytest.fixture
def client(fx_runtime):
    return TestClient(create_app(runtime=fx_runtime))


def err(resp, status, code):
    assert resp.status_code == status, resp.text
    assert ErrorResponse.model_validate(resp.json()).error.code == code


def test_core_endpoints_validate(client):
    h = HealthResponse.model_validate(client.get("/api/health").json())
    assert h.build_ready and h.data_ready and not h.grok_configured
    SpaceResponse.model_validate(client.get("/api/space").json())
    TwinsResponse.model_validate(client.get("/api/twins", params={"dish": "fx_noodle_soup"}).json())
    ShiftResponse.model_validate(client.post("/api/shift", json={"dish_id": "fx_noodle_soup",
                                                                 "deltas": {"rich": -0.8, "sour": 1.2}}).json())
    ExplainResponse.model_validate(client.get("/api/explain", params={"a": "fx_noodle_soup", "b": "fx_spicy_soup"}).json())
    RecipeResponse.model_validate(client.post("/api/recipe", json={"text": "200 g noodles\n300 g broth"}).json())


def test_errors_use_the_contract_shape(client):
    err(client.get("/api/twins", params={"dish": "nope"}), 404, "not_found")
    err(client.post("/api/shift", json={"dish_id": "fx_noodle_soup", "deltas": {"salty_ish": 1}}), 422, "validation_error")
    err(client.post("/api/shift", json={"dish_id": "fx_noodle_soup", "deltas": {"sour": 9}}), 422, "validation_error")
    err(client.get("/api/twins"), 422, "validation_error")


def test_ask_without_grok_is_unavailable_but_core_still_works(client):
    err(client.post("/api/ask", json={"messages": [{"role": "user", "content": "hi"}]}), 503, "grok_unavailable")
    assert client.get("/api/space").status_code == 200


def test_ask_with_fake_grok(fx_runtime):
    c = TestClient(create_app(runtime=fx_runtime, chat_factory=fake_factory([text_turn("Hello from TasteSpace.")])))
    res = AskResponse.model_validate(c.post("/api/ask", json={"messages": [{"role": "user", "content": "hi"}]}).json())
    assert res.grounded and res.reply == "Hello from TasteSpace."


def test_missing_build_is_not_ready(fx_settings):
    c = TestClient(create_app(runtime=Runtime(fx_settings)))  # nothing saved in tmp build dir
    err(c.get("/api/space"), 503, "not_ready")
    assert HealthResponse.model_validate(c.get("/api/health").json()).build_ready is False

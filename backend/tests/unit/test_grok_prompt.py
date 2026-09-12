"""The Ask system prompt carries the dish catalog so Grok can skip a search round-trip (fakes only)."""

from tastespace.grok import agent
from tastespace.grok.agent import run_ask
from tastespace_contracts.api_models import AskRequest

from ..fakes.fake_grok import fake_factory, text_turn


def _prompt(state, monkeypatch=None) -> str:
    factory = fake_factory([text_turn("ok")])
    run_ask(state, AskRequest(messages=[{"role": "user", "content": "hi"}]), factory)
    return factory.chats[0].system_prompt


def test_prompt_lists_every_dish_id_and_ambiguity_rule(fx_state):
    prompt = _prompt(fx_state)
    assert all(did in prompt for did in fx_state.dishes)
    assert "search_dishes only if" in prompt and "which other one they can ask about" in prompt


def test_huge_spaces_fall_back_to_search(fx_state, monkeypatch):
    monkeypatch.setattr(agent, "MAX_CATALOG", 2)
    prompt = _prompt(fx_state)
    assert "use search_dishes" in prompt and "fx_noodle_soup" not in prompt

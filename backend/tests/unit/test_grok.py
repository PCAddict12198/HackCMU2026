"""Grok -> Engine boundary: only registered tools run, numbers are grounded, UI actions are valid."""

import json
import typing

import pytest
from pydantic import ValidationError
from tastespace.grok.agent import MAX_TOOL_ROUNDS, run_ask
from tastespace.grok.grounding import ungrounded_numbers
from tastespace.grok.ingredient_mapper import build_shape, map_ingredients
from tastespace.grok.tools import TOOLS, tool_specs
from tastespace_contracts.api_models import AskRequest
from tastespace_contracts.taxonomy import ToolName
from tastespace_contracts.ui_actions import referenced_dish_ids

from ..fakes.fake_grok import call, fake_factory, text_turn, tool_turn


def ask(text: str) -> AskRequest:
    return AskRequest(messages=[{"role": "user", "content": text}])


def test_tool_registry_matches_contract():
    assert set(TOOLS) == set(typing.get_args(ToolName))
    assert {s.name for s in tool_specs()} == set(TOOLS)


def test_grounded_twin_flow_produces_ui_actions(fx_state):
    factory = fake_factory([
        tool_turn(call("search_dishes", {"query": "noodle soup"})),
        tool_turn(call("find_twins", {"dish_id": "fx_noodle_soup"}, "c2")),
        text_turn("Its closest cross-cuisine twin is the spicy soup."),
    ])
    res = run_ask(fx_state, ask("what is the flavor twin of noodle soup?"), factory)
    assert res.grounded and [t.tool for t in res.tool_trace] == ["search_dishes", "find_twins"]
    types = [a.type for a in res.ui_actions]
    assert "show_twins" in types and types[-1] == "open_panel"
    traced = json.dumps([t.model_dump() for t in res.tool_trace])
    for a in res.ui_actions:
        for did in referenced_dish_ids(a):
            assert did in fx_state.dishes and did in traced


def test_fabricated_numbers_are_replaced_by_template(fx_state):
    factory = fake_factory([tool_turn(call("find_twins", {"dish_id": "fx_noodle_soup"})),
                            text_turn("It is 97.3% similar to spicy soup.")])
    res = run_ask(fx_state, ask("twin of noodle soup"), factory)
    assert not res.grounded and "Flavor twins for" in res.reply and "97.3" not in res.reply


def test_real_numbers_from_tools_are_allowed(fx_state):
    factory = fake_factory([tool_turn(call("find_twins", {"dish_id": "fx_noodle_soup", "k": 1}))])
    first = run_ask(fx_state, ask("twin"), factory)
    pct = first.tool_trace[0].result["twins"][0]["similarity_pct"]
    assert ungrounded_numbers(f"closer than {pct:.0f}% of pairs", first.tool_trace) == []


def test_unknown_tool_is_refused(fx_state):
    factory = fake_factory([tool_turn(call("drop_database", {})), text_turn("Sorry.")])
    res = run_ask(fx_state, ask("hi"), factory)
    assert res.tool_trace == []
    tool_msgs = [e for e in factory.chats[0].log if e[0] == "tool"]
    assert "unknown tool" in tool_msgs[0][2]


@pytest.mark.parametrize("args", [{"dish": "fx_noodle_soup"}, {"dish_id": "does_not_exist"}])
def test_bad_args_and_unknown_dishes_fail_softly(fx_state, args):
    factory = fake_factory([tool_turn(call("find_twins", args)), text_turn("Couldn't find it.")])
    res = run_ask(fx_state, ask("twin"), factory)
    assert res.tool_trace and not res.tool_trace[0].ok and res.tool_trace[0].error
    assert res.ui_actions == []


def test_tool_rounds_are_capped(fx_state):
    factory = fake_factory([tool_turn(call("search_dishes", {"query": "soup"}, f"c{i}"))
                            for i in range(MAX_TOOL_ROUNDS + 3)])
    res = run_ask(fx_state, ask("loop forever"), factory)
    assert len(res.tool_trace) == MAX_TOOL_ROUNDS and not res.grounded


def test_shift_tool_emits_set_shift(fx_state):
    factory = fake_factory([tool_turn(call("shift_taste", {"dish_id": "fx_noodle_soup",
                                                           "changes": [{"dim": "sour", "delta": 1.0}]})),
                            text_turn("Here is a more acidic direction.")])
    res = run_ask(fx_state, ask("noodle soup but more sour"), factory)
    set_shift = next(a for a in res.ui_actions if a.type == "set_shift")
    assert set_shift.deltas == {"sour": 1.0}


def test_ingredient_mapper_is_closed_vocabulary(fx_dataset):
    shape = build_shape(list(fx_dataset.ingredients))
    with pytest.raises(ValidationError):
        shape.model_validate({"items": [{"name": "x", "ingredient_id": "invented_thing"}]})
    factory = fake_factory([], parse_result={"items": [{"name": "dragonfruit", "ingredient_id": "lime"},
                                                       {"name": "unobtainium", "ingredient_id": "none"}]})
    assert map_ingredients(["dragonfruit", "unobtainium"], fx_dataset.ingredients, factory) == {"dragonfruit": "lime"}

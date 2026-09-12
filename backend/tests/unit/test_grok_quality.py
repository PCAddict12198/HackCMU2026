"""Answer-quality fixes found in the first live Grok run (fixtures + fakes only)."""

from tastespace.engine.explain import explain
from tastespace.grok.grounding import derive_ui_actions
from tastespace.grok.tools import TOOLS, ExplainPairArgs, FindTwinsArgs
from tastespace_contracts.api_models import ToolCallTrace


def test_explain_tool_reports_shared_strengths_not_shared_absences(fx_state):
    out = TOOLS["explain_pair"].run(fx_state, ExplainPairArgs(a="fx_noodle_soup", b="fx_spicy_soup"))
    assert "closest_dims" not in out and out["shared_strengths"]
    full = {d.dim: d for d in explain(fx_state, "fx_noodle_soup", "fx_spicy_soup").dims}
    for dim in out["shared_strengths"]:
        assert min(full[dim].a, full[dim].b) >= 0.2  # both dishes actually have it


def test_explain_tool_numbers_are_rounded_for_speech(fx_state):
    out = TOOLS["explain_pair"].run(fx_state, ExplainPairArgs(a="fx_noodle_soup", b="fx_spicy_soup"))
    values = [d["a"] for d in out["dims"]] + [c["value"] for side in out["attributions"].values()
                                              for contribs in side.values() for c in contribs]
    assert values and all(round(v, 2) == v for v in values)


def test_ui_actions_have_no_consecutive_duplicates(fx_state):
    search = {"matches": [{"dish_id": "fx_noodle_soup", "name": "Noodle soup", "cuisine": "japanese", "course": "savory"}]}
    twins = TOOLS["find_twins"].run(fx_state, FindTwinsArgs(dish_id="fx_noodle_soup"))
    trace = [ToolCallTrace(call_id="c0", tool="search_dishes", args={"query": "noodle soup"}, ok=True, result=search),
             ToolCallTrace(call_id="c1", tool="find_twins", args={"dish_id": "fx_noodle_soup"}, ok=True, result=twins)]
    actions = derive_ui_actions(trace, fx_state)
    assert all(a != b for a, b in zip(actions, actions[1:], strict=False))
    assert [a.type for a in actions].count("select_dish") == 1

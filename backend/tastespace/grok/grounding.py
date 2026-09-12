"""Keep Grok honest: numbers in replies must come from engine tool results, and UI actions are
derived from (and only reference dishes in) the tool trace."""

import re
from typing import Any

from pydantic import TypeAdapter
from tastespace_contracts.api_models import ToolCallTrace
from tastespace_contracts.ui_actions import (
    ExplainPair,
    HighlightDishes,
    OpenPanel,
    SelectDish,
    SetShift,
    ShowTwins,
    UiAction,
    referenced_dish_ids,
)

from ..state import EngineState

_NUM_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?%?")
_UI_ACTION = TypeAdapter(UiAction)


def numeric_leaves(obj: Any) -> list[float]:
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, dict):
        return [x for v in obj.values() for x in numeric_leaves(v)]
    if isinstance(obj, (list, tuple)):
        return [x for v in obj for x in numeric_leaves(v)]
    return []


def ungrounded_numbers(reply: str, trace: list[ToolCallTrace], user_text: str = "") -> list[str]:
    """Numbers in `reply` that no tool returned (small counting integers 0-10 are allowed)."""
    allowed = [x for t in trace for x in numeric_leaves(t.result) + numeric_leaves(t.args)]
    allowed += [float(tok.rstrip("%")) for tok in _NUM_RE.findall(user_text)]
    bad = []
    for tok in _NUM_RE.findall(reply):
        is_pct = tok.endswith("%")
        val = float(tok.rstrip("%"))
        if not is_pct and val.is_integer() and 0 <= val <= 10:
            continue
        decimals = len(tok.rstrip("%").split(".")[1]) if "." in tok else 0
        ok = any(round(x, decimals) == val or (is_pct and abs(x - val) <= 0.5)
                 or (is_pct and 0 <= x <= 1 and abs(100 * x - val) <= 0.5) for x in allowed)
        if not ok:
            bad.append(tok)
    return bad


def template_reply(trace: list[ToolCallTrace]) -> str:
    """Deterministic summary built only from tool results (used when Grok's text is not grounded)."""
    parts = []
    for t in trace:
        r = t.result or {}
        if not t.ok:
            continue
        if t.tool == "find_twins" and r.get("twins"):
            twins = ", ".join(f"{x['name']} ({x['cuisine']}, closer than {x['similarity_pct']:.0f}% of pairs)"
                              for x in r["twins"])
            parts.append(f"Flavor twins for {r.get('source_name')}: {twins}.")
        elif t.tool == "shift_taste" and r.get("results"):
            parts.append(f"Shifting {r.get('source_name')}: " + ", ".join(x["name"] for x in r["results"]) + ".")
        elif t.tool == "explain_pair":
            parts.append(f"{r.get('a_name')} vs {r.get('b_name')}: closer than {r.get('similarity_pct', 0):.0f}% of "
                         f"pairs; biggest differences in {', '.join(d['dim'] for d in r.get('dims', [])[:3])}.")
        elif t.tool == "search_dishes" and r.get("matches"):
            parts.append("Found: " + ", ".join(m["name"] for m in r["matches"]) + ".")
    return " ".join(parts) or "I couldn't find that in TasteSpace - try naming a dish from the galaxy."


def derive_ui_actions(trace: list[ToolCallTrace], state: EngineState) -> list:
    """Map successful tool calls to UI actions. Only dish ids present in tool results are used."""
    actions: list = []
    for t in trace:
        r = t.result or {}
        if not t.ok:
            continue
        if t.tool == "search_dishes" and len(r.get("matches", [])) == 1:
            actions.append(SelectDish(dish_id=r["matches"][0]["dish_id"]))
        elif t.tool == "find_twins" and r.get("twins"):
            ids = [x["dish_id"] for x in r["twins"]]
            actions += [SelectDish(dish_id=r["source_id"]),
                        ShowTwins(dish_id=r["source_id"], highlight_dish_id=ids[0]),
                        HighlightDishes(dish_ids=ids[:10]), OpenPanel(panel="twins")]
        elif t.tool == "shift_taste":
            actions += [SelectDish(dish_id=r["source_id"]),
                        SetShift(dish_id=r["source_id"], deltas=r.get("requested", {}))]
            if r.get("results"):
                actions.append(HighlightDishes(dish_ids=[x["dish_id"] for x in r["results"]][:10]))
            actions.append(OpenPanel(panel="shift"))
        elif t.tool == "explain_pair":
            actions += [ExplainPair(a=r["a"], b=r["b"]), OpenPanel(panel="explain")]
    return validate_ui_actions(actions, trace, state)


def validate_ui_actions(actions: list, trace: list[ToolCallTrace], state: EngineState) -> list:
    seen = {x for t in trace for x in _ids_in(t.result)} | {x for t in trace for x in _ids_in(t.args)}
    out = []
    for a in actions:
        a = _UI_ACTION.validate_python(a.model_dump() if hasattr(a, "model_dump") else a)
        if all(d in state.dishes and d in seen for d in referenced_dish_ids(a)) and (not out or out[-1] != a):
            out.append(a)  # (consecutive duplicates, e.g. search's select_dish then twins', are dropped)
    panels = [i for i, a in enumerate(out) if isinstance(a, OpenPanel)]
    return [a for i, a in enumerate(out) if not isinstance(a, OpenPanel) or i == panels[-1]]


def _ids_in(obj: Any) -> set[str]:
    if isinstance(obj, dict):
        found = {v for k, v in obj.items() if k in ("dish_id", "source_id", "a", "b") and isinstance(v, str)}
        return found | {x for v in obj.values() for x in _ids_in(v)}
    if isinstance(obj, list):
        return {x for v in obj for x in _ids_in(v)}
    return set()

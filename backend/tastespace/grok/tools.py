"""The ONLY functions Grok may call. Each runs the same engine function as its REST endpoint and
returns plain JSON; Grok must quote numbers from these results (grounding.py enforces it)."""

import difflib
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field
from tastespace_contracts.api_models import ShiftRequest
from tastespace_contracts.taxonomy import DimId

from ..engine.explain import explain
from ..engine.shift import shift
from ..engine.twins import find_twins
from ..state import EngineState
from .client import ToolSpec


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchDishesArgs(_Args):
    query: str = Field(min_length=1, max_length=80, description="dish name, partial name or cuisine")
    limit: int = Field(5, ge=1, le=10)


class FindTwinsArgs(_Args):
    dish_id: str = Field(description="exact dish_id from a previous tool result")
    k: int = Field(3, ge=1, le=5)


class DimChange(_Args):
    dim: DimId
    delta: float = Field(ge=-2.0, le=2.0, description="sigma units: 0.5 slight, 1 noticeable, 2 strong; negative = less")


class ShiftTasteArgs(_Args):
    dish_id: str = Field(description="exact dish_id from a previous tool result")
    changes: list[DimChange] = Field(min_length=1, max_length=6)


class ExplainPairArgs(_Args):
    a: str = Field(description="dish_id")
    b: str = Field(description="dish_id")


@dataclass
class Tool:
    name: str
    description: str
    args_model: type[_Args]
    run: Callable[[EngineState, BaseModel], dict]


def _name(state: EngineState, did: str) -> str:
    return state.dishes[did].name if did in state.dishes else did


def _search(state: EngineState, args: SearchDishesArgs) -> dict:
    q = args.query.lower().strip()
    scored = []
    for did, meta in state.dishes.items():
        hay = [meta.name.lower(), did.replace("_", " ")]
        if meta.cuisine == q:
            score = 0.9
        elif any(q in h for h in hay):
            score = 1.0
        else:
            score = max(difflib.SequenceMatcher(None, q, h).ratio() for h in hay)
        if score >= 0.5:
            scored.append((score, did))
    scored.sort(key=lambda x: -x[0])
    return {"matches": [{"dish_id": d, "name": _name(state, d), "cuisine": state.dishes[d].cuisine,
                         "course": state.dishes[d].course} for _, d in scored[: args.limit]]}


def _twins(state: EngineState, args: FindTwinsArgs) -> dict:
    out = find_twins(state, args.dish_id, args.k).model_dump()
    out["source_name"] = _name(state, args.dish_id)
    for t in out["twins"]:
        t["name"] = _name(state, t["dish_id"])
        t["cuisine"] = state.dishes[t["dish_id"]].cuisine
    return out


def _shift(state: EngineState, args: ShiftTasteArgs) -> dict:
    deltas = {c.dim: c.delta for c in args.changes}
    out = shift(state, ShiftRequest(dish_id=args.dish_id, deltas=deltas, k=5)).model_dump()  # type: ignore[arg-type]
    out.pop("target_z", None)  # large + not useful in prose
    out["source_name"] = _name(state, args.dish_id)
    out["requested"] = deltas
    for r in out["results"]:
        r["name"] = _name(state, r["dish_id"])
    return out


def _explain(state: EngineState, args: ExplainPairArgs) -> dict:
    out = explain(state, args.a, args.b).model_dump()
    dims = sorted(out["dims"], key=lambda d: -d["distance_share"])
    out["dims"] = dims[:6]
    # strengths they SHARE: both clearly present and close. (Smallest distance share also picks dims
    # where both are ~0, which the model then reported as "they align most on bitter".)
    both = [d for d in dims if min(d["a"], d["b"]) >= 0.2]
    out["shared_strengths"] = [d["dim"] for d in sorted(both, key=lambda d: abs(d["a"] - d["b"]) - min(d["a"], d["b"]))][:4]
    top = {x["dim"] for x in dims[:4]}
    out["attributions"] = {side: {dim: contribs[:2] for dim, contribs in out["attributions"][side].items() if dim in top}
                           for side in ("a", "b")}
    out["a_name"], out["b_name"] = _name(state, args.a), _name(state, args.b)
    return _round(out)  # Grok quotes what it sees: 0.8, not 0.7991


def _round(obj, nd: int = 2):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, dict):
        return {k: _round(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, nd) for v in obj]
    return obj


TOOLS: dict[str, Tool] = {
    "search_dishes": Tool("search_dishes", "Find dishes in TasteSpace by name or cuisine. Use it to resolve any "
                          "dish the user mentions into a dish_id.", SearchDishesArgs, _search),  # type: ignore[arg-type]
    "find_twins": Tool("find_twins", "Flavor Twins: dishes from OTHER cuisines with the most similar sensory "
                       "profile (similarity is a percentile over dish pairs).", FindTwinsArgs, _twins),  # type: ignore[arg-type]
    "shift_taste": Tool("shift_taste", "Start from a dish and move through taste space (e.g. lighter = rich "
                        "negative, more acidic = sour positive); returns dishes near the new target.",
                        ShiftTasteArgs, _shift),  # type: ignore[arg-type]
    "explain_pair": Tool("explain_pair", "Explain why two dishes are similar or different: per-dimension values "
                         "and which ingredients produce them.", ExplainPairArgs, _explain),  # type: ignore[arg-type]
}


def tool_specs() -> list[ToolSpec]:
    return [ToolSpec(name=t.name, description=t.description, parameters=t.args_model.model_json_schema())
            for t in TOOLS.values()]

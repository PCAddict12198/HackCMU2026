#!/usr/bin/env python3
"""INTEGRATOR ONLY (`make fixtures`): regenerate contracts/fixtures/api/*.json from the current data/.
Run rarely (H0, and when a breaking contract change lands at a checkpoint). Every fixture is validated
against its contract model before it is written. P3's mock mode serves these files."""

import json
import sys
from pathlib import Path

import numpy as np
from tastespace.build import build_state
from tastespace.engine.explain import explain
from tastespace.engine.recipe import analyze_recipe
from tastespace.engine.shift import shift
from tastespace.engine.twins import find_twins
from tastespace.grok.grounding import derive_ui_actions
from tastespace.grok.tools import TOOLS, FindTwinsArgs, ShiftTasteArgs
from tastespace_contracts import CONTRACT_VERSION
from tastespace_contracts.api_models import (
    AskResponse,
    DishPoint,
    HealthResponse,
    RecipeRequest,
    ShiftRequest,
    SpaceMeta,
    SpaceResponse,
    ToolCallTrace,
)
from tastespace_contracts.errors import ERROR_STATUS, ErrorBody, ErrorResponse
from tastespace_contracts.taxonomy import CUISINE_IDS, DIM_IDS, FORMAT_IDS
from tastespace_contracts.ui_actions import (
    ExplainPair,
    HighlightDishes,
    OpenPanel,
    SelectDish,
    SetShift,
    ShowTwins,
)
from tastespace_contracts.validate import load_dataset

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "contracts" / "fixtures" / "api"
DEMO, PAIR = "tonkotsu_ramen", "french_onion_soup"
RECIPE = "200 g spaghetti\n100 g guanciale\n2 eggs\n50 g pecorino\n1 tsp black pepper\n1 pinch saffron"


def write(name: str, obj) -> None:
    data = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj
    type(obj).model_validate(data) if hasattr(obj, "model_dump") else None
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {name}")


def ask_fixture(state) -> AskResponse:
    twins = TOOLS["find_twins"].run(state, FindTwinsArgs(dish_id=DEMO, k=3))
    moved = TOOLS["shift_taste"].run(state, ShiftTasteArgs.model_validate(
        {"dish_id": DEMO, "changes": [{"dim": "rich", "delta": -0.8}, {"dim": "sour", "delta": 1.2}]}))
    trace = [ToolCallTrace(call_id="call_0", tool="find_twins", args={"dish_id": DEMO, "k": 3}, ok=True, result=twins),
             ToolCallTrace(call_id="call_1", tool="shift_taste", args={"dish_id": DEMO, "changes": [
                 {"dim": "rich", "delta": -0.8}, {"dim": "sour", "delta": 1.2}]}, ok=True, result=moved)]
    top = twins["twins"][0]
    actions = derive_ui_actions(trace, state)
    # make sure the fixture exercises EVERY ui_action type (P3 builds the reducer against it)
    actions += [ExplainPair(a=DEMO, b=top["dish_id"]), OpenPanel(panel="explain")]
    have = {a.type for a in actions}
    for extra in (SelectDish(dish_id=DEMO), ShowTwins(dish_id=DEMO, highlight_dish_id=top["dish_id"]),
                  SetShift(dish_id=DEMO, deltas={"rich": -0.8, "sour": 1.2}),
                  HighlightDishes(dish_ids=[t["dish_id"] for t in twins["twins"]])):
        if extra.type not in have:
            actions.append(extra)
    reply = f"{top['name']} is the flavor twin of {twins['source_name']}: closer than {top['similarity_pct']:.0f}% of dish pairs."
    return AskResponse(reply=reply, grounded=True, ui_actions=actions, tool_trace=trace)


def large_space(space: SpaceResponse, state) -> SpaceResponse:
    """80 synthetic clustered dishes (ids fx_###) for galaxy layout/perf work. Vectors are FAKE."""
    rng = np.random.default_rng(7)
    centers = rng.uniform(0.05, 0.8, size=(8, len(DIM_IDS)))
    dishes = []
    for i in range(80):
        c = i % 8
        v = np.clip(centers[c] + rng.normal(0, 0.12, len(DIM_IDS)), 0, 1)
        cuisine = CUISINE_IDS[(i * 3 + c) % len(CUISINE_IDS)]
        dishes.append(DishPoint(id=f"fx_{i:03d}", name=f"Fixture {cuisine} dish {i:02d}", cuisine=cuisine,
                                course="dessert" if c == 7 else "savory", format=FORMAT_IDS[(i + c) % len(FORMAT_IDS)],
                                tier="core", confidence="draft", blurb="Synthetic fixture dish (fake values).",
                                xyz=tuple(round(float(x), 4) for x in state.model.project(v)),
                                vector={d: round(float(v[k]), 4) for k, d in enumerate(DIM_IDS)}))
    meta = SpaceMeta(build_id="fixture-large", data_tier="core", n_dishes=len(dishes), contract_version=CONTRACT_VERSION,
                     dim_order=list(DIM_IDS), warnings=["synthetic fixture: values are fake"])
    return SpaceResponse(dims=space.dims, cuisines=space.cuisines, dishes=dishes, pca=space.pca, meta=meta)


def main() -> int:
    ds = load_dataset(ROOT / "data", "core")
    state = build_state(ds)
    space = state.space_response()
    for did in (DEMO, PAIR):
        if did not in state.dishes:
            print(f"fixture dish '{did}' missing from data/", file=sys.stderr)
            return 1
    OUT.mkdir(parents=True, exist_ok=True)
    write("health.json", HealthResponse(build_ready=True, data_ready=True, grok_configured=True,
                                        contract_version=CONTRACT_VERSION, build_id=state.build_id))
    write("space.json", space)
    write("space_large.json", large_space(space, state))
    write("twins.json", find_twins(state, DEMO, 3))
    write("shift.json", shift(state, ShiftRequest(dish_id=DEMO, deltas={"rich": -0.8, "sour": 1.2}, k=5)))
    write("explain.json", explain(state, DEMO, PAIR))
    write("recipe.json", analyze_recipe(state, ds, RecipeRequest(text=RECIPE, name="My carbonara", format="noodles")))
    write("ask.json", ask_fixture(state))
    errors = {code: ErrorResponse(error=ErrorBody(code=code, message=f"example {code} error")).model_dump(mode="json")
              for code in ERROR_STATUS}
    (OUT / "errors.json").write_text(json.dumps(errors, indent=2) + "\n")
    print("wrote errors.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

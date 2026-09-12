"""Engine hardening (H0-3): calibration on sparse dims, tiny courses, identical dishes.
Synthetic spaces only - no data/ reads."""

import numpy as np
import pytest
from tastespace.engine.aggregate import calibrate
from tastespace.engine.shift import shift
from tastespace.engine.space import fit_space
from tastespace.engine.twins import EMPTY_COURSE_NOTE, LADDER, find_twins
from tastespace.state import DishMeta, EngineState
from tastespace_contracts.api_models import ShiftRequest
from tastespace_contracts.taxonomy import DIM_IDS

N = len(DIM_IDS)


def saturate(raw: float, s: float) -> float:
    return 1.0 - np.exp(-raw / s)


def make_state(rows: list[tuple[str, str, str, list[float]]]) -> EngineState:
    """rows: (id, course, cuisine, vector-of-N) -> minimal EngineState for engine calls."""
    ids = [r[0] for r in rows]
    V = np.array([r[3] for r in rows], dtype=float)
    m = fit_space(ids, [r[1] for r in rows], [r[2] for r in rows], V, np.ones(N))
    dishes = {r[0]: DishMeta(r[0], r[0], r[2], r[1], "soup", "core", "draft") for r in rows}
    return EngineState("synthetic", "core", m, dishes, {}, [], [])


def test_sparse_dim_is_not_saturated():
    raws = np.zeros((10, N))
    raws[:, 0] = np.linspace(0.1, 1.0, 10)  # dense dim: every dish has it
    raws[8, 1], raws[9, 1] = 0.05, 0.5  # sparse dim: only 2 of 10 dishes
    s = calibrate(raws)
    assert saturate(0.05, s[1]) < 0.4  # a hint of the dim stays a hint...
    assert 0.85 < saturate(0.5, s[1]) < 0.95  # ...and the strongest dish lands near the target
    assert np.isclose(saturate(np.quantile(raws[:, 0], 0.9), s[0]), 0.9)  # dense dims: plain 90th pct


def test_dim_no_dish_has_gets_a_safe_scale():
    s = calibrate(np.zeros((5, N)))
    assert np.all(s == 1.0) and np.isfinite(s).all()


def test_single_dish_course_returns_empty_results_not_errors():
    base = [0.5] * N
    state = make_state([("a", "savory", "thai", base), ("b", "savory", "french", [0.4] * N),
                        ("lonely", "dessert", "italian", base)])
    twins = find_twins(state, "lonely", 3)
    assert twins.twins == [] and twins.relaxation_note == EMPTY_COURSE_NOTE
    assert twins.relaxation_level == len(LADDER)
    assert shift(state, ShiftRequest(dish_id="lonely", deltas={"sour": 1.0})).results == []


def test_identical_dishes_are_perfect_twins():
    v = list(np.linspace(0.1, 0.9, N))
    state = make_state([("x", "savory", "japanese", v), ("y", "savory", "mexican", v),
                        ("z", "savory", "french", [0.9 - t for t in v])])
    top = find_twins(state, "x", 1).twins[0]
    assert top.dish_id == "y" and top.distance == 0.0 and top.diffs == []
    # percentile = share of same-course pairs FARTHER apart; the pair itself never counts, so with
    # 3 pairs a perfect twin is "closer than 66.7% of pairs" (99.9% in a real ~55-dish course)
    assert top.similarity_pct == pytest.approx(66.7, abs=0.1)

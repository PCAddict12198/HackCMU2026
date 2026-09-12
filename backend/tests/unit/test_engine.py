import numpy as np
import pytest
from tastespace.engine import twins as twins_mod
from tastespace.engine.aggregate import finalize, raw_dish
from tastespace.engine.explain import explain
from tastespace.engine.shift import shift
from tastespace.engine.transforms import DIM_INDEX, apply_processes
from tastespace.engine.twins import LADDER, find_twins
from tastespace.errors import TasteSpaceError
from tastespace_contracts.api_models import ShiftRequest
from tastespace_contracts.taxonomy import DIM_IDS


def test_process_transform_applies_in_order_and_clips(fx_dataset):
    r = np.zeros(len(DIM_IDS))
    r[DIM_INDEX["sweet"]] = 0.9
    out = apply_processes(r, ["caramelized", "caramelized"], fx_dataset.processes)
    assert out[DIM_INDEX["sweet"]] == 1.0  # clipped
    assert np.isclose(out[DIM_INDEX["roasted"]], 0.9)


def test_golden_aggregation(fx_dataset):
    rd = raw_dish(fx_dataset.dishes["fx_sweet_cream"], fx_dataset.ingredients, fx_dataset.processes, fx_dataset.formats)
    # cream share .8 * potency 1.5 * creamy .9 = 1.08 ; sugar share .2 * potency 3 * sweet 1 = .6
    assert np.isclose(rd.raw[DIM_INDEX["creamy"]], 1.08)
    assert np.isclose(rd.raw[DIM_INDEX["rich"]], 0.96)
    assert np.isclose(rd.raw[DIM_INDEX["sweet"]], 0.6)
    dv = finalize(rd, np.ones(len(DIM_IDS)))
    ing = 1 - np.exp(-1.08)
    assert np.isclose(dv.vector[DIM_INDEX["creamy"]], ing + 0.7 * (1 - ing))  # custard_creamy f_creamy = 0.7
    assert np.isclose(dv.vector[DIM_INDEX["sweet"]], 1 - np.exp(-0.6))


def test_attributions_sum_to_vector_and_vectors_in_range(fx_state):
    m = fx_state.model
    assert (m.V >= 0).all() and (m.V <= 1).all()
    for did, attr in fx_state.attributions.items():
        v = m.V[m.index[did]]
        for k, dim in enumerate(DIM_IDS):
            assert abs(sum(c["value"] for c in attr[dim]) - v[k]) < 1e-9


def test_projection_roundtrip_and_unseen_vector(fx_state):
    space = fx_state.space_response()
    m = fx_state.model
    for p in space.dishes:
        assert np.allclose(m.project(m.V[m.index[p.id]]), p.xyz, atol=1e-3)
    assert np.isfinite(m.project(np.full(len(DIM_IDS), 0.5))).all()


def test_percentile_is_monotonic(fx_state):
    m = fx_state.model
    pcts = [m.similarity_pct(d, "savory") for d in np.linspace(0, 20, 50)]
    assert all(a >= b for a, b in zip(pcts, pcts[1:], strict=False))
    assert pcts[0] == 100.0 and pcts[-1] == 0.0


def test_twins_are_same_course_and_other_cuisine(fx_state):
    res = find_twins(fx_state, "fx_noodle_soup", 3)
    assert res.twins
    for t in res.twins:
        assert fx_state.dishes[t.dish_id].course == "savory"
        assert fx_state.dishes[t.dish_id].cuisine != "japanese"
        assert len(t.shared_dims) <= 5 and len(t.diffs) <= 3


@pytest.mark.parametrize("pct,level", [(95.0, 0), (85.0, 1), (75.0, 2), (10.0, 3)])
def test_every_twin_relaxation_level_is_reachable(fx_state, monkeypatch, pct, level):
    monkeypatch.setattr(type(fx_state.model), "similarity_pct", lambda self, d, course: pct)
    assert find_twins(fx_state, "fx_noodle_soup", 1).relaxation_level == level


def test_same_cuisine_fallback(fx_state, monkeypatch):
    monkeypatch.setattr(twins_mod, "cuisine_distance", lambda a, b: 0.0)
    res = find_twins(fx_state, "fx_noodle_soup", 2)
    assert res.relaxation_level == len(LADDER) and res.twins


def test_shift_moves_in_requested_direction(fx_state):
    res = shift(fx_state, ShiftRequest(dish_id="fx_noodle_soup", deltas={"sour": 1.5}, k=3))
    assert res.results
    if res.relaxation_level == 0:
        assert all(r.moved["sour"] > 0 for r in res.results)
    assert len(res.target_xyz) == 3 and "fx_noodle_soup" not in [r.dish_id for r in res.results]


def test_shift_without_deltas_returns_neighbours(fx_state):
    res = shift(fx_state, ShiftRequest(dish_id="fx_sweet_cream", k=5))
    assert [r.dish_id for r in res.results] == ["fx_sweet_lime"]  # only other dessert


def test_unknown_dish_is_not_found(fx_state):
    with pytest.raises(TasteSpaceError) as exc:
        find_twins(fx_state, "nope")
    assert exc.value.code == "not_found"


def test_explain_distance_shares_sum_to_one(fx_state):
    res = explain(fx_state, "fx_noodle_soup", "fx_spicy_soup")
    assert abs(sum(d.distance_share for d in res.dims) - 1) < 1e-3
    assert set(res.attributions.a) == set(DIM_IDS)

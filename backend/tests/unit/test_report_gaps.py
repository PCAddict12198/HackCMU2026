"""The build report tells P1 which empty ingredients matter most (fixtures only)."""

import dataclasses

from tastespace.build import build_state
from tastespace.report import data_gaps, render_report


def with_empty(ds, *ids):
    ings = {**ds.ingredients, **{i: ds.ingredients[i].model_copy(update={"profile": {}}) for i in ids}}
    return dataclasses.replace(ds, ingredients=ings)


def test_complete_fixture_has_no_gaps(fx_dataset):
    assert data_gaps(fx_dataset) == ([], [])


def test_gaps_ranked_by_share_times_potency(fx_dataset):
    ds = with_empty(fx_dataset, "cream", "onion")
    gaps, blind = data_gaps(ds)
    assert [g["id"] for g in gaps] == ["cream", "onion"]  # cream: big shares x potency 1.5
    assert gaps[0]["dishes"] == 3
    assert ("fx_sweet_cream", 0.8) in blind  # 200 g of 250 g is cream


def test_report_has_gap_section(fx_dataset):
    ds = with_empty(fx_dataset, "cream")
    text = render_report(build_state(ds), ds)
    assert "## Data gaps (fill these first)" in text and "| cream | 3 |" in text

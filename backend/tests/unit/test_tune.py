"""Weight tuning is judged by human ratings; sanity pairs are only reported (fixtures only)."""

import dataclasses
import math

import pytest
from tastespace.build import build_state
from tastespace.tune import SCHEMES, evaluate
from tastespace_contracts.data_models import RatingPair, RatingsFile
from tastespace_contracts.taxonomy import DIM_GROUP, DIM_IDS


def test_group_balanced_gives_each_group_equal_total_weight():
    w = SCHEMES["group_balanced"]
    totals = {g: sum(w[d] for d in DIM_IDS if DIM_GROUP[d] == g) for g in ("taste", "aroma", "mouthfeel")}
    assert all(t == pytest.approx(len(DIM_IDS) / 3) for t in totals.values())
    assert sum(w.values()) == pytest.approx(len(DIM_IDS))


def test_weights_reach_the_space(fx_dataset):
    assert build_state(fx_dataset, weights=SCHEMES["group_balanced"]).model.weights.tolist() == \
        [SCHEMES["group_balanced"][d] for d in DIM_IDS]


def test_evaluate_without_ratings_reports_nan(fx_dataset):
    r = evaluate(fx_dataset, SCHEMES["neutral"])
    assert r["n_rated"] == 0 and math.isnan(r["spearman"])
    assert r["sanity_pos"].endswith("/1")  # reported, whatever the outcome


def test_evaluate_uses_ratings(fx_dataset):
    pairs = [RatingPair(a="fx_noodle_soup", b="fx_spicy_soup", ratings={"p1": 5}),
             RatingPair(a="fx_noodle_soup", b="fx_lime_salad", ratings={"p1": 2}),
             RatingPair(a="fx_cream_noodles", b="fx_lime_salad", ratings={"p1": 1})]
    ds = dataclasses.replace(fx_dataset, ratings=RatingsFile(pairs=pairs))
    r = evaluate(ds, SCHEMES["neutral"])
    assert r["n_rated"] == 3 and not math.isnan(r["spearman"])

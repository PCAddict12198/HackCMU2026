"""AI ratings must never be reported, or used, as human validation (fixtures only)."""

import dataclasses
import math

from tastespace.build import build_state
from tastespace.report import is_ai_rater, rater_panel, render_report
from tastespace.tune import SCHEMES, evaluate
from tastespace_contracts.data_models import RatingPair, RatingsFile

PAIRS = [("fx_noodle_soup", "fx_spicy_soup", 5, 4), ("fx_noodle_soup", "fx_lime_salad", 2, 3),
         ("fx_cream_noodles", "fx_lime_salad", 1, 1), ("fx_spicy_soup", "fx_cream_noodles", 2, 2)]


def with_ratings(ds, human: bool, ai: bool):
    pairs = [RatingPair(a=a, b=b, ratings={**({"p1": h} if human else {}), **({"claude": c} if ai else {})})
             for a, b, h, c in PAIRS]
    return dataclasses.replace(ds, ratings=RatingsFile(pairs=pairs))


def test_ai_rater_detection():
    assert is_ai_rater("claude") and is_ai_rater("Grok") and is_ai_rater("ai_panel")
    assert not is_ai_rater("p1") and not is_ai_rater("ishan")


def test_panel_separates_human_and_ai(fx_dataset):
    ds = with_ratings(fx_dataset, human=True, ai=True)
    panel = rater_panel(build_state(ds), ds)
    assert {r["rater"]: r["kind"] for r in panel["rows"]} == {"claude": "AI", "p1": "human"}
    assert panel["human_keys"] == ["p1"] and panel["ai_keys"] == ["claude"] and panel["human"][0] == 4


def test_ai_only_report_says_not_human_validation(fx_dataset):
    ds = with_ratings(fx_dataset, human=False, ai=True)
    text = render_report(build_state(ds), ds)
    assert "Human ratings vs model" not in text
    assert "human panel: none" in text and "NOT human validation" in text and "| claude | AI |" in text


def test_ai_ratings_never_choose_weights(fx_dataset):
    r = evaluate(with_ratings(fx_dataset, human=False, ai=True), SCHEMES["neutral"])
    assert r["n_rated"] == 0 and math.isnan(r["spearman"]) and not math.isnan(r["ai_rho"])

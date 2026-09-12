"""Demo pairs come from engine output: cross-region, deduplicated, strongest first (fixtures only)."""

from tastespace.report import demo_candidates, render_report


def test_candidates_are_cross_region_unique_and_sorted(fx_state):
    cands = demo_candidates(fx_state, min_pct=0.0)
    assert cands
    pairs = [frozenset((c["a"], c["b"])) for c in cands]
    assert len(pairs) == len(set(pairs))
    assert [c["pct"] for c in cands] == sorted((c["pct"] for c in cands), reverse=True)
    for c in cands:  # japanese/thai (asia) vs italian (europe) only: distance 1.0
        cuisines = {fx_state.dishes[c["a"]].cuisine, fx_state.dishes[c["b"]].cuisine}
        assert "italian" in cuisines and len(cuisines) == 2


def test_threshold_filters(fx_state):
    assert all(c["pct"] >= 90 for c in demo_candidates(fx_state))


def test_report_section(fx_state, fx_dataset):
    assert "## Demo candidates" in render_report(fx_state, fx_dataset)

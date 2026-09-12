"""Compare dimension-weight schemes on HELD-OUT human ratings. OWNER: engine (P2).

    uv run python -m tastespace.tune [--data-dir data]

Choose weights by the Spearman correlation with data/validation/ratings.yaml (the H15 blind rating
study), never by sanity hits: the sanity set is frozen and is only shown as a secondary column.
Apply the chosen scheme by editing engine/space.py DEFAULT_WEIGHTS.
"""

import argparse
import math
import sys

from tastespace_contracts.taxonomy import DIM_GROUP, DIM_IDS
from tastespace_contracts.validate import Dataset, load_dataset

from .build import build_state
from .config import get_settings
from .engine.twins import find_twins
from .report import rater_panel, sanity_results

MIN_RATED = 10
GROUPS = ("taste", "aroma", "mouthfeel")


def _group_balanced() -> dict[str, float]:
    """Each sensory group gets the same total weight (aroma has 7 dims, the others 5)."""
    per_group = len(DIM_IDS) / len(GROUPS)
    sizes = {g: sum(1 for d in DIM_IDS if DIM_GROUP[d] == g) for g in GROUPS}
    return {d: per_group / sizes[DIM_GROUP[d]] for d in DIM_IDS}


SCHEMES: dict[str, dict[str, float]] = {
    "neutral": {d: 1.0 for d in DIM_IDS},
    "group_balanced": _group_balanced(),
}


def evaluate(ds: Dataset, weights: dict[str, float]) -> dict:
    state = build_state(ds, weights=weights)
    panel = rater_panel(state, ds)
    s = sanity_results(state, ds)
    return {
        "n_rated": panel["human"][0],  # only HUMAN raters can choose weights
        "spearman": panel["human"][1],
        "ai_rho": panel["ai"][1],  # reference only
        "sanity_pos": f"{sum(r['pass'] for r in s['positive'])}/{len(s['positive'])}",
        "sanity_neg": f"{sum(r['pass'] for r in s['negative'])}/{len(s['negative'])}",
        "strict_twins": sum(1 for d in state.model.ids if find_twins(state, d, 3).relaxation_level == 0),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare weight schemes on held-out human ratings.")
    ap.add_argument("--data-dir", default=str(get_settings().data_dir))
    args = ap.parse_args(argv)
    ds = load_dataset(args.data_dir, "core")
    rows = {name: evaluate(ds, w) for name, w in SCHEMES.items()}
    fmt = lambda x: "-" if math.isnan(x) else f"{x:.2f}"  # noqa: E731
    print(f"{'scheme':<16}{'human':>6}{'human rho':>11}{'AI rho*':>9}{'sanity+':>9}{'sanity-':>9}{'strict twins':>14}")
    for name, r in rows.items():
        print(f"{name:<16}{r['n_rated']:>6}{fmt(r['spearman']):>11}{fmt(r['ai_rho']):>9}{r['sanity_pos']:>9}"
              f"{r['sanity_neg']:>9}{r['strict_twins']:>14}")
    print("* AI-rater baseline: reference only, never used to choose weights.")
    rated = max(r["n_rated"] for r in rows.values())
    if rated < MIN_RATED:
        print(f"\nOnly {rated} HUMAN-rated pairs (need >= {MIN_RATED}). Keep 'neutral'.")
    else:
        best = max(rows, key=lambda n: -math.inf if math.isnan(rows[n]["spearman"]) else rows[n]["spearman"])
        print(f"\nBest by human ratings: {best}. Sanity columns are informational only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

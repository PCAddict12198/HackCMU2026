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
from .report import pair_pct, sanity_results, spearman

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
    xs, ys = [], []
    for p in (ds.ratings.pairs if ds.ratings else []):
        pct = pair_pct(state, p.a, p.b)
        if pct is not None and p.ratings:
            xs.append(pct)
            ys.append(sum(p.ratings.values()) / len(p.ratings))
    s = sanity_results(state, ds)
    return {
        "n_rated": len(xs),
        "spearman": spearman(xs, ys) if len(xs) >= 3 else float("nan"),
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
    print(f"{'scheme':<16}{'rated':>6}{'spearman':>10}{'sanity+':>9}{'sanity-':>9}{'strict twins':>14}")
    for name, r in rows.items():
        rho = "-" if math.isnan(r["spearman"]) else f"{r['spearman']:.2f}"
        print(f"{name:<16}{r['n_rated']:>6}{rho:>10}{r['sanity_pos']:>9}{r['sanity_neg']:>9}{r['strict_twins']:>14}")
    rated = max(r["n_rated"] for r in rows.values())
    if rated < MIN_RATED:
        print(f"\nOnly {rated} rated pairs (need >= {MIN_RATED}). Keep 'neutral' until the H15 rating study is in.")
    else:
        best = max(rows, key=lambda n: -math.inf if math.isnan(rows[n]["spearman"]) else rows[n]["spearman"])
        print(f"\nBest by human ratings: {best}. Sanity columns are informational only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

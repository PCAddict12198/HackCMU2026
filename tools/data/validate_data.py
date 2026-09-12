#!/usr/bin/env python3
"""P1: validate data/ against the frozen contracts, then show corpus progress. OWNER: data (P1).

    uv run python tools/data/validate_data.py [data_dir] [--tier core|all] [--strict]
"""

import sys
from collections import Counter

from tastespace_contracts.validate import DataValidationError, load_dataset
from tastespace_contracts.validate import main as validate_main

UNGROUNDED = ("seed_placeholder", "grok_draft", "fixture")


def progress(data_dir: str) -> None:
    try:
        ds = load_dataset(data_dir, "all")
    except DataValidationError:
        return
    manifest = ds.manifest.core if ds.manifest else []
    core = [d for d in ds.dishes.values() if d.tier == "core"]
    reviewed = sum(1 for d in core if d.confidence == "reviewed")
    per_cuisine = Counter(d.cuisine for d in core)
    values = [ing.value(k) for ing in ds.ingredients.values() for k in ing.profile]
    nonzero = [v for v in values if v is not None and v.v > 0]
    grounded = sum(1 for v in nonzero if v.src not in UNGROUNDED)
    print(f"\nPROGRESS  core dishes {len(core)}/{len(manifest)} (reviewed {reviewed})  |  "
          f"ingredients {len(ds.ingredients)}  |  grounded values {grounded}/{len(nonzero)} "
          f"({100 * grounded // max(1, len(nonzero))}%)  |  extended {len(ds.extended_dishes)}")
    print("  per cuisine: " + ", ".join(f"{c} {n}" for c, n in sorted(per_cuisine.items())))


if __name__ == "__main__":
    args = sys.argv[1:]
    code = validate_main(args)
    if code == 0:
        progress(next((a for a in args if not a.startswith("-")), "data"))
    sys.exit(code)

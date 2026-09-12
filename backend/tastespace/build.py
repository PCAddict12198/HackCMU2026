"""`make build`: data/ -> build/tastespace.json + build/report.md. OWNER: engine (P2).

    uv run python -m tastespace.build [--tier core|all] [--freeze-calibration] [--ignore-frozen]

Calibration (s_k) is computed on the CORE tier only, so extended drafts never move the space.
At H16 run with --freeze-calibration to pin s_k in backend/tastespace/calibration_frozen.json.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from tastespace_contracts.taxonomy import CUISINE_IDS, DIM_IDS
from tastespace_contracts.validate import Dataset, DataValidationError, load_dataset

from .config import get_settings
from .engine.aggregate import calibrate, finalize, raw_dish
from .engine.space import fit_space
from .errors import TasteSpaceError
from .report import render_report, sanity_results
from .state import DishMeta, EngineState

FROZEN_CALIBRATION = Path(__file__).with_name("calibration_frozen.json")


def build_state(ds: Dataset, calibration: np.ndarray | None = None) -> EngineState:
    ids = sorted(ds.dishes)
    if len(ids) < 2:
        raise TasteSpaceError("not_ready", "need at least 2 dishes to build a space")
    raws = {d: raw_dish(ds.dishes[d], ds.ingredients, ds.processes, ds.formats) for d in ids}
    core_ids = [d for d in ids if ds.dishes[d].tier == "core"] or ids
    s = np.asarray(calibration, float) if calibration is not None else calibrate(np.array([raws[d].raw for d in core_ids]))
    vecs = {d: finalize(raws[d], s) for d in ids}
    V = np.array([vecs[d].vector for d in ids])
    model = fit_space(ids, [ds.dishes[d].course for d in ids], [ds.dishes[d].cuisine for d in ids], V, s)

    h = hashlib.sha256(json.dumps(ids).encode())
    h.update(np.round(V, 6).tobytes())
    dishes = {d: DishMeta(id=d, name=ds.dishes[d].name, cuisine=ds.dishes[d].cuisine, course=ds.dishes[d].course,
                          format=ds.dishes[d].format, tier=ds.dishes[d].tier, confidence=ds.dishes[d].confidence,
                          blurb=ds.dishes[d].blurb) for d in ids}
    dims = [{"id": x.id, "group": x.group, "label": x.label, "low_label": x.low_label, "high_label": x.high_label}
            for x in ds.dims]
    cuisines = [{"id": c, "name": ds.cuisines[c].name, "region": ds.cuisines[c].region, "macro": ds.cuisines[c].macro}
                for c in CUISINE_IDS if c in ds.cuisines]
    return EngineState(build_id=h.hexdigest()[:12], data_tier=ds.tier, model=model, dishes=dishes,
                       attributions={d: vecs[d].attributions for d in ids}, dims=dims, cuisines=cuisines,
                       warnings=list(ds.warnings))


def load_frozen_calibration() -> np.ndarray | None:
    if not FROZEN_CALIBRATION.exists():
        return None
    data = json.loads(FROZEN_CALIBRATION.read_text())
    if data.get("dims") != list(DIM_IDS):
        raise SystemExit("calibration_frozen.json was made for different dims; rebuild with --ignore-frozen")
    return np.asarray(data["s"], float)


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    ap = argparse.ArgumentParser(description="Build the TasteSpace artifact from data/.")
    ap.add_argument("--data-dir", default=str(settings.data_dir))
    ap.add_argument("--tier", choices=["core", "all"], default=settings.data_tier)
    ap.add_argument("--out-dir", default=str(settings.build_dir))
    ap.add_argument("--freeze-calibration", action="store_true", help="pin s_k for future builds (H16)")
    ap.add_argument("--ignore-frozen", action="store_true", help="recompute s_k even if frozen")
    args = ap.parse_args(argv)

    try:
        ds = load_dataset(args.data_dir, args.tier)
    except DataValidationError as exc:
        print("\n".join(f"ERROR {e}" for e in exc.errors), file=sys.stderr)
        print(f"build: data invalid ({len(exc.errors)} errors) - run `make check-data`", file=sys.stderr)
        return 1
    state = build_state(ds, None if args.ignore_frozen else load_frozen_calibration())

    out = Path(args.out_dir)
    state.save(out / "tastespace.json")
    (out / "report.md").write_text(render_report(state, ds))
    if args.freeze_calibration:
        FROZEN_CALIBRATION.write_text(json.dumps({"dims": list(DIM_IDS), "s": state.model.s.tolist(),
                                                  "build_id": state.build_id}, indent=2) + "\n")
        print(f"froze calibration -> {FROZEN_CALIBRATION}")

    s = sanity_results(state, ds)
    print(f"build {state.build_id}: {len(state.model.ids)} dishes (tier={args.tier}) -> {out / 'tastespace.json'}")
    print(f"  sanity: positive {sum(r['pass'] for r in s['positive'])}/{len(s['positive'])}, "
          f"negative {sum(r['pass'] for r in s['negative'])}/{len(s['negative'])}, skipped {s['skipped']}"
          f"  | report: {out / 'report.md'}")
    for w in ds.warnings:
        print(f"  WARN {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

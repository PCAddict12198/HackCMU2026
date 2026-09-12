"""build/report.md: the honest scoreboard for the space. OWNER: engine (P2).

Sanity pairs are FROZEN (data/sanity/). Read this report; never edit data just to make a demo pair pass.
"""

from collections import Counter

import numpy as np
from tastespace_contracts import CONTRACT_VERSION
from tastespace_contracts.taxonomy import DIM_IDS
from tastespace_contracts.validate import Dataset

from .engine.twins import LADDER, find_twins
from .state import EngineState

POSITIVE_MIN_PCT = 90.0  # a positive pair passes if b is in a's top 10% of same-course pairs
NEGATIVE_MAX_PCT = 50.0  # a negative pair passes if it is less similar than the median pair


def pair_pct(state: EngineState, a: str, b: str) -> float | None:
    m = state.model
    if a not in m.index or b not in m.index:
        return None
    ia, ib = m.index[a], m.index[b]
    return m.similarity_pct(m.distance(ia, ib), m.courses[ia])


def sanity_results(state: EngineState, ds: Dataset) -> dict:
    out: dict = {"positive": [], "negative": [], "skipped": 0}
    if not ds.sanity:
        return out
    for kind, pairs in (("positive", ds.sanity.positive), ("negative", ds.sanity.negative)):
        for p in pairs:
            pct = pair_pct(state, p.a, p.b)
            if pct is None:
                out["skipped"] += 1
                continue
            ok = pct >= POSITIVE_MIN_PCT if kind == "positive" else pct < NEGATIVE_MAX_PCT
            out[kind].append({"a": p.a, "b": p.b, "pct": pct, "pass": ok, "why": p.why})
    return out


def attribution_error(state: EngineState) -> float:
    worst = 0.0
    for did, attr in state.attributions.items():
        v = state.model.V[state.model.index[did]]
        for k, dim in enumerate(DIM_IDS):
            worst = max(worst, abs(sum(c["value"] for c in attr.get(dim, [])) - v[k]))
    return worst


def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    ranks[order] = np.arange(len(x), dtype=float)
    for val in np.unique(x):  # average ranks for ties
        idx = np.where(x == val)[0]
        ranks[idx] = ranks[idx].mean()
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = _rank(np.asarray(x, float)), _rank(np.asarray(y, float))
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def _hist(values: np.ndarray, bins: int = 8, width: int = 28) -> list[str]:
    if len(values) == 0:
        return ["(no pairs)"]
    counts, edges = np.histogram(values, bins=bins)
    peak = counts.max() or 1
    return [f"{edges[i]:6.2f}-{edges[i + 1]:6.2f} | {'#' * int(width * c / peak):<{width}} {c}" for i, c in enumerate(counts)]


def render_report(state: EngineState, ds: Dataset) -> str:
    m = state.model
    L: list[str] = [f"# TasteSpace build report `{state.build_id}`", ""]
    courses = Counter(m.courses)
    L += [f"- contract {CONTRACT_VERSION} · tier `{state.data_tier}` · {len(m.ids)} dishes "
          f"({', '.join(f'{c}: {n}' for c, n in sorted(courses.items()))}) · {len(ds.ingredients)} ingredients", ""]

    if ds.warnings:
        L += ["## Data warnings", *[f"- {w}" for w in ds.warnings], ""]

    s = sanity_results(state, ds)
    pos_ok = sum(r["pass"] for r in s["positive"])
    neg_ok = sum(r["pass"] for r in s["negative"])
    L += ["## Sanity pairs (frozen - do not tune data to pass these)",
          f"positive {pos_ok}/{len(s['positive'])} (need >= {POSITIVE_MIN_PCT:g}th pct) · negative "
          f"{neg_ok}/{len(s['negative'])} (need < {NEGATIVE_MAX_PCT:g}th pct) · skipped {s['skipped']} (dishes not built yet)",
          "", "| kind | a | b | similarity pct | result |", "|---|---|---|---:|---|"]
    for kind in ("positive", "negative"):
        for r in s[kind]:
            L.append(f"| {kind} | {r['a']} | {r['b']} | {r['pct']:.1f} | {'PASS' if r['pass'] else 'FAIL'} |")
    L.append("")

    prov: Counter = Counter()
    for ing in ds.ingredients.values():
        for dim in ing.profile:
            pv = ing.value(dim)
            if pv is not None and pv.v > 0:
                prov[pv.src] += 1
    total = sum(prov.values()) or 1
    reviewed = sum(n for src, n in prov.items() if src not in ("seed_placeholder", "grok_draft", "fixture"))
    L += ["## Provenance of non-zero ingredient values",
          *[f"- `{src}`: {n} ({100 * n / total:.0f}%)" for src, n in prov.most_common()],
          f"- reviewed/grounded share: **{100 * reviewed / total:.0f}%**", ""]

    err = attribution_error(state)
    L += ["## Attribution check", f"max |sum(contributions) - dish value| = {err:.2e} -> "
          f"{'OK' if err < 1e-6 else 'BROKEN'}", ""]

    L += ["## Pair-distance distribution (weighted z-space)"]
    for course, arr in m.pair_dists.items():
        if len(arr):
            L += [f"**{course}** - {len(arr)} pairs, min {arr.min():.2f} · median {np.median(arr):.2f} · max {arr.max():.2f}",
                  "```", *_hist(arr), "```"]
    L.append("")

    from .engine.space import axis_labels
    labels = axis_labels(m.components)
    L += ["## PCA", *[f"- axis {i + 1}: {labels[i]} - {100 * m.explained[i]:.1f}% of variance" for i in range(3)],
          f"- cumulative: {100 * float(m.explained.sum()):.1f}%", ""]

    levels = Counter(find_twins(state, did, 3).relaxation_level for did in m.ids)
    L += ["## Twin relaxation usage (k=3, per dish)",
          *[f"- level {lvl} ({LADDER[lvl][1] if lvl < len(LADDER) else 'same-cuisine fallback'}): {n}"
            for lvl, n in sorted(levels.items())], ""]

    if ds.ratings and ds.ratings.pairs:
        xs, ys = [], []
        for p in ds.ratings.pairs:
            pct = pair_pct(state, p.a, p.b)
            if pct is not None and p.ratings:
                xs.append(pct)
                ys.append(sum(p.ratings.values()) / len(p.ratings))
        rho = spearman(xs, ys) if len(xs) >= 3 else float("nan")
        L += ["## Human ratings vs model", f"{len(xs)} rated pairs · Spearman rho = {rho:.2f}", ""]
    return "\n".join(L) + "\n"

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


def data_gaps(ds: Dataset, top: int = 15) -> tuple[list[dict], list[tuple[str, float]]]:
    """Empty-profile ingredients ranked by how much they would move dish vectors once filled
    (sum over dishes of recipe share x potency), plus dishes mostly made of them."""
    empty = {i for i, ing in ds.ingredients.items() if not ing.profile}
    usage: dict[str, dict] = {}
    blind: list[tuple[str, float]] = []
    for d in ds.dishes.values():
        total = sum(di.g for di in d.ingredients) or 1.0
        missing = 0.0
        for di in d.ingredients:
            if di.ing in empty:
                share = di.g / total
                u = usage.setdefault(di.ing, {"id": di.ing, "dishes": set(), "impact": 0.0})
                u["dishes"].add(d.id)
                u["impact"] += share * ds.ingredients[di.ing].potency
                missing += share
        if missing >= 0.5:
            blind.append((d.id, missing))
    ranked = sorted(usage.values(), key=lambda u: -u["impact"])[:top]
    return ([{"id": u["id"], "dishes": len(u["dishes"]), "impact": u["impact"]} for u in ranked],
            sorted(blind, key=lambda x: -x[1]))


AI_RATER_KEYS = {"claude", "grok", "gpt", "chatgpt", "gemini", "llm", "ai", "model"}


def is_ai_rater(key: str) -> bool:
    k = key.lower()
    return k in AI_RATER_KEYS or k.startswith(("ai_", "ai-", "llm_"))


def rater_rho(state: EngineState, ds: Dataset, keys: set[str] | None = None) -> tuple[int, float]:
    """Spearman rho between the engine percentile and the mean rating over `keys` (None = every key)."""
    xs, ys = [], []
    for p in (ds.ratings.pairs if ds.ratings else []):
        vals = [v for k, v in p.ratings.items() if keys is None or k in keys]
        pct = pair_pct(state, p.a, p.b)
        if pct is not None and vals:
            xs.append(pct)
            ys.append(sum(vals) / len(vals))
    return len(xs), (spearman(xs, ys) if len(xs) >= 3 else float("nan"))


def rater_panel(state: EngineState, ds: Dataset) -> dict:
    """One rho per rater key, labelled human/AI, plus separate human and AI panel means."""
    keys = sorted({k for p in (ds.ratings.pairs if ds.ratings else []) for k in p.ratings})
    human = {k for k in keys if not is_ai_rater(k)}
    ai = set(keys) - human
    rows = [{"rater": k, "kind": "AI" if k in ai else "human", **dict(zip(("n", "rho"), rater_rho(state, ds, {k}), strict=True))}
            for k in keys]
    return {"rows": rows, "human_keys": sorted(human), "ai_keys": sorted(ai),
            "human": rater_rho(state, ds, human) if human else (0, float("nan")),
            "ai": rater_rho(state, ds, ai) if ai else (0, float("nan"))}


def demo_candidates(state: EngineState, min_pct: float = 90.0, top: int = 10) -> list[dict]:
    """The strongest cross-macro-region twin pairs, straight from find_twins (not hand-picked).
    At H16 the team picks demo pairs from this list; it is also honest pitch evidence."""
    seen: set[frozenset] = set()
    out = []
    for did in state.model.ids:
        for t in find_twins(state, did, 3).twins:
            key = frozenset((did, t.dish_id))
            if t.cuisine_distance >= 1.0 and t.similarity_pct >= min_pct and key not in seen:
                seen.add(key)
                out.append({"a": did, "b": t.dish_id, "pct": t.similarity_pct, "shared": t.shared_dims[:4]})
    return sorted(out, key=lambda c: -c["pct"])[:top]


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

    gaps, blind = data_gaps(ds)
    n_empty = sum(1 for ing in ds.ingredients.values() if not ing.profile)
    L += ["## Data gaps (fill these first)",
          f"{n_empty} ingredient(s) have an empty profile, so they add nothing to any dish. "
          "Ranked by impact (sum over dishes of recipe share x potency):"]
    if gaps:
        L += ["", "| ingredient | used in dishes | impact |", "|---|---:|---:|",
              *[f"| {g['id']} | {g['dishes']} | {g['impact']:.2f} |" for g in gaps]]
    if blind:
        L += ["", f"Dishes where >= 50% of the recipe has no profile ({len(blind)}): "
              + ", ".join(f"{d} ({100 * s:.0f}%)" for d, s in blind)]
    L.append("")

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

    cands = demo_candidates(state)
    L += ["## Demo candidates (engine output, cross-region twins >= 90th pct)",
          "Pick demo pairs from here at H16; never hand-pick or tune data to create one."]
    if cands:
        L += ["", "| a | b | similarity pct | shared |", "|---|---|---:|---|",
              *[f"| {c['a']} | {c['b']} | {c['pct']:.1f} | {', '.join(c['shared'])} |" for c in cands]]
    else:
        L.append("(none yet)")
    L.append("")

    if ds.ratings and ds.ratings.pairs:
        panel = rater_panel(state, ds)
        L += ["## Rater panel vs model (Spearman rho: engine percentile vs mean rating)",
              "", "| rater | kind | pairs | rho |", "|---|---|---:|---:|",
              *[f"| {r['rater']} | {r['kind']} | {r['n']} | {r['rho']:.2f} |" for r in panel["rows"]], ""]
        hn, hrho = panel["human"]
        if panel["human_keys"]:
            L.append(f"- **human panel** ({', '.join(panel['human_keys'])}): {hn} pairs, rho = {hrho:.2f}")
        else:
            L.append("- **human panel: none.** Any rho above is an AI baseline, NOT human validation.")
        if panel["ai_keys"]:
            an, arho = panel["ai"]
            L.append(f"- AI raters ({', '.join(panel['ai_keys'])}): {an} pairs, rho = {arho:.2f}. A baseline only: "
                     "if the AI also wrote or reviewed the data, agreement is partly self-agreement.")
        L.append("")
    return "\n".join(L) + "\n"

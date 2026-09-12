"""Flavor Twins: high sensory similarity first, then maximize culinary (cuisine) distance.

Same-course candidates only. A small corpus can leave the strict band empty, so candidates are filled
from an adaptive ladder of percentile thresholds; the response reports the deepest level used.
"""

import numpy as np
from tastespace_contracts.api_models import DimDelta, TwinResult, TwinsResponse
from tastespace_contracts.taxonomy import DIM_IDS, cuisine_distance

from ..state import EngineState

# (minimum similarity percentile, note). Level index = relaxation_level.
LADDER: list[tuple[float, str]] = [
    (90.0, "twins are in the top 10% of similar dish pairs"),
    (80.0, "relaxed to the top 20% of similar pairs"),
    (70.0, "relaxed to the top 30% of similar pairs"),
    (0.0, "no close cross-cuisine match yet; showing the nearest other cuisines"),
]
SAME_CUISINE_NOTE = "no other cuisine in this course yet; showing same-cuisine neighbours"
EMPTY_COURSE_NOTE = "no other dishes in this course yet"


def shared_and_diffs(va: np.ndarray, vb: np.ndarray) -> tuple[list[str], list[DimDelta]]:
    score = np.minimum(va, vb) - np.abs(va - vb)
    shared = [DIM_IDS[k] for k in np.argsort(-score) if min(va[k], vb[k]) >= 0.2][:5]
    diffs = [DimDelta(dim=DIM_IDS[k], delta=round(float(vb[k] - va[k]), 4))
             for k in np.argsort(-np.abs(vb - va))[:3] if abs(vb[k] - va[k]) > 1e-6]
    return shared, diffs  # type: ignore[return-value]


def find_twins(state: EngineState, dish_id: str, k: int = 3) -> TwinsResponse:
    m = state.model
    i = m.require(dish_id)
    course, cuisine = m.courses[i], m.cuisines[i]
    d = m.dists_to(m.Z[i])
    cands = [(j, float(d[j]), m.similarity_pct(float(d[j]), course), cuisine_distance(cuisine, m.cuisines[j]))
             for j in range(len(m.ids)) if j != i and m.courses[j] == course]
    cross = [c for c in cands if c[3] > 0]

    picked: list[tuple[int, float, float, float]] = []
    level, note = 0, LADDER[0][1]
    if cross:
        for lvl, (threshold, lvl_note) in enumerate(LADDER):
            taken = {p[0] for p in picked}
            pool = sorted((c for c in cross if c[2] >= threshold and c[0] not in taken), key=lambda c: (-c[3], -c[2]))
            if pool:
                picked += pool[: k - len(picked)]
                level, note = lvl, lvl_note
            if len(picked) >= k:
                break
    else:
        picked = sorted(cands, key=lambda c: -c[2])[:k]
        level, note = len(LADDER), SAME_CUISINE_NOTE if cands else EMPTY_COURSE_NOTE

    twins = []
    for j, dist, pct, cd in picked:
        shared, diffs = shared_and_diffs(m.V[i], m.V[j])
        twins.append(TwinResult(dish_id=m.ids[j], similarity_pct=round(pct, 1), distance=round(dist, 4),
                                cuisine_distance=cd, shared_dims=shared, diffs=diffs))  # type: ignore[arg-type]
    return TwinsResponse(source_id=dish_id, relaxation_level=level, relaxation_note=note, twins=twins)

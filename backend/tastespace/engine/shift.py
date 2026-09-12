"""Taste Shift: move from a dish through z-space and find what lives there.

target = z_A + delta (sigma units). Candidates stay in A's course and must move in the requested
direction on the touched dims; untouched dims keep their full weight in the distance, so the result
stays close to what you liked about A. Adaptive ladder: all touched dims -> majority -> any.
"""

import numpy as np
from tastespace_contracts.api_models import ShiftRequest, ShiftResponse, ShiftResult
from tastespace_contracts.taxonomy import DIM_IDS

from ..state import EngineState
from .transforms import DIM_INDEX

MIN_DELTA = 0.05
LADDER: list[tuple[str, str]] = [
    ("all", "every requested dimension moves the right way"),
    ("majority", "relaxed: most requested dimensions move the right way"),
    ("any", "relaxed: nearest to the target regardless of direction"),
]
NO_SHIFT_NOTE = "no shift requested: nearest neighbours of the dish"


def shift(state: EngineState, req: ShiftRequest) -> ShiftResponse:
    m = state.model
    i = m.require(req.dish_id)
    course = m.courses[i]
    delta = np.zeros(len(DIM_IDS))
    for dim, v in req.deltas.items():
        delta[DIM_INDEX[dim]] = v
    touched = [k for k in range(len(DIM_IDS)) if abs(delta[k]) >= MIN_DELTA]
    target = m.Z[i] + delta
    d = m.dists_to(target)
    cands = [j for j in range(len(m.ids)) if j != i and m.courses[j] == course]

    def n_right(j: int) -> int:
        return sum(1 for k in touched if (m.Z[j, k] - m.Z[i, k]) * delta[k] > 0)

    picked: list[int] = []
    level, note = 0, NO_SHIFT_NOTE
    if not touched:
        picked = sorted(cands, key=lambda j: d[j])[: req.k]
    else:
        for lvl, (mode, lvl_note) in enumerate(LADDER):
            need = len(touched) if mode == "all" else (len(touched) // 2 + 1 if mode == "majority" else 0)
            pool = sorted((j for j in cands if j not in picked and n_right(j) >= need), key=lambda j: d[j])
            if pool:
                picked += pool[: req.k - len(picked)]
                level, note = lvl, lvl_note
            if len(picked) >= req.k:
                break

    results = [ShiftResult(dish_id=m.ids[j], similarity_pct=round(m.similarity_pct(float(d[j]), course), 1),
                           distance=round(float(d[j]), 4),
                           moved={DIM_IDS[k]: round(float(m.V[j, k] - m.V[i, k]), 4) for k in touched})  # type: ignore[misc]
               for j in picked]
    return ShiftResponse(source_id=req.dish_id,
                         target_z={d_: round(float(target[k]), 4) for k, d_ in enumerate(DIM_IDS)},  # type: ignore[misc]
                         target_xyz=tuple(round(float(x), 4) for x in m.project_z(target)),  # type: ignore[arg-type]
                         relaxation_level=level, relaxation_note=note, results=results)

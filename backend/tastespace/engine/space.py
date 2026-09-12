"""Weighted z-space, percentile similarity and the PCA-3D projection.

Distance  : sqrt(sum_k w_k (z_ak - z_bk)^2), z = (v - mean) / std over the built dishes.
Similarity: PERCENTILE = % of same-course dish pairs that are farther apart (never a cosine).
Projection: PCA on weighted z-scores; mean/std/components/scale are stored so any new vector
            (recipe, shift target) lands in the same 3D space, moving linearly with its z-scores.
"""

from dataclasses import dataclass, field

import numpy as np
from tastespace_contracts.taxonomy import DIM_IDS

from ..errors import TasteSpaceError

N = len(DIM_IDS)

# P2: tune per-dimension weights here (1.0 = neutral). They scale squared z-distance and PCA.
DEFAULT_WEIGHTS: dict[str, float] = {d: 1.0 for d in DIM_IDS}
DISPLAY_RADIUS = 10.0


@dataclass
class SpaceModel:
    ids: list[str]
    courses: list[str]
    cuisines: list[str]
    V: np.ndarray  # n x N dish vectors in [0,1]
    s: np.ndarray  # calibration scales used by aggregate.finalize
    mean: np.ndarray
    std: np.ndarray
    weights: np.ndarray
    components: np.ndarray  # 3 x N
    explained: np.ndarray  # 3
    scale: float
    pair_dists: dict[str, np.ndarray]  # course -> sorted pairwise distances
    index: dict[str, int] = field(init=False)
    Z: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.index = {d: i for i, d in enumerate(self.ids)}
        self.Z = (self.V - self.mean) / self.std

    def require(self, dish_id: str) -> int:
        if dish_id not in self.index:
            raise TasteSpaceError("not_found", f"unknown dish '{dish_id}'", {"dish_id": dish_id})
        return self.index[dish_id]

    def z(self, v: np.ndarray) -> np.ndarray:
        return (np.asarray(v, dtype=float) - self.mean) / self.std

    def project_z(self, z: np.ndarray) -> np.ndarray:
        return (np.asarray(z, dtype=float) * np.sqrt(self.weights)) @ self.components.T * self.scale

    def project(self, v: np.ndarray) -> np.ndarray:
        return self.project_z(self.z(v))

    def dists_to(self, z: np.ndarray) -> np.ndarray:
        return np.sqrt((((self.Z - np.asarray(z)) ** 2) * self.weights).sum(axis=1))

    def distance(self, i: int, j: int) -> float:
        return float(np.sqrt((((self.Z[i] - self.Z[j]) ** 2) * self.weights).sum()))

    def similarity_pct(self, d: float, course: str) -> float:
        arr = self.pair_dists.get(course)
        if arr is None or len(arr) == 0:
            return 100.0
        farther = len(arr) - np.searchsorted(arr, d, side="right")
        return float(100.0 * farther / len(arr))


def _pairwise(Z: np.ndarray, w: np.ndarray, idx: list[int]) -> np.ndarray:
    out = []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            out.append(np.sqrt((((Z[idx[a]] - Z[idx[b]]) ** 2) * w).sum()))
    return np.sort(np.array(out, dtype=float))


def fit_space(ids: list[str], courses: list[str], cuisines: list[str], V: np.ndarray, s: np.ndarray,
              weights: dict[str, float] | None = None) -> SpaceModel:
    V = np.asarray(V, dtype=float)
    mean = V.mean(axis=0)
    std = V.std(axis=0)
    std = np.where(std < 1e-6, 1.0, std)
    wmap = weights or DEFAULT_WEIGHTS
    w = np.array([wmap.get(d, 1.0) for d in DIM_IDS], dtype=float)
    Zw = (V - mean) / std * np.sqrt(w)

    comps = np.zeros((3, N))
    explained = np.zeros(3)
    if len(ids) >= 2:
        _, S, Vt = np.linalg.svd(Zw - Zw.mean(axis=0), full_matrices=False)
        var = S ** 2
        k = min(3, len(Vt))
        comps[:k] = Vt[:k]
        if var.sum() > 0:
            explained[:k] = (var / var.sum())[:k]
    for r in range(3):  # deterministic signs: largest |loading| positive
        if comps[r].any() and comps[r][np.argmax(np.abs(comps[r]))] < 0:
            comps[r] = -comps[r]
    proj = Zw @ comps.T
    peak = float(np.abs(proj).max()) if proj.size else 0.0
    scale = DISPLAY_RADIUS / peak if peak > 1e-9 else 1.0

    Z = (V - mean) / std
    pair_dists = {c: _pairwise(Z, w, [i for i, cc in enumerate(courses) if cc == c]) for c in sorted(set(courses))}
    return SpaceModel(ids=list(ids), courses=list(courses), cuisines=list(cuisines), V=V, s=np.asarray(s, float),
                      mean=mean, std=std, weights=w, components=comps, explained=explained, scale=scale,
                      pair_dists=pair_dists)


def axis_labels(components: np.ndarray) -> list[str]:
    labels = []
    for row in components:
        if not row.any():
            labels.append("(unused)")
            continue
        labels.append(f"{DIM_IDS[int(np.argmin(row))]} ↔ {DIM_IDS[int(np.argmax(row))]}")
    return labels

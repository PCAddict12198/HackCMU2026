"""Per-ingredient preparation transforms: r' = clip(r * scale_p + delta_p, 0, 1), in listed order."""

import numpy as np
from tastespace_contracts.data_models import Process
from tastespace_contracts.taxonomy import DIM_IDS

N = len(DIM_IDS)
DIM_INDEX = {d: i for i, d in enumerate(DIM_IDS)}


def process_arrays(process: Process) -> tuple[np.ndarray, np.ndarray]:
    scale = np.ones(N)
    delta = np.zeros(N)
    for dim, v in process.scale.items():
        scale[DIM_INDEX[dim]] = v
    for dim, v in process.delta.items():
        delta[DIM_INDEX[dim]] = v
    return scale, delta


def apply_processes(r: np.ndarray, process_ids: list[str], processes: dict[str, Process]) -> np.ndarray:
    out = np.asarray(r, dtype=float).copy()
    for pid in process_ids:
        scale, delta = process_arrays(processes[pid])
        out = np.clip(out * scale + delta, 0.0, 1.0)
    return out

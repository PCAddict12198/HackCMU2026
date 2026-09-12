"""Explain a pair: per-dim values, each dim's share of the distance, and ingredient attributions."""

from tastespace_contracts.api_models import DimComparison, ExplainResponse, PairAttributions
from tastespace_contracts.taxonomy import DIM_IDS

from ..state import EngineState


def explain(state: EngineState, a: str, b: str) -> ExplainResponse:
    m = state.model
    ia, ib = m.require(a), m.require(b)
    diff2 = m.weights * (m.Z[ia] - m.Z[ib]) ** 2
    total = float(diff2.sum())
    dims = [DimComparison(dim=dim, a=round(float(m.V[ia, k]), 4), b=round(float(m.V[ib, k]), 4),  # type: ignore[arg-type]
                          distance_share=round(float(diff2[k] / total), 4) if total > 0 else 0.0)
            for k, dim in enumerate(DIM_IDS)]
    dist = total ** 0.5
    return ExplainResponse(a=a, b=b, similarity_pct=round(m.similarity_pct(dist, m.courses[ia]), 1),
                           distance=round(dist, 4), dims=dims,
                           attributions=PairAttributions(a=state.attributions[a], b=state.attributions[b]))  # type: ignore[arg-type]

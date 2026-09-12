"""EngineState: everything the API needs. build.py creates it and saves build/tastespace.json
(internal artifact format - NOT a contract; the contract is SpaceResponse etc.). OWNER: engine (P2)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from tastespace_contracts import CONTRACT_VERSION
from tastespace_contracts.api_models import CuisineMeta, DimMeta, DishPoint, PcaInfo, SpaceMeta, SpaceResponse
from tastespace_contracts.taxonomy import DIM_IDS

from .engine.space import SpaceModel, axis_labels

ARTIFACT_VERSION = 1


@dataclass
class DishMeta:
    id: str
    name: str
    cuisine: str
    course: str
    format: str
    tier: str
    confidence: str
    blurb: str = ""


@dataclass
class EngineState:
    build_id: str
    data_tier: str
    model: SpaceModel
    dishes: dict[str, DishMeta]
    attributions: dict[str, dict[str, list[dict]]]
    dims: list[dict]
    cuisines: list[dict]
    warnings: list[str] = field(default_factory=list)
    _space: SpaceResponse | None = field(default=None, repr=False)

    @staticmethod
    def vector_dict(v: np.ndarray) -> dict[str, float]:
        return {d: round(float(v[k]), 6) for k, d in enumerate(DIM_IDS)}

    def space_response(self) -> SpaceResponse:
        if self._space is None:
            m = self.model
            points = []
            for i, did in enumerate(m.ids):
                meta = self.dishes[did]
                xyz = m.project(m.V[i])
                points.append(DishPoint(id=did, name=meta.name, cuisine=meta.cuisine, course=meta.course,
                                        format=meta.format, tier=meta.tier, confidence=meta.confidence,
                                        blurb=meta.blurb, xyz=tuple(round(float(x), 4) for x in xyz),
                                        vector=self.vector_dict(m.V[i])))
            pca = PcaInfo(mean=m.mean.tolist(), std=m.std.tolist(), weights=m.weights.tolist(),
                          components=m.components.tolist(), explained_variance=m.explained.tolist(),
                          axis_labels=axis_labels(m.components), scale=m.scale)
            meta = SpaceMeta(build_id=self.build_id, data_tier=self.data_tier, n_dishes=len(m.ids),  # type: ignore[arg-type]
                             contract_version=CONTRACT_VERSION, dim_order=list(DIM_IDS), warnings=self.warnings)
            self._space = SpaceResponse(dims=[DimMeta(**d) for d in self.dims],
                                        cuisines=[CuisineMeta(**c) for c in self.cuisines],
                                        dishes=points, pca=pca, meta=meta)
        return self._space

    # --- artifact I/O ---------------------------------------------------------------------------------
    def to_artifact(self) -> dict:
        m = self.model
        return {
            "artifact_version": ARTIFACT_VERSION,
            "build_id": self.build_id,
            "data_tier": self.data_tier,
            "warnings": self.warnings,
            "dims": self.dims,
            "cuisines": self.cuisines,
            "dishes": {k: asdict(v) for k, v in self.dishes.items()},
            "attributions": self.attributions,
            "model": {
                "ids": m.ids, "courses": m.courses, "cuisines": m.cuisines,
                "V": m.V.tolist(), "s": m.s.tolist(), "mean": m.mean.tolist(), "std": m.std.tolist(),
                "weights": m.weights.tolist(), "components": m.components.tolist(),
                "explained": m.explained.tolist(), "scale": m.scale,
                "pair_dists": {c: a.tolist() for c, a in m.pair_dists.items()},
            },
        }

    @classmethod
    def from_artifact(cls, data: dict) -> EngineState:
        if data.get("artifact_version") != ARTIFACT_VERSION:
            raise ValueError(f"artifact version {data.get('artifact_version')} != {ARTIFACT_VERSION}; run make build")
        md = data["model"]
        arr = lambda k: np.asarray(md[k], dtype=float)  # noqa: E731
        model = SpaceModel(ids=md["ids"], courses=md["courses"], cuisines=md["cuisines"], V=arr("V"), s=arr("s"),
                           mean=arr("mean"), std=arr("std"), weights=arr("weights"),
                           components=arr("components"), explained=arr("explained"), scale=float(md["scale"]),
                           pair_dists={c: np.asarray(v, dtype=float) for c, v in md["pair_dists"].items()})
        return cls(build_id=data["build_id"], data_tier=data["data_tier"], model=model,
                   dishes={k: DishMeta(**v) for k, v in data["dishes"].items()},
                   attributions=data["attributions"], dims=data["dims"], cuisines=data["cuisines"],
                   warnings=data.get("warnings", []))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_artifact()))

    @classmethod
    def load(cls, path: Path) -> EngineState:
        return cls.from_artifact(json.loads(path.read_text()))

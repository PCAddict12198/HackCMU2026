"""Request/response models for every endpoint. FastAPI turns these into contracts/openapi.json,
which openapi-typescript turns into contracts/generated/api.d.ts for the web app.

Units: dish vectors are in [0,1] per dim; shift deltas and target_z are in sigma units (z-scores);
similarity_pct is a PERCENTILE ("closer than N% of same-course dish pairs"), never a cosine.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .taxonomy import (
    Confidence,
    Course,
    CuisineId,
    DataTier,
    DimGroup,
    DimId,
    FormatId,
    MacroId,
    Panel,
    ProcessId,
    RegionId,
    Source,
    Tier,
    ToolName,
)
from .ui_actions import ShiftDelta, UiAction

Vec3 = tuple[float, float, float]
Pct = Annotated[float, Field(ge=0.0, le=100.0)]


class _M(BaseModel):
    # serialization-mode schemas mark defaulted fields as required: responses always carry every field
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


# --- shared pieces ------------------------------------------------------------------------------------
class DimMeta(_M):
    id: DimId
    group: DimGroup
    label: str
    low_label: str
    high_label: str


class CuisineMeta(_M):
    id: CuisineId
    name: str
    region: RegionId
    macro: MacroId


class DishPoint(_M):
    id: str
    name: str
    cuisine: CuisineId
    course: Course
    format: FormatId
    tier: Tier
    confidence: Confidence
    blurb: str = ""
    xyz: Vec3
    vector: dict[DimId, float]


class Contribution(_M):
    kind: Literal["ingredient", "format"]
    id: str = Field(description="ingredient id or format id")
    value: float = Field(description="share of the final 0..1 dim value; contributions sum to it")
    src: Source | None = Field(None, description="provenance of the ingredient value (None = derived)")
    process: list[ProcessId] = []


DishAttribution = dict[DimId, list[Contribution]]


class DimDelta(_M):
    dim: DimId
    delta: float


class NeighborResult(_M):
    dish_id: str
    similarity_pct: Pct
    distance: float


# --- GET /api/health ------------------------------------------------------------------------------------
class HealthResponse(_M):
    status: Literal["ok"] = "ok"
    build_ready: bool
    data_ready: bool
    grok_configured: bool
    contract_version: str
    build_id: str | None = None


# --- GET /api/space -------------------------------------------------------------------------------------
class PcaInfo(_M):
    mean: list[float]
    std: list[float]
    weights: list[float]
    components: list[list[float]] = Field(description="3 x N_DIMS, applied to weighted z-scores")
    explained_variance: list[float]
    axis_labels: list[str]
    scale: float = Field(description="display scale applied after projection")


class SpaceMeta(_M):
    build_id: str
    data_tier: DataTier
    n_dishes: int
    contract_version: str
    dim_order: list[DimId]
    warnings: list[str] = []


class SpaceResponse(_M):
    dims: list[DimMeta]
    cuisines: list[CuisineMeta]
    dishes: list[DishPoint]
    pca: PcaInfo
    meta: SpaceMeta


# --- GET /api/twins -------------------------------------------------------------------------------------
class TwinResult(NeighborResult):
    cuisine_distance: float
    shared_dims: list[DimId] = Field(max_length=5)
    diffs: list[DimDelta] = Field(max_length=3, description="twin minus source, in 0..1 units")


class TwinsResponse(_M):
    source_id: str
    relaxation_level: int = Field(ge=0, description="0 = strictest threshold met")
    relaxation_note: str
    twins: list[TwinResult]


# --- POST /api/shift ------------------------------------------------------------------------------------
class ShiftRequest(_M):
    dish_id: str
    deltas: dict[DimId, ShiftDelta] = Field(default_factory=dict)
    k: int = Field(5, ge=1, le=20)


class ShiftResult(NeighborResult):
    moved: dict[DimId, float] = Field(description="candidate minus source on touched dims, 0..1 units")


class ShiftResponse(_M):
    source_id: str
    target_z: dict[DimId, float]
    target_xyz: Vec3
    relaxation_level: int = Field(ge=0)
    relaxation_note: str
    results: list[ShiftResult]


# --- GET /api/explain -----------------------------------------------------------------------------------
class DimComparison(_M):
    dim: DimId
    a: float
    b: float
    distance_share: float = Field(description="fraction of the pair's squared distance from this dim")


class PairAttributions(_M):
    a: DishAttribution
    b: DishAttribution


class ExplainResponse(_M):
    a: str
    b: str
    similarity_pct: Pct
    distance: float
    dims: list[DimComparison]
    attributions: PairAttributions


# --- POST /api/recipe -----------------------------------------------------------------------------------
class RecipeRequest(_M):
    text: str = Field(min_length=1, max_length=5000)
    name: str | None = None
    format: FormatId | None = None
    course: Course | None = None


class RecipeLine(_M):
    raw: str
    status: Literal["matched", "fuzzy", "grok_mapped", "unmatched"]
    ingredient_id: str | None = None
    grams: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    process: list[ProcessId] = []
    note: str | None = None


class Coverage(_M):
    matched: int
    total: int


class RecipeResponse(_M):
    name: str
    course: Course
    lines: list[RecipeLine]
    coverage: Coverage
    used_grok: bool
    vector: dict[DimId, float]
    xyz: Vec3
    neighbors: list[NeighborResult]
    attributions: DishAttribution


# --- POST /api/ask --------------------------------------------------------------------------------------
class ChatMessage(_M):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class AskContext(_M):
    selected_dish_id: str | None = None
    active_panel: Panel | None = None


class AskRequest(_M):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    context: AskContext = Field(default_factory=AskContext)


class ToolCallTrace(_M):
    call_id: str
    tool: ToolName
    args: dict[str, Any]
    ok: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class AskResponse(_M):
    reply: str
    grounded: bool = Field(description="false = reply replaced by a template because it cited numbers "
                                        "the engine did not return")
    ui_actions: list[UiAction]
    tool_trace: list[ToolCallTrace]

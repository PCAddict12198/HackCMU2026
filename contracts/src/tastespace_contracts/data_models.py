"""Schemas for everything under data/. P1 validates against these; the engine loads through them.

Profile shorthand: inside an ingredients file with `default_src: <Source>`, a profile value may be a
bare number (e.g. `salty: 0.9`) and is expanded to `{v: 0.9, src: <default_src>}`. Explicit objects
(`salty: {v: 0.9, src: usda, note: "..."}`) always win. Every value therefore carries provenance.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .taxonomy import (
    CUISINE_REGION,
    DIM_GROUP,
    REGION_MACRO,
    SLUG_PATTERN,
    Confidence,
    Course,
    CuisineId,
    DimGroup,
    DimId,
    FormatId,
    IngredientCategory,
    MacroId,
    ProcessId,
    RegionId,
    Source,
    Tier,
)

Slug = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]
Unit01 = Annotated[float, Field(ge=0.0, le=1.0)]
NonNeg = Annotated[float, Field(ge=0.0)]
Delta1 = Annotated[float, Field(ge=-1.0, le=1.0)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- dims / cuisines ----------------------------------------------------------------------------------
class DimInfo(Strict):
    id: DimId
    group: DimGroup
    label: str
    low_label: str
    high_label: str
    description: str = ""

    @model_validator(mode="after")
    def _group_matches(self) -> "DimInfo":
        if DIM_GROUP[self.id] != self.group:
            raise ValueError(f"dim {self.id} must be in group {DIM_GROUP[self.id]}")
        return self


class DimsFile(Strict):
    dims: list[DimInfo]


class CuisineInfo(Strict):
    id: CuisineId
    name: str
    region: RegionId
    macro: MacroId

    @model_validator(mode="after")
    def _hierarchy_matches(self) -> "CuisineInfo":
        if CUISINE_REGION[self.id] != self.region or REGION_MACRO[self.region] != self.macro:
            raise ValueError(f"cuisine {self.id} must be region={CUISINE_REGION[self.id]}, "
                             f"macro={REGION_MACRO[CUISINE_REGION[self.id]]}")
        return self


class CuisinesFile(Strict):
    cuisines: list[CuisineInfo]


# --- ingredients ----------------------------------------------------------------------------------------
class ProfileValue(Strict):
    v: Unit01
    src: Source
    note: str | None = None


class Ingredient(Strict):
    id: Slug
    name: str
    category: IngredientCategory
    aliases: list[str] = []
    potency: float = Field(1.0, ge=0.1, le=10.0, description="How strongly it carries when diluted.")
    unit_weight_g: float | None = Field(None, gt=0, description="Grams per piece, for '2 eggs'.")
    density_g_per_ml: float | None = Field(None, gt=0, description="For volume units; default 1.0.")
    profile: dict[DimId, ProfileValue | Unit01] = Field(
        default_factory=dict, description="Neat intensity per dim in [0,1]; omitted dims are 0.")
    reviewed_by: str | None = None

    def value(self, dim: str) -> ProfileValue | None:
        pv = self.profile.get(dim)  # type: ignore[call-overload]
        assert pv is None or isinstance(pv, ProfileValue), "IngredientFile expands shorthand values"
        return pv


class IngredientFile(Strict):
    default_src: Source | None = None
    ingredients: list[Ingredient]

    @model_validator(mode="after")
    def _expand_shorthand(self) -> "IngredientFile":
        for ing in self.ingredients:
            for dim, val in list(ing.profile.items()):
                if isinstance(val, ProfileValue):
                    continue
                if self.default_src is None:
                    raise ValueError(f"{ing.id}.{dim}: bare number needs a file-level default_src")
                ing.profile[dim] = ProfileValue(v=val, src=self.default_src)
        return self


# --- processes / formats --------------------------------------------------------------------------------
class Process(Strict):
    id: ProcessId
    scale: dict[DimId, NonNeg] = Field(default_factory=dict, description="Multiplier (default 1).")
    delta: dict[DimId, Delta1] = Field(default_factory=dict, description="Added after scaling (default 0).")
    note: str = ""


class ProcessesFile(Strict):
    processes: list[Process]


class Format(Strict):
    id: FormatId
    f: dict[DimId, Unit01] = Field(default_factory=dict, description="Dish-level contribution (noisy-OR).")
    note: str = ""


class FormatsFile(Strict):
    formats: list[Format]


# --- dishes ---------------------------------------------------------------------------------------------
class DishIngredient(Strict):
    ing: Slug
    g: float = Field(gt=0, description="Grams in the canonical recipe (grams only).")
    process: list[ProcessId] = Field(default_factory=list, description="Applied in order.")
    note: str | None = None


class Dish(Strict):
    id: Slug
    name: str
    cuisine: CuisineId
    course: Course
    format: FormatId
    tier: Tier = "core"
    confidence: Confidence = "draft"
    blurb: str = ""
    recipe_basis: str = Field("", description="Where the canonical recipe comes from.")
    ingredients: list[DishIngredient] = Field(min_length=1)


class DishesFile(Strict):
    dishes: list[Dish]


class DishManifest(Strict):
    core: list[Slug]


# --- lexicon (recipe parsing) ---------------------------------------------------------------------------
class UnitDef(Strict):
    kind: Literal["mass", "volume", "count"]
    factor: float = Field(gt=0, description="grams (mass), millilitres (volume), pieces (count)")
    aliases: list[str] = []


class UnitsFile(Strict):
    units: dict[str, UnitDef]


class AliasesFile(Strict):
    aliases: dict[str, Slug]


# --- validation sets ------------------------------------------------------------------------------------
class SanityPair(Strict):
    a: Slug
    b: Slug
    why: str


class SanityPairs(Strict):
    positive: list[SanityPair]
    negative: list[SanityPair]


class RatingPair(Strict):
    a: Slug
    b: Slug
    ratings: dict[str, Annotated[int, Field(ge=1, le=5)]] = Field(default_factory=dict,
                                                                  description="rater -> 1..5")


class RatingsFile(Strict):
    pairs: list[RatingPair] = []


DATA_FILE_MODELS: dict[str, type[BaseModel]] = {
    "dims": DimsFile,
    "cuisines": CuisinesFile,
    "ingredients": IngredientFile,
    "processes": ProcessesFile,
    "formats": FormatsFile,
    "dishes": DishesFile,
    "manifest": DishManifest,
    "units": UnitsFile,
    "aliases": AliasesFile,
    "sanity_pairs": SanityPairs,
    "ratings": RatingsFile,
}

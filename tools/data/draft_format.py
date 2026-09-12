"""Shared draft-file format for tools/data (usda_fill, grok_draft_ingredients, promote_draft).
OWNER: data (P1). Drafts live in data/drafts/ and are NEVER loaded by the engine."""

from typing import Literal

from pydantic import BaseModel, ConfigDict
from tastespace_contracts.data_models import ProfileValue, Slug
from tastespace_contracts.taxonomy import DimId, IngredientCategory


class DraftIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Slug
    name: str | None = None  # required for NEW ingredients
    category: IngredientCategory | None = None  # required for NEW ingredients
    potency: float | None = None
    profile: dict[DimId, ProfileValue] = {}
    note: str | None = None  # rationale / USDA match, for the reviewer


class DraftFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["usda", "grok_draft", "team"]
    generated: str
    ingredients: list[DraftIngredient]

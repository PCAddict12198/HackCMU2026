"""UI actions returned by /api/ask. The web app applies them with one reducer.

Rules (enforced server-side in backend/tastespace/grok): actions carry IDs only, never scores; every
referenced dish_id must exist AND must have appeared in that turn's tool_trace. The UI refetches all
numbers from the engine. Unknown action types must be ignored by the UI (forward compatible).
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from .taxonomy import DimId, Panel

ShiftDelta = Annotated[float, Field(ge=-2.0, le=2.0, description="sigma units")]


class _Action(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class SelectDish(_Action):
    type: Literal["select_dish"] = "select_dish"
    dish_id: str


class ShowTwins(_Action):
    type: Literal["show_twins"] = "show_twins"
    dish_id: str
    highlight_dish_id: str | None = None


class SetShift(_Action):
    type: Literal["set_shift"] = "set_shift"
    dish_id: str
    deltas: dict[DimId, ShiftDelta]


class ExplainPair(_Action):
    type: Literal["explain_pair"] = "explain_pair"
    a: str
    b: str


class OpenPanel(_Action):
    type: Literal["open_panel"] = "open_panel"
    panel: Panel


class HighlightDishes(_Action):
    type: Literal["highlight_dishes"] = "highlight_dishes"
    dish_ids: list[str] = Field(min_length=1, max_length=10)


UiAction = Annotated[
    Union[SelectDish, ShowTwins, SetShift, ExplainPair, OpenPanel, HighlightDishes],
    Field(discriminator="type"),
]


def referenced_dish_ids(action: BaseModel) -> list[str]:
    """Every dish id an action points at (used by the grounding check)."""
    if isinstance(action, (SelectDish, SetShift)):
        return [action.dish_id]
    if isinstance(action, ShowTwins):
        return [action.dish_id] + ([action.highlight_dish_id] if action.highlight_dish_id else [])
    if isinstance(action, ExplainPair):
        return [action.a, action.b]
    if isinstance(action, HighlightDishes):
        return list(action.dish_ids)
    return []

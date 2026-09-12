"""Grok maps recipe ingredient names our parser could not match onto the CLOSED list of ontology ids.

Structured output: the response schema's `ingredient_id` is an enum of our ids plus "none", so Grok
cannot invent ingredients. Anything it maps is labelled `grok_mapped` in the recipe response.
"""

import json
from typing import Literal

from pydantic import BaseModel, create_model
from tastespace_contracts.data_models import Ingredient

from ..errors import TasteSpaceError
from .client import ChatFactory
from .errors import provider_error_message

SYSTEM = ("You map free-text recipe ingredient names to the closest ingredient id from a fixed list. "
          "Prefer the ingredient that would taste most similar. Answer 'none' if nothing is reasonably close. "
          "Never invent ids.")


def build_shape(ids: list[str]) -> type[BaseModel]:
    id_enum = Literal[tuple(sorted(ids)) + ("none",)]  # type: ignore[valid-type]
    item = create_model("IngredientMapping", name=(str, ...), ingredient_id=(id_enum, ...))
    return create_model("IngredientMappings", items=(list[item], ...))  # type: ignore[valid-type]


def map_ingredients(names: list[str], ingredients: dict[str, Ingredient], chat_factory: ChatFactory) -> dict[str, str]:
    if not names:
        return {}
    shape = build_shape(list(ingredients))
    chat = chat_factory(SYSTEM, None)
    catalog = "\n".join(f"{i.id}: {i.name}" for i in ingredients.values())
    chat.add_user(f"Ingredient ids:\n{catalog}\n\nMap each of these recipe ingredient names: {json.dumps(names)}")
    try:
        out = chat.parse(shape)
    except Exception as exc:
        reason = provider_error_message(exc)
        raise TasteSpaceError("grok_failed", f"Grok ingredient mapping failed: {reason}", {"reason": reason}) from exc
    wanted = set(names)
    return {it.name: it.ingredient_id for it in out.items  # type: ignore[attr-defined]
            if it.name in wanted and it.ingredient_id != "none" and it.ingredient_id in ingredients}

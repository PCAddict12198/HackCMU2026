"""Frozen identifiers shared by data, engine, API and web.

Everything here is exported to OpenAPI and becomes a TypeScript union, so adding a value is a
contract change (minor version bump) and renaming/removing one is breaking.
"""

from typing import Literal, get_args

# --- Sensory dimensions (order is canonical: vectors are always laid out in this order) ---------
DimId = Literal[
    # taste
    "sweet", "salty", "sour", "bitter", "umami",
    # aroma / flavor character
    "spicy", "smoky", "roasted", "fermented", "herbal", "fruity", "earthy",
    # mouthfeel
    "rich", "creamy", "crispy", "chewy", "brothy",
]
DIM_IDS: tuple[str, ...] = get_args(DimId)
N_DIMS = len(DIM_IDS)

DimGroup = Literal["taste", "aroma", "mouthfeel"]
DIM_GROUP: dict[str, str] = {
    **{d: "taste" for d in ("sweet", "salty", "sour", "bitter", "umami")},
    **{d: "aroma" for d in ("spicy", "smoky", "roasted", "fermented", "herbal", "fruity", "earthy")},
    **{d: "mouthfeel" for d in ("rich", "creamy", "crispy", "chewy", "brothy")},
}

# --- Dish classification --------------------------------------------------------------------------
Course = Literal["savory", "dessert"]
COURSES: tuple[str, ...] = get_args(Course)

FormatId = Literal[
    "soup", "noodles", "rice_dish", "stew_braise", "fried", "grilled_roasted", "raw_salad",
    "bread_sandwich", "dumpling", "baked_sweet", "custard_creamy", "frozen",
]
FORMAT_IDS: tuple[str, ...] = get_args(FormatId)

ProcessId = Literal[
    "raw", "boiled", "simmered", "braised", "steamed", "grilled", "roasted", "fried", "deep_fried",
    "smoked", "caramelized", "toasted", "fermented", "pickled", "cured",
]
PROCESS_IDS: tuple[str, ...] = get_args(ProcessId)

Tier = Literal["core", "extended"]
Confidence = Literal["reviewed", "draft"]
DataTier = Literal["core", "all"]

# --- Cuisines and the region hierarchy used for culinary distance ----------------------------------
CuisineId = Literal[
    "japanese", "chinese", "korean", "thai", "vietnamese", "indian", "levantine", "italian", "french",
    "mexican",
]
CUISINE_IDS: tuple[str, ...] = get_args(CuisineId)

RegionId = Literal["east_asia", "southeast_asia", "south_asia", "middle_east", "europe", "americas"]
MacroId = Literal["asia", "europe_mena", "americas"]

CUISINE_REGION: dict[str, str] = {
    "japanese": "east_asia", "chinese": "east_asia", "korean": "east_asia",
    "thai": "southeast_asia", "vietnamese": "southeast_asia",
    "indian": "south_asia",
    "levantine": "middle_east",
    "italian": "europe", "french": "europe",
    "mexican": "americas",
}
REGION_MACRO: dict[str, str] = {
    "east_asia": "asia", "southeast_asia": "asia", "south_asia": "asia",
    "middle_east": "europe_mena", "europe": "europe_mena",
    "americas": "americas",
}


def cuisine_distance(a: str, b: str) -> float:
    """0 same cuisine, 0.4 same region, 0.7 same macro-region, 1.0 otherwise."""
    if a == b:
        return 0.0
    ra, rb = CUISINE_REGION[a], CUISINE_REGION[b]
    if ra == rb:
        return 0.4
    if REGION_MACRO[ra] == REGION_MACRO[rb]:
        return 0.7
    return 1.0


# --- Provenance -------------------------------------------------------------------------------------
Source = Literal[
    "usda", "scoville", "literature", "team", "grok_reviewed", "grok_draft", "seed_placeholder", "fixture",
]
FORBIDDEN_CANONICAL_SOURCES = ("grok_draft",)  # drafts must be reviewed + promoted first
WARN_SOURCES = ("seed_placeholder",)

IngredientCategory = Literal[
    "protein", "seafood", "dairy", "vegetable", "fruit", "starch", "legume", "nut_seed", "herb", "spice",
    "condiment", "fat_oil", "sweetener", "liquid",
]

# --- UI / agent -------------------------------------------------------------------------------------
Panel = Literal["twins", "shift", "explain", "recipe", "ask"]
ToolName = Literal["search_dishes", "find_twins", "shift_taste", "explain_pair"]

SLUG_PATTERN = r"^[a-z][a-z0-9_]{1,40}$"

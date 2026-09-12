#!/usr/bin/env python3
"""P1: ask Grok (xAI API, official xai_sdk) to DRAFT sensory priors for ingredients. OWNER: data (P1).

Drafts are never canonical. They are written to data/drafts/ingredients/grok_<time>.yaml with
src: grok_draft; a human reviews them and merges with tools/data/promote_draft.py, which relabels
reviewed values `grok_reviewed`. The engine refuses grok_draft values in canonical data.

    uv run python tools/data/grok_draft_ingredients.py --ids galangal lemongrass
    uv run python tools/data/grok_draft_ingredients.py --new "yuzu" "white miso" --groups taste aroma mouthfeel

Default groups are aroma + mouthfeel (basic tastes come from USDA via usda_fill.py).
Needs XAI_API_KEY + GROK_MODEL in .env.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, create_model
from tastespace_contracts.taxonomy import DIM_GROUP, DIM_IDS, IngredientCategory
from tastespace_contracts.validate import load_dataset

ROOT = Path(__file__).resolve().parents[2]
BATCH = 8

SYSTEM = """You are a food scientist helping build an interpretable flavor database.
For each ingredient, rate each listed sensory dimension as tasted NEAT on a 0-1 scale:
0 = absent, 1 = the most intense common example (salt for salty, lime juice for sour,
habanero for spicy, heavy cream for creamy, espresso for bitter, liquid smoke for smoky).
Also give potency (0.1-10): how strongly the ingredient carries in a dish per gram
(bland starch 0.5, meat 1, cheese 2-3, soy sauce 6, dried spices 8, vanilla 10).
Be conservative: most dimensions should be 0. Give a one-sentence rationale."""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:40]


def make_shape(dims: list[str]) -> type[BaseModel]:
    profile = create_model("DraftProfile", **{d: (float, Field(0.0, ge=0.0, le=1.0)) for d in dims})
    item = create_model("DraftItem", id=(str, ...), name=(str, ...), category=(IngredientCategory, ...),
                        potency=(float, Field(1.0, ge=0.1, le=10.0)), profile=(profile, ...), rationale=(str, ...))
    return create_model("DraftBatch", items=(list[item], ...))  # type: ignore[valid-type]


def main() -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=[], help="existing ingredient ids to (re)draft")
    ap.add_argument("--new", nargs="*", default=[], help="names of NEW ingredients")
    ap.add_argument("--groups", nargs="*", default=["aroma", "mouthfeel"], choices=["taste", "aroma", "mouthfeel"])
    args = ap.parse_args()
    key, model = os.environ.get("XAI_API_KEY"), os.environ.get("GROK_MODEL")
    if not (key and model):
        print("set XAI_API_KEY and GROK_MODEL in .env (models: https://docs.x.ai/docs/models)", file=sys.stderr)
        return 1
    ds = load_dataset(ROOT / "data", "all")
    targets = [(i, ds.ingredients[i].name, ds.ingredients[i].category) for i in args.ids if i in ds.ingredients]
    targets += [(slug(n), n, None) for n in args.new]
    if not targets:
        print("nothing to draft: pass --ids and/or --new", file=sys.stderr)
        return 1
    dims = [d for d in DIM_IDS if DIM_GROUP[d] in args.groups]
    shape = make_shape(dims)

    from xai_sdk import Client
    from xai_sdk.chat import system, user

    client = Client(api_key=key, timeout=180)
    drafted = []
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = ROOT / "data" / "drafts" / "ingredients" / f"grok_{stamp}.yaml"
    header = ("# DRAFT from Grok (xAI). NOT canonical. Review every value (fix or delete lines), then:\n"
              f"#   uv run python tools/data/promote_draft.py {path.relative_to(ROOT)} --reviewer <you> [--new-into <file>]\n")

    def _flush() -> None:
        path.write_text(header + yaml.safe_dump({"source": "grok_draft", "generated": stamp, "ingredients": drafted},
                                                sort_keys=False, allow_unicode=True, width=120))

    for start in range(0, len(targets), BATCH):
        batch = targets[start:start + BATCH]
        lines = "\n".join(f"- id={i}; name={n}" + (f"; category={c}" if c else "") for i, n, c in batch)
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                chat = client.chat.create(model=model, messages=[system(SYSTEM)])
                chat.append(user(f"Dimensions: {', '.join(dims)}\nIngredients:\n{lines}\nKeep the given ids."))
                _, result = chat.parse(shape)
                last_err = None
                break
            except Exception as exc:  # noqa: BLE001 - xAI SDK raises several transport errors
                last_err = exc
                print(f"  retry {attempt + 1}/3 after {type(exc).__name__}")
        if last_err is not None:
            _flush()
            print(f"wrote partial {path.relative_to(ROOT)} ({len(drafted)} so far)")
            raise last_err
        for item in result.items:  # type: ignore[attr-defined]
            prof = {d: {"v": round(v, 2), "src": "grok_draft"} for d, v in item.profile.model_dump().items() if v > 0}
            drafted.append({"id": slug(item.id), "name": item.name, "category": item.category,
                            "potency": round(item.potency, 2), "note": item.rationale, "profile": prof})
        _flush()
        print(f"  drafted {len(batch)} ingredient(s)  total={len(drafted)}")

    print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

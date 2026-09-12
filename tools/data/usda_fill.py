#!/usr/bin/env python3
"""P1: propose basic-taste/body values from USDA FoodData Central nutrients. OWNER: data (P1).

Writes a DRAFT (data/drafts/ingredients/usda_<time>.yaml, src: usda, nutrient numbers in `note`).
Review the matches, then merge with tools/data/promote_draft.py.

    uv run python tools/data/usda_fill.py soy_sauce lime_juice      # specific ingredient ids
    uv run python tools/data/usda_fill.py --all                     # every canonical ingredient

Needs USDA_API_KEY in .env (free: https://fdc.nal.usda.gov/api-key-signup). Saturating maps
(documented in docs/MODEL.md):
    sweet = 1 - exp(-sugar_g_per_100g / 12)
    salty = 1 - exp(-sodium_mg_per_100g / 1500)
    rich  = 1 - exp(-fat_g_per_100g / 25)
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from tastespace_contracts.validate import load_dataset

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "tools" / "data" / ".cache" / "usda.json"
API = "https://api.nal.usda.gov/fdc/v1/foods/search"
NUTRIENT_NUMBERS = {"sugar": "269", "sodium": "307", "fat": "204"}


def fetch(query: str, key: str, cache: dict) -> dict | None:
    if query in cache:
        return cache[query]
    r = httpx.get(API, params={"query": query, "dataType": "Foundation,SR Legacy", "pageSize": 1, "api_key": key},
                  timeout=20)
    r.raise_for_status()
    foods = r.json().get("foods", [])
    hit = None
    if foods:
        f = foods[0]
        nutr = {n.get("nutrientNumber"): n.get("value") for n in f.get("foodNutrients", [])}
        hit = {"fdcId": f.get("fdcId"), "description": f.get("description"),
               **{k: nutr.get(num) for k, num in NUTRIENT_NUMBERS.items()}}
    cache[query] = hit
    return hit


def main() -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    key = os.environ.get("USDA_API_KEY")
    if not key:
        print("set USDA_API_KEY in .env (free key: https://fdc.nal.usda.gov/api-key-signup)", file=sys.stderr)
        return 1
    ds = load_dataset(ROOT / "data", "all")
    ids = list(ds.ingredients) if args.all else args.ids
    unknown = [i for i in ids if i not in ds.ingredients]
    if unknown or not ids:
        print(f"unknown or missing ingredient ids: {unknown or '(none given)'}", file=sys.stderr)
        return 1

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    out = []
    for iid in ids:
        ing = ds.ingredients[iid]
        hit = fetch(ing.name, key, cache)
        if not hit:
            print(f"  no USDA match for {iid} ({ing.name})")
            continue
        tag = f"fdc {hit['fdcId']}: {hit['description']}"
        profile = {}
        if hit.get("sugar") is not None:
            profile["sweet"] = {"v": round(1 - math.exp(-hit["sugar"] / 12), 2), "src": "usda",
                                "note": f"sugar {hit['sugar']} g/100g ({tag})"}
        if hit.get("sodium") is not None:
            profile["salty"] = {"v": round(1 - math.exp(-hit["sodium"] / 1500), 2), "src": "usda",
                                "note": f"sodium {hit['sodium']} mg/100g ({tag})"}
        if hit.get("fat") is not None:
            profile["rich"] = {"v": round(1 - math.exp(-hit["fat"] / 25), 2), "src": "usda",
                               "note": f"fat {hit['fat']} g/100g ({tag})"}
        out.append({"id": iid, "note": f"USDA match: {tag} - CHECK this is the right food", "profile": profile})
        print(f"  {iid:<22} <- {hit['description']}")
    CACHE.write_text(json.dumps(cache, indent=1))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = ROOT / "data" / "drafts" / "ingredients" / f"usda_{stamp}.yaml"
    header = "# DRAFT from USDA FoodData Central. Check every match, then:\n" \
             f"#   uv run python tools/data/promote_draft.py {path.relative_to(ROOT)} --reviewer <you>\n"
    path.write_text(header + yaml.safe_dump({"source": "usda", "generated": stamp, "ingredients": out},
                                            sort_keys=False, allow_unicode=True, width=120))
    print(f"wrote {path.relative_to(ROOT)} ({len(out)} ingredients)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

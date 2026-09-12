#!/usr/bin/env python3
"""P1: merge REVIEWED draft values into canonical data/ingredients/*.yaml. OWNER: data (P1).

    uv run python tools/data/promote_draft.py data/drafts/ingredients/grok_X.yaml --reviewer alex
        [--only id1 id2] [--dims sour fruity] [--new-into produce] [--dry-run]

- grok_draft values become grok_reviewed (running this asserts that you reviewed them); other srcs keep theirs.
- Existing ingredients: the listed dims are overwritten; other dims are untouched.
- New ingredients need name + category in the draft and --new-into <ingredients file stem>.
- Touched ingredients are rewritten with explicit {v, src} values; the file header comment is kept.
Then run `make check-data`.
"""

import argparse
import sys
from pathlib import Path

import yaml
from draft_format import DraftFile
from tastespace_contracts.data_models import IngredientFile

ROOT = Path(__file__).resolve().parents[2]
ING_DIR = ROOT / "data" / "ingredients"


def load_raw(path: Path) -> tuple[str, dict]:
    text = path.read_text()
    header = "".join(line + "\n" for line in text.splitlines() if line.startswith("#"))
    return header, yaml.safe_load(text) or {"ingredients": []}


def explicit(profile: dict, default_src: str | None) -> dict:
    return {d: (v if isinstance(v, dict) else {"v": v, "src": default_src}) for d, v in (profile or {}).items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dims", nargs="*")
    ap.add_argument("--new-into", help="ingredients file stem for new ingredients, e.g. produce")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    draft = DraftFile.model_validate(yaml.safe_load(Path(args.draft).read_text()))
    files = {p: load_raw(p) for p in sorted(ING_DIR.glob("*.yaml"))}
    where = {ing["id"]: p for p, (_, raw) in files.items() for ing in raw.get("ingredients", [])}
    touched: set[Path] = set()

    for item in draft.ingredients:
        if args.only and item.id not in args.only:
            continue
        values = {d: pv for d, pv in item.profile.items() if not args.dims or d in args.dims}
        new_vals = {d: {"v": pv.v, "src": "grok_reviewed" if pv.src == "grok_draft" else pv.src,
                        **({"note": pv.note} if pv.note else {})} for d, pv in values.items()}
        if item.id in where:
            path = where[item.id]
            header, raw = files[path]
            ing = next(i for i in raw["ingredients"] if i["id"] == item.id)
            ing["profile"] = {**explicit(ing.get("profile"), raw.get("default_src")), **new_vals}
            if item.potency is not None and draft.source != "usda":
                ing["potency"] = item.potency
        else:
            if not (args.new_into and item.name and item.category):
                print(f"  skip new ingredient '{item.id}': needs name + category in the draft and --new-into")
                continue
            path = ING_DIR / f"{args.new_into}.yaml"
            if path not in files:
                files[path] = ("# OWNER: data (P1). See protein.yaml for the format.\n", {"ingredients": []})
            files[path][1]["ingredients"].append({"id": item.id, "name": item.name, "category": item.category,
                                                  **({"potency": item.potency} if item.potency else {}),
                                                  "profile": new_vals})
            ing = files[path][1]["ingredients"][-1]
        ing["reviewed_by"] = args.reviewer
        touched.add(path)
        print(f"  {item.id:<22} {', '.join(f'{d}={v['v']}' for d, v in new_vals.items())} -> {path.name}")

    for path in sorted(touched):
        header, raw = files[path]
        IngredientFile.model_validate(raw)  # never write an invalid file
        if not args.dry_run:
            path.write_text(header + yaml.safe_dump(raw, sort_keys=False, default_flow_style=None, width=160,
                                                    allow_unicode=True))
    print(f"{'would update' if args.dry_run else 'updated'} {len(touched)} file(s). Now run: make check-data")
    return 0


if __name__ == "__main__":
    sys.exit(main())

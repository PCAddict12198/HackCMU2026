"""Load + validate everything under data/ against the contracts.

Used by P1 (`make check-data`) and by the engine (build + API). It collects ALL problems before
failing, so one run shows the full list. CLI:

    uv run python -m tastespace_contracts.validate [data_dir] [--tier core|all] [--strict]

--strict (use from H16): every manifest dish must exist and every sanity pair must resolve.
"""

from __future__ import annotations

import argparse
import dataclasses
import difflib
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .data_models import (
    AliasesFile,
    CuisineInfo,
    CuisinesFile,
    DimInfo,
    DimsFile,
    Dish,
    DishesFile,
    DishManifest,
    Format,
    FormatsFile,
    Ingredient,
    IngredientFile,
    Process,
    ProcessesFile,
    RatingsFile,
    SanityPairs,
    UnitDef,
    UnitsFile,
)
from .taxonomy import (
    CUISINE_IDS,
    DIM_IDS,
    FORBIDDEN_CANONICAL_SOURCES,
    FORMAT_IDS,
    PROCESS_IDS,
    WARN_SOURCES,
)


class DataValidationError(Exception):
    def __init__(self, errors: list[str], warnings: list[str] | None = None):
        self.errors = list(errors)
        self.warnings = list(warnings or [])
        super().__init__(f"{len(self.errors)} data error(s):\n" + "\n".join(f"  - {e}" for e in self.errors))


@dataclasses.dataclass
class Dataset:
    data_dir: Path
    tier: str
    dims: list[DimInfo]
    cuisines: dict[str, CuisineInfo]
    formats: dict[str, Format]
    processes: dict[str, Process]
    ingredients: dict[str, Ingredient]
    dishes: dict[str, Dish]  # filtered by tier
    extended_dishes: dict[str, Dish]
    units: dict[str, UnitDef]
    aliases: dict[str, str]
    manifest: DishManifest | None
    sanity: SanityPairs | None
    ratings: RatingsFile | None
    warnings: list[str]


def _describe_loc(raw: Any, loc: tuple) -> str:
    """Turn ('ingredients', 3, 'profile', 'salty') into 'ingredients[3](lime).profile.salty'."""
    parts: list[str] = []
    node = raw
    for p in loc:
        if isinstance(p, int) and isinstance(node, list) and p < len(node):
            item = node[p]
            label = item.get("id") if isinstance(item, dict) else None
            parts.append(f"[{p}]" + (f"({label})" if label else ""))
            node = item
        else:
            parts.append(f".{p}")
            node = node.get(p) if isinstance(node, dict) else None
    return "".join(parts).lstrip(".")


class _Collector:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.root.parent))
        except ValueError:
            return str(p)

    def load(self, path: Path, model: type[BaseModel], required: bool = True) -> Any:
        rel = self.rel(path)
        if not path.exists():
            if required:
                self.errors.append(f"{rel}: file is missing")
            return None
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            self.errors.append(f"{rel}: YAML syntax error: {' '.join(str(exc).split())}")
            return None
        if raw is None:
            self.errors.append(f"{rel}: file is empty")
            return None
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            for err in exc.errors():
                self.errors.append(f"{rel}: {_describe_loc(raw, err['loc'])}: {err['msg']}")
            return None

    def index(self, rel: str, items: list, kind: str) -> dict:
        out: dict = {}
        for it in items:
            if it.id in out:
                self.errors.append(f"{rel}: duplicate {kind} id '{it.id}'")
            out[it.id] = it
        return out


def _suggest(name: str, options) -> str:
    match = difflib.get_close_matches(name, list(options), n=1)
    return f" (did you mean '{match[0]}'?)" if match else ""


def _load_dish_folder(c: _Collector, folder: Path, tier: str) -> dict[str, tuple[Dish, str]]:
    found: dict[str, tuple[Dish, str]] = {}
    if not folder.is_dir():
        return found
    for path in sorted(folder.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        f = c.load(path, DishesFile)
        if not f:
            continue
        for d in f.dishes:
            rel = c.rel(path)
            if d.tier != tier:
                c.errors.append(f"{rel}: dish '{d.id}' has tier '{d.tier}' but lives in dishes/{tier}/")
            if d.id in found:
                c.errors.append(f"{rel}: duplicate dish id '{d.id}' (also in {found[d.id][1]})")
            found[d.id] = (d, rel)
    return found


def load_dataset(data_dir: str | Path = "data", tier: str = "core", strict: bool = False) -> Dataset:
    root = Path(data_dir).resolve()
    if not root.is_dir():
        raise DataValidationError([f"{root}: data directory not found"])
    c = _Collector(root)

    dims_f = c.load(root / "dims.yaml", DimsFile)
    cuis_f = c.load(root / "cuisines.yaml", CuisinesFile)
    fmts_f = c.load(root / "formats.yaml", FormatsFile)
    proc_f = c.load(root / "processes.yaml", ProcessesFile)
    units_f = c.load(root / "lexicon" / "units.yaml", UnitsFile)
    alias_f = c.load(root / "lexicon" / "aliases.yaml", AliasesFile)
    manifest = c.load(root / "dishes" / "core" / "_manifest.yaml", DishManifest)
    sanity = c.load(root / "sanity" / "sanity_pairs.yaml", SanityPairs)
    ratings = c.load(root / "validation" / "ratings.yaml", RatingsFile, required=False)

    # --- fixed vocabularies must be complete and canonical -------------------------------------------
    dims = dims_f.dims if dims_f else []
    if dims_f and [d.id for d in dims] != list(DIM_IDS):
        c.errors.append(f"data/dims.yaml: must list exactly these dims in this order: {', '.join(DIM_IDS)}")
    cuisines = c.index("data/cuisines.yaml", cuis_f.cuisines if cuis_f else [], "cuisine")
    formats = c.index("data/formats.yaml", fmts_f.formats if fmts_f else [], "format")
    processes = c.index("data/processes.yaml", proc_f.processes if proc_f else [], "process")
    for rel, have, want in (("data/cuisines.yaml", cuisines, CUISINE_IDS), ("data/formats.yaml", formats, FORMAT_IDS),
                            ("data/processes.yaml", processes, PROCESS_IDS)):
        missing = [x for x in want if x not in have]
        if (cuis_f if rel.endswith("cuisines.yaml") else fmts_f if rel.endswith("formats.yaml") else proc_f) and missing:
            c.errors.append(f"{rel}: missing entries for {', '.join(missing)}")

    # --- ingredients ------------------------------------------------------------------------------------
    ingredients: dict[str, Ingredient] = {}
    where: dict[str, str] = {}
    ing_files = sorted((root / "ingredients").glob("*.yaml"))
    if not ing_files:
        c.errors.append("data/ingredients/: no ingredient files found")
    for path in ing_files:
        f = c.load(path, IngredientFile)
        if not f:
            continue
        for ing in f.ingredients:
            if ing.id in ingredients:
                c.errors.append(f"{c.rel(path)}: duplicate ingredient id '{ing.id}' (also in {where[ing.id]})")
            ingredients[ing.id] = ing
            where[ing.id] = c.rel(path)

    seed_ings = 0
    for ing in ingredients.values():
        has_seed = False
        for dim in ing.profile:
            pv = ing.value(dim)
            if pv is None:
                continue
            if pv.src in FORBIDDEN_CANONICAL_SOURCES:
                c.errors.append(f"{where[ing.id]}: {ing.id}.{dim} has src '{pv.src}' - drafts belong in "
                                f"data/drafts/; review and run tools/data/promote_draft.py")
            if pv.src in WARN_SOURCES:
                has_seed = True
        seed_ings += has_seed
    if seed_ings:
        c.warnings.append(f"{seed_ings} ingredient(s) still contain seed_placeholder values (replace before H16)")

    # names/aliases must point at exactly one ingredient
    name_owner: dict[str, str] = {}
    for ing in ingredients.values():
        for n in [ing.id.replace("_", " "), ing.name, *ing.aliases]:
            key = n.strip().lower()
            if key in name_owner and name_owner[key] != ing.id:
                c.errors.append(f"{where[ing.id]}: name/alias '{n}' used by both '{name_owner[key]}' and '{ing.id}'")
            name_owner.setdefault(key, ing.id)
    aliases = dict(alias_f.aliases) if alias_f else {}
    for alias, target in aliases.items():
        if target not in ingredients:
            c.errors.append(f"data/lexicon/aliases.yaml: '{alias}' -> unknown ingredient '{target}'"
                            f"{_suggest(target, ingredients)}")
        owner = name_owner.get(alias.strip().lower())
        if owner and owner != target:
            c.errors.append(f"data/lexicon/aliases.yaml: '{alias}' -> '{target}' conflicts with ingredient '{owner}'")

    # --- dishes -----------------------------------------------------------------------------------------
    core = _load_dish_folder(c, root / "dishes" / "core", "core")
    ext = _load_dish_folder(c, root / "dishes" / "extended", "extended")
    for dup in set(core) & set(ext):
        c.errors.append(f"dish id '{dup}' exists in both core/ and extended/")
    for dish, rel in list(core.values()) + list(ext.values()):
        for i, di in enumerate(dish.ingredients):
            if di.ing not in ingredients:
                c.errors.append(f"{rel}: {dish.id}.ingredients[{i}]: unknown ingredient '{di.ing}'"
                                f"{_suggest(di.ing, ingredients)}")

    # --- manifest (the frozen list of core dishes) --------------------------------------------------------
    if manifest is not None:
        man = list(manifest.core)
        if len(set(man)) != len(man):
            c.errors.append("data/dishes/core/_manifest.yaml: duplicate ids")
        for did, (_, rel) in core.items():
            if did not in man:
                c.errors.append(f"{rel}: core dish '{did}' is not in _manifest.yaml (add it there or move it to "
                                f"dishes/extended/)")
        missing = [d for d in man if d not in core]
        if missing:
            msg = (f"core progress: {len(man) - len(missing)}/{len(man)} manifest dishes written; "
                   f"missing e.g. {', '.join(missing[:6])}")
            (c.errors if strict else c.warnings).append(msg)

    # --- sanity pairs (frozen at h0-freeze) + optional ratings -------------------------------------------
    man_set = set(manifest.core) if manifest else set()
    if sanity is not None:
        unresolved = 0
        for kind, pairs in (("positive", sanity.positive), ("negative", sanity.negative)):
            for p in pairs:
                if p.a == p.b:
                    c.errors.append(f"data/sanity/sanity_pairs.yaml: {kind} pair {p.a}/{p.b} compares a dish to itself")
                for x in (p.a, p.b):
                    if manifest is not None and x not in man_set:
                        c.errors.append(f"data/sanity/sanity_pairs.yaml: '{x}' is not a manifest (core) dish")
                if p.a in core and p.b in core:
                    if core[p.a][0].course != core[p.b][0].course:
                        c.errors.append(f"data/sanity/sanity_pairs.yaml: {p.a}/{p.b} are different courses")
                else:
                    unresolved += 1
        if unresolved:
            msg = f"{unresolved} sanity pair(s) reference dishes not written yet (skipped in the report)"
            (c.errors if strict else c.warnings).append(msg)
    if ratings is not None:
        for p in ratings.pairs:
            for x in (p.a, p.b):
                if manifest is not None and x not in man_set:
                    c.errors.append(f"data/validation/ratings.yaml: '{x}' is not a manifest (core) dish")

    if c.errors:
        raise DataValidationError(c.errors, c.warnings)

    core_d = {k: v[0] for k, v in core.items()}
    ext_d = {k: v[0] for k, v in ext.items()}
    return Dataset(
        data_dir=root,
        tier=tier,
        dims=dims,
        cuisines=cuisines,
        formats=formats,
        processes=processes,
        ingredients=ingredients,
        dishes=core_d if tier == "core" else {**core_d, **ext_d},
        extended_dishes=ext_d,
        units=dict(units_f.units) if units_f else {},
        aliases=aliases,
        manifest=manifest,
        sanity=sanity,
        ratings=ratings,
        warnings=c.warnings,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate data/ against the frozen TasteSpace contracts.")
    ap.add_argument("data_dir", nargs="?", default="data")
    ap.add_argument("--tier", choices=["core", "all"], default="core")
    ap.add_argument("--strict", action="store_true", help="manifest + sanity pairs must be complete (H16+)")
    args = ap.parse_args(argv)
    try:
        ds = load_dataset(args.data_dir, args.tier, args.strict)
    except DataValidationError as exc:
        for w in exc.warnings:
            print(f"WARN  {w}")
        for e in exc.errors:
            print(f"ERROR {e}")
        print(f"\nFAIL: data invalid ({len(exc.errors)} error(s))")
        return 1
    for w in ds.warnings:
        print(f"WARN  {w}")
    n_seed = sum(1 for i in ds.ingredients.values() if any(ds_v.src == "seed_placeholder"
                                                            for ds_v in (i.value(d) for d in i.profile) if ds_v))
    print(f"OK: {len(ds.ingredients)} ingredients ({n_seed} with seed values), {len(ds.dishes)} dishes "
          f"(tier={args.tier}), {len(ds.extended_dishes)} extended")
    return 0


if __name__ == "__main__":
    sys.exit(main())

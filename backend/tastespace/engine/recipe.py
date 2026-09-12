"""Recipe text -> ingredient lines -> dish vector, using the SAME aggregation + stored calibration.

Pipeline: regex (quantity, unit) -> units lexicon -> exact name/alias match -> difflib fuzzy match
-> optional Grok mapper for leftovers (closed list of ingredient ids) -> grams -> aggregate -> project.
Every line reports how it was matched so the UI can show coverage honestly.
"""

import difflib
import re
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from tastespace_contracts.api_models import (
    Coverage,
    NeighborResult,
    RecipeLine,
    RecipeRequest,
    RecipeResponse,
)
from tastespace_contracts.data_models import Ingredient, UnitDef
from tastespace_contracts.validate import Dataset

from ..errors import TasteSpaceError
from ..state import EngineState
from .aggregate import finalize, raw_from_items

Mapper = Callable[[list[str]], dict[str, str]]

UNICODE_FRACTIONS = {"½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75, "⅛": 0.125, "⅜": 0.375,
                     "⅝": 0.625, "⅞": 0.875}
PROCESS_WORDS = {
    "smoked": "smoked", "roasted": "roasted", "grilled": "grilled", "charred": "grilled", "fried": "fried",
    "deep-fried": "deep_fried", "caramelized": "caramelized", "caramelised": "caramelized",
    "toasted": "toasted", "pickled": "pickled", "fermented": "fermented", "braised": "braised",
    "steamed": "steamed", "boiled": "boiled", "cured": "cured",
}
DESCRIPTORS = {
    "fresh", "freshly", "chopped", "diced", "minced", "sliced", "large", "small", "medium", "finely",
    "roughly", "thinly", "grated", "crushed", "peeled", "dried", "about", "optional", "for", "serving",
    "garnish", "to", "taste", "of", "a", "an", "the", "good", "quality", "extra", "virgin", "packed",
    "ripe", "cold", "warm", "hot", "boneless", "skinless", "raw", "cooked", "halved", "quartered", "whole",
}
DEFAULT_TO_TASTE_G = 1.0
DEFAULT_UNKNOWN_G = 10.0
DEFAULT_PIECE_G = 50.0

_NUM = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|[½⅓⅔¼¾⅛⅜⅝⅞])"
_QTY_RE = re.compile(rf"^\s*(?P<a>{_NUM})(?:\s*(?:-|–|to)\s*(?P<b>{_NUM}))?\s*")


def _num(tok: str) -> float:
    tok = tok.strip()
    if tok in UNICODE_FRACTIONS:
        return UNICODE_FRACTIONS[tok]
    if " " in tok:
        whole, frac = tok.split(None, 1)
        return float(whole) + _num(frac)
    if "/" in tok:
        n, d = tok.split("/")
        return float(n) / float(d) if float(d) else 0.0
    return float(tok)


@dataclass
class ParsedLine:
    raw: str
    qty: float | None
    unit: str | None
    name: str
    processes: list[str]
    to_taste: bool


def build_unit_index(units: dict[str, UnitDef]) -> dict[str, str]:
    idx: dict[str, str] = {}
    for key, u in units.items():
        for n in [key, *u.aliases]:
            idx[n.lower()] = key
    return idx


def parse_line(line: str, unit_index: dict[str, str]) -> ParsedLine | None:
    raw = line.strip()
    s = raw.lstrip("-*•·–").strip()
    if not s or s.endswith(":") or not re.search(r"[A-Za-z]", s):
        return None
    s = re.sub(r"(\d)([½⅓⅔¼¾⅛⅜⅝⅞])", r"\1 \2", s)
    s = re.sub(r"\([^)]*\)", " ", s)
    to_taste = bool(re.search(r"\bto taste\b|\bpinch\b|\bdash\b", s, re.I))
    s = s.split(",")[0]
    qty = None
    mq = _QTY_RE.match(s)
    if mq:
        a = _num(mq["a"])
        qty = (a + _num(mq["b"])) / 2 if mq["b"] else a
        s = s[mq.end():]
    tokens = s.strip().split()
    unit = None
    if tokens and tokens[0].lower().rstrip(".") in unit_index:
        unit = unit_index[tokens[0].lower().rstrip(".")]
        tokens = tokens[1:]
    words = [w.lower().strip(".;:") for w in tokens]
    if words and words[0] == "of":
        words = words[1:]
    procs = [PROCESS_WORDS[w] for w in words if w in PROCESS_WORDS]
    name = " ".join(w for w in words if w not in PROCESS_WORDS).strip()
    if not name:
        return None
    return ParsedLine(raw=raw, qty=qty, unit=unit, name=name, processes=procs, to_taste=to_taste)


class IngredientMatcher:
    def __init__(self, ingredients: dict[str, Ingredient], aliases: dict[str, str]):
        self.index: dict[str, str] = {}
        for ing in ingredients.values():
            for n in [ing.id, ing.id.replace("_", " "), ing.name, *ing.aliases]:
                self.index.setdefault(n.lower().strip(), ing.id)
        for alias, target in aliases.items():
            self.index.setdefault(alias.lower().strip(), target)
        self.keys = list(self.index)

    @staticmethod
    def _singulars(s: str) -> list[str]:
        out = [s]
        if s.endswith("es"):
            out.append(s[:-2])
        if s.endswith("s"):
            out.append(s[:-1])
        return out

    def match(self, name: str) -> tuple[str | None, str, float]:
        core = " ".join(w for w in name.split() if w not in DESCRIPTORS)
        exact = [v for c in (name, core) if c for v in self._singulars(c)]
        for v in exact:
            if v in self.index:
                return self.index[v], "matched", 1.0
        best: tuple[float, str] | None = None
        for c in (name, core):
            for hit in difflib.get_close_matches(c, self.keys, n=1, cutoff=0.84) if c else []:
                ratio = difflib.SequenceMatcher(None, c, hit).ratio()
                if best is None or ratio > best[0]:
                    best = (ratio, hit)
        if best:
            return self.index[best[1]], "fuzzy", round(best[0], 2)
        words = core.split()
        for tail in ([" ".join(words[-2:])] if len(words) >= 2 else []) + (words[-1:] if words else []):
            for v in self._singulars(tail):
                if v in self.index:
                    return self.index[v], "fuzzy", 0.7
        return None, "unmatched", 0.0


def estimate_grams(p: ParsedLine, ing: Ingredient, units: dict[str, UnitDef]) -> tuple[float, str | None]:
    if p.qty is None:
        if p.to_taste:
            return DEFAULT_TO_TASTE_G, f"no amount ('to taste'): assumed {DEFAULT_TO_TASTE_G:g} g"
        if ing.unit_weight_g:
            return ing.unit_weight_g, "no amount: assumed 1 piece"
        return DEFAULT_UNKNOWN_G, f"no amount: assumed {DEFAULT_UNKNOWN_G:g} g"
    if p.unit is None:
        if ing.unit_weight_g:
            return p.qty * ing.unit_weight_g, None
        if p.qty >= 20:
            return p.qty, "no unit: read as grams"
        return p.qty * DEFAULT_PIECE_G, f"no unit: assumed {DEFAULT_PIECE_G:g} g each"
    u = units[p.unit]
    if u.kind == "mass":
        return p.qty * u.factor, None
    if u.kind == "volume":
        return p.qty * u.factor * (ing.density_g_per_ml or 1.0), None
    per = ing.unit_weight_g or DEFAULT_PIECE_G
    return p.qty * u.factor * per, None if ing.unit_weight_g else f"assumed {per:g} g per {p.unit}"


def analyze_recipe(state: EngineState, ds: Dataset, req: RecipeRequest, mapper: Mapper | None = None) -> RecipeResponse:
    unit_index = build_unit_index(ds.units)
    matcher = IngredientMatcher(ds.ingredients, ds.aliases)
    parsed = [p for line in req.text.splitlines() if (p := parse_line(line, unit_index))]
    if not parsed:
        raise TasteSpaceError("validation_error", "no ingredient lines found in the recipe text")

    rows: list[list] = []
    for p in parsed:
        ing_id, status, conf = matcher.match(p.name)
        rows.append([p, ing_id, status, conf])

    used_grok = False
    unmatched = [r[0].name for r in rows if r[1] is None]
    if unmatched and mapper is not None:
        try:
            mapping = mapper(unmatched)
        except TasteSpaceError:
            mapping = {}  # Grok is optional here: fall back to reporting the lines as unmatched
        for r in rows:
            target = mapping.get(r[0].name)
            if r[1] is None and target in ds.ingredients:
                r[1], r[2], r[3] = target, "grok_mapped", 0.6
                used_grok = True

    lines: list[RecipeLine] = []
    items: list[tuple[str, float, list[str]]] = []
    for p, ing_id, status, conf in rows:
        grams, note = (None, None)
        if ing_id:
            grams, note = estimate_grams(p, ds.ingredients[ing_id], ds.units)
            items.append((ing_id, grams, p.processes))
        lines.append(RecipeLine(raw=p.raw, status=status, ingredient_id=ing_id,
                                grams=round(grams, 1) if grams else None, confidence=conf,
                                process=p.processes, note=note))  # type: ignore[arg-type]
    if not items:
        raise TasteSpaceError("validation_error", "none of the ingredients were recognized",
                              {"unmatched": unmatched})

    fmt = ds.formats.get(req.format) if req.format else None
    dv = finalize(raw_from_items(items, ds.ingredients, ds.processes, fmt), state.model.s)
    m = state.model
    d = m.dists_to(m.z(dv.vector))
    course = req.course or m.courses[int(np.argmin(d))]
    idx = sorted((j for j in range(len(m.ids)) if m.courses[j] == course), key=lambda j: d[j])
    neighbors = [NeighborResult(dish_id=m.ids[j], similarity_pct=round(m.similarity_pct(float(d[j]), course), 1),
                                distance=round(float(d[j]), 4)) for j in idx[:5]]
    return RecipeResponse(
        name=req.name or "Your recipe", course=course, lines=lines,  # type: ignore[arg-type]
        coverage=Coverage(matched=sum(1 for ln in lines if ln.ingredient_id), total=len(lines)),
        used_grok=used_grok, vector=state.vector_dict(dv.vector),  # type: ignore[arg-type]
        xyz=tuple(round(float(x), 4) for x in m.project(dv.vector)),  # type: ignore[arg-type]
        neighbors=neighbors, attributions=dv.attributions)  # type: ignore[arg-type]

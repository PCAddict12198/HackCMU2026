"""Dish vector = saturating, potency-weighted aggregation of processed ingredients + a format term.

    raw_k = sum_i share_i * potency_i * r'_ik        share_i = grams_i / total grams
    ing_k = 1 - exp(-raw_k / s_k)                    s_k calibrated on the core tier (see calibrate)
    D_k   = ing_k + f_k * (1 - ing_k)                format contribution (noisy-OR)

Attribution is exact: ingredient i contributes ing_k * term_ik / raw_k, the format contributes
f_k * (1 - ing_k); together they sum to D_k. Bland bulk (water, noodles) has r ~ 0 so it no longer
dilutes the potent ingredients the way a weighted average would.
"""

from dataclasses import dataclass

import numpy as np
from tastespace_contracts.data_models import Dish, Format, Ingredient, Process
from tastespace_contracts.taxonomy import DIM_IDS

from .transforms import DIM_INDEX, apply_processes

N = len(DIM_IDS)


@dataclass
class Term:
    ingredient_id: str
    process: list[str]
    grams: float
    vector: np.ndarray  # share * potency * r'
    src: list[str | None]  # provenance of the ingredient's own value per dim (None = came from a process)


@dataclass
class RawDish:
    raw: np.ndarray
    terms: list[Term]
    fmt: np.ndarray
    fmt_id: str | None


@dataclass
class DishVector:
    vector: np.ndarray
    attributions: dict[str, list[dict]]  # dim -> Contribution dicts, largest first


def ingredient_vector(ing: Ingredient) -> tuple[np.ndarray, list[str | None]]:
    r = np.zeros(N)
    src: list[str | None] = [None] * N
    for dim in ing.profile:
        pv = ing.value(dim)
        if pv is not None:
            r[DIM_INDEX[dim]] = pv.v
            src[DIM_INDEX[dim]] = pv.src
    return r, src


def format_vector(fmt: Format | None) -> np.ndarray:
    f = np.zeros(N)
    if fmt is not None:
        for dim, v in fmt.f.items():
            f[DIM_INDEX[dim]] = v
    return f


def raw_from_items(items: list[tuple[str, float, list[str]]], ingredients: dict[str, Ingredient],
                   processes: dict[str, Process], fmt: Format | None) -> RawDish:
    total = sum(g for _, g, _ in items)
    raw = np.zeros(N)
    terms: list[Term] = []
    for ing_id, grams, procs in items:
        ing = ingredients[ing_id]
        r, src = ingredient_vector(ing)
        r2 = apply_processes(r, procs, processes)
        term = (grams / total) * ing.potency * r2
        raw += term
        terms.append(Term(ing_id, list(procs), grams, term, src))
    return RawDish(raw=raw, terms=terms, fmt=format_vector(fmt), fmt_id=fmt.id if fmt else None)


def raw_dish(dish: Dish, ingredients: dict[str, Ingredient], processes: dict[str, Process],
             formats: dict[str, Format]) -> RawDish:
    items = [(di.ing, di.g, list(di.process)) for di in dish.ingredients]
    return raw_from_items(items, ingredients, processes, formats.get(dish.format))


def calibrate(raws: np.ndarray, quantile: float = 0.9, target: float = 0.9) -> np.ndarray:
    """Pick s_k so the dish at the `quantile` of raw_k scores `target` (before the format term).

    The quantile is taken over the dishes that HAVE dim k (raw_k > 0). Over all dishes, a sparse dim
    (e.g. smoky in 4 of 16) puts its 90th percentile on a barely-smoky dish, which saturates every
    smoky dish to ~1 and erases the differences between them.
    """
    raws = np.atleast_2d(np.asarray(raws, dtype=float))
    s = np.ones(raws.shape[1])  # a dim no dish has: any positive scale works
    for k in range(raws.shape[1]):
        present = raws[:, k][raws[:, k] > 0]
        if len(present):
            s[k] = np.quantile(present, quantile) / -np.log(1.0 - target)
    return s


def finalize(rd: RawDish, s: np.ndarray) -> DishVector:
    ing = 1.0 - np.exp(-rd.raw / s)
    vec = ing + rd.fmt * (1.0 - ing)
    attributions: dict[str, list[dict]] = {}
    for k, dim in enumerate(DIM_IDS):
        contribs: list[dict] = []
        if rd.raw[k] > 0:
            for t in rd.terms:
                if t.vector[k] > 0:
                    contribs.append({"kind": "ingredient", "id": t.ingredient_id,
                                     "value": float(ing[k] * t.vector[k] / rd.raw[k]),
                                     "src": t.src[k], "process": list(t.process)})
        fmt_part = float(rd.fmt[k] * (1.0 - ing[k]))
        if fmt_part > 0 and rd.fmt_id:
            contribs.append({"kind": "format", "id": rd.fmt_id, "value": fmt_part, "src": None, "process": []})
        contribs.sort(key=lambda c: -c["value"])
        attributions[dim] = contribs
    return DishVector(vector=vec, attributions=attributions)

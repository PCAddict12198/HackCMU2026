"""Messy real-world recipe lines found by probing the parser (H3-5). Fixture lexicon only."""

import pytest
from tastespace.engine.recipe import (
    IngredientMatcher,
    build_unit_index,
    estimate_grams,
    parse_line,
    parse_lines,
)


@pytest.fixture
def units(fx_dataset):
    return build_unit_index(fx_dataset.units)


@pytest.fixture
def matcher(fx_dataset):
    return IngredientMatcher(fx_dataset.ingredients, fx_dataset.aliases)


@pytest.mark.parametrize("line,qty,unit,name", [
    ("1½ cups broth", 1.5, "cup", "broth"),  # was qty=1, unit=None
    ("2¼ tbsp cream", 2.25, "tbsp", "cream"),
    ("200g/7oz noodles", 200, "g", "noodles"),  # alternate unit after a slash
    ("200 g / 7 oz noodles", 200, "g", "noodles"),
    ("1 x 400g can cream", 400, "g", "can cream"),  # "N x" multiplier
    ("2 x 400g cans broth", 800, "g", "cans broth"),
    ("a handful of chili", 1, "handful", "chili"),  # leading article = 1
    ("juice of 2 limes", 2, None, "limes"),
])
def test_messy_lines_parse(units, line, qty, unit, name):
    p = parse_line(line, units)
    assert p is not None and p.qty == pytest.approx(qty) and p.unit == unit and p.name == name


def test_container_words_do_not_block_exact_matches(units, matcher):
    for line in ("400ml can broth", "1 x 400g can cream"):
        assert matcher.match(parse_line(line, units).name)[1] == "matched"


def test_salt_and_pepper_to_taste_splits(units, matcher):
    parts = parse_lines("Salt and pepper to taste", units)
    assert [p.name for p in parts] == ["salt to taste", "pepper to taste"]
    assert all(p.to_taste and p.qty is None for p in parts)
    assert matcher.match(parts[0].name)[0] == "salt"


def test_lines_with_quantities_are_never_split(units):
    assert len(parse_lines("2 tbsp salt and pepper to taste", units)) == 1


def test_grams_for_fixed_lines(units, fx_dataset):
    ings = fx_dataset.ingredients
    assert estimate_grams(parse_line("1½ cups broth", units), ings["broth"], fx_dataset.units)[0] == pytest.approx(360)
    assert estimate_grams(parse_line("juice of 2 limes", units), ings["lime"], fx_dataset.units)[0] == pytest.approx(60)
    assert estimate_grams(parse_line("a handful of chili", units), ings["chili"], fx_dataset.units)[0] == pytest.approx(30)

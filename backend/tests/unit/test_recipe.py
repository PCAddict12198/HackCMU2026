import numpy as np
import pytest
from tastespace.engine.recipe import analyze_recipe, build_unit_index, parse_line
from tastespace.errors import TasteSpaceError
from tastespace_contracts.api_models import RecipeRequest


@pytest.fixture
def units(fx_dataset):
    return build_unit_index(fx_dataset.units)


@pytest.mark.parametrize("line,qty,unit,name", [
    ("200g noodles", 200, "g", "noodles"),
    ("1 1/2 cups broth", 1.5, "cup", "broth"),
    ("½ tsp chili", 0.5, "tsp", "chili"),
    ("2 limes", 2, None, "limes"),
    ("- 3 tbsp cream (heavy)", 3, "tbsp", "cream"),
    ("1-2 onions, diced", 1.5, None, "onions"),
])
def test_parse_line(units, line, qty, unit, name):
    p = parse_line(line, units)
    assert p is not None and p.qty == pytest.approx(qty) and p.unit == unit and p.name == name


def test_parse_line_skips_headers_and_handles_to_taste(units):
    assert parse_line("Ingredients:", units) is None
    assert parse_line("   ", units) is None
    p = parse_line("salt to taste", units)
    assert p.qty is None and p.to_taste


def test_analyze_recipe_coverage_and_vector(fx_state, fx_dataset):
    text = "400 g broth\n150g noodles\n1 tsp sea salt\n2 green onions\n1 dragonfruit"
    res = analyze_recipe(fx_state, fx_dataset, RecipeRequest(text=text, format="soup"))
    statuses = {ln.raw: ln.status for ln in res.lines}
    assert statuses["1 dragonfruit"] == "unmatched"
    assert res.coverage.matched == 4 and res.coverage.total == 5 and not res.used_grok
    assert all(0 <= v <= 1 for v in res.vector.values()) and np.isfinite(res.xyz).all()
    assert res.neighbors[0].dish_id == "fx_noodle_soup"


def test_grok_mapper_only_fills_unmatched_lines(fx_state, fx_dataset):
    res = analyze_recipe(fx_state, fx_dataset, RecipeRequest(text="100 g cream\n1 dragonfruit"),
                         mapper=lambda names: {"dragonfruit": "lime"})
    line = next(ln for ln in res.lines if ln.raw == "1 dragonfruit")
    assert line.status == "grok_mapped" and line.ingredient_id == "lime" and res.used_grok


def test_mapper_cannot_inject_unknown_ids(fx_state, fx_dataset):
    res = analyze_recipe(fx_state, fx_dataset, RecipeRequest(text="100 g cream\n1 dragonfruit"),
                         mapper=lambda names: {"dragonfruit": "not_an_ingredient"})
    assert next(ln for ln in res.lines if ln.raw == "1 dragonfruit").status == "unmatched"


def test_recipe_with_nothing_recognised_is_a_validation_error(fx_state, fx_dataset):
    with pytest.raises(TasteSpaceError) as exc:
        analyze_recipe(fx_state, fx_dataset, RecipeRequest(text="1 dragonfruit"))
    assert exc.value.code == "validation_error"

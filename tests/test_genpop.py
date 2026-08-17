"""Tests for the v1 structural layout (see references/specs/structural-layout-v1.md)."""
import os
import string
from collections import Counter

from genpop import generate_agents

def test_module_count(fresh_layout, params_no_overflow):
    assert len(fresh_layout.modules) == params_no_overflow["modules"]["count"]


def test_module_letters(fresh_layout):
    assert [m.letter for m in fresh_layout.modules.values()] == list(
        string.ascii_uppercase[0 : len(fresh_layout.modules)]
    )


def test_total_cell_count(fresh_layout, params_no_overflow):
    n_gp_cells = (
        sum([tier["cells_per_tier"] for tier in params_no_overflow["tiers"]])
        * params_no_overflow["cells"]["gp"]["default_bunk_capacity"]
    )
    assert (
        sum([len(module.cells) for module in fresh_layout.modules.values()])
        == n_gp_cells
    )

    n_special = sum(
        [len(module.cells) for module in fresh_layout.shared_modules.values()]
    )
    assert (
        sum([special["count"] for special in params_no_overflow["cells"]["special"]])
        == n_special
    )


def test_each_module_has_58_gp_cells(fresh_layout):
    for module in fresh_layout.modules.values():
        gp = [cell for cell in module.cells if cell.housing_category == "gp"]
        assert len(gp) == 40


def test_each_module_has_two_tiers_of_20(fresh_layout):
    for module in fresh_layout.modules.values():
        bottom = [cell for cell in module.cells if cell.tier == "bottom"]
        top = [cell for cell in module.cells if cell.tier == "top"]
        assert len(bottom) == len(top) == 20


def test_rh_cell_count(fresh_layout):
    assert len(fresh_layout.shared_modules["segregation"].cells) == 30


def test_mi_cell_count(fresh_layout):
    assert len(fresh_layout.shared_modules["medical"].cells) == 20


def test_shared_places_per_type(fresh_layout, params_no_overflow):
    expected = {
        "gym": 1,
        "yard": 1,
        "education": 1,
        "industry": 1,
        "visit_room": 1,
        "chapel": 1,
        "barber": 1,
    }
    values = [d.place_type for d in fresh_layout.shared_places.values()]
    assert dict(Counter(values)) == expected
    for module in fresh_layout.modules.values():
        assert len(module.showers) == 1
        assert len(module.dayrooms) == 1
    assert len(fresh_layout.cafeterias) == 2


def test_subplace_module(fresh_layout):
    for p in fresh_layout.shared_places.values():
        if p.place_type in ("dayroom", "shower"):
            assert p.module_id != 2011
        else:
            assert p.module_id == 2011


def test_place_ids_globally_unique(places):
    assert len(places["place_id"]) == len(set(places["place_id"]))

def test_generate_schedule():
    schedule = generate_agents.generate_schedule(0)
    for activity in schedule:
        assert activity[1] % 60 == 0, "Activities should be hourly"

def test_generate_schedules(tmp_path_factory):
    d = tmp_path_factory.mktemp("schedules")
    generate_agents.generate_schedules(10, os.path.join(str(d), "schedules.csv"))
    with open(os.path.join(str(d), "schedules.csv")) as f:
        schedules = f.readlines()[1:]
    schedule_ids = []
    for line in schedules:
        schedule_ids.append(line[0])

    assert len(set(schedule_ids)) == 10, "Did not create correct number of schedules"

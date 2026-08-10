"""Tests for the v1 structural layout (see references/specs/structural-layout-v1.md)."""

import os
import string
import pytest
from collections import Counter
from pandas import read_csv

import pytest
from pandas import DataFrame, read_csv

from genpop import generate_agents, generate_layout
from radmodel.layout import Layout


@pytest.fixture(scope="session")
def fresh_layout(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate_layout.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
        os.path.join(str(d), "ng_places.csv"),
    )
    layout = Layout()
    layout.load_places(str(d))
    return layout

@pytest.fixture(scope="session")
def overflow_layout(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate_layout.generate_places(
        "./tests/test_params/module_with_overflow.yaml",
        os.path.join(str(d), "ng_places.csv"),
    )
    layout = Layout()
    layout.load_places(str(d))
    return layout

@pytest.fixture(scope="session")
def places(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
        os.path.join(str(d), "ng_places.csv"),
    )
    return read_csv(os.path.join(str(d), "ng_places.csv"))


@pytest.fixture(scope="session")
def params_no_overflow():
    return generate_layout.get_params("./tests/test_params/module_no_overflow.yaml")[
        "facility"
    ]

@pytest.fixture(scope="session")
def params_with_overflow():
    return generate_layout.get_params("./tests/test_params/module_with_overflow.yaml")[
        "facility"
    ]

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


def test_each_module_has_40_gp_cells(fresh_layout):
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


def test_resident_count(fresh_layout):
    assert len(fresh_layout.cell_assignments) == 1200


def test_resident_ids_are_dense_and_unique(fresh_layout):
    ids = [a.person_id for a in fresh_layout.cell_assignments]
    assert sorted(ids) == list(range(1200))


def test_residents_assigned_only_to_gp_cells(fresh_layout):
    gp_ids = {c.place_id for c in fresh_layout.cells_by_category("GP")}
    for a in fresh_layout.cell_assignments:
        assert a.cell_place_id in gp_ids


def test_no_cell_oversubscribed(fresh_layout):
    by_cell: dict = {}
    for a in fresh_layout.cell_assignments:
        by_cell.setdefault(a.cell_place_id, []).append(a)
    cells_by_id = {c.place_id: c for c in fresh_layout.cells}
    for cid, assigns in by_cell.items():
        assert len(assigns) <= cells_by_id[cid].bunk_capacity


def test_shared_places_total(fresh_layout):
    # 2 dayrooms + 2 showers + 2 dining + 9 single-instance facility-shared
    assert len(fresh_layout.shared_places) == 13


def test_shared_places_per_type(fresh_layout):
    expected = {
        "dayroom": 2,
        "shower": 2,
        "dining_room": 2,
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


def test_subplace_module(fresh_layout):
    for p in fresh_layout.shared_places.values():
        if p.place_type in ("dayroom", "shower"):
            assert p.module_id != 2011
        else:
            assert p.module_id == 2011


def test_fk_module_ids_valid(fresh_layout):
    valid = {m.module_id for m in fresh_layout.modules}
    for c in fresh_layout.cells:
        if c.module_id is not None:
            assert c.module_id in valid
    for p in fresh_layout.shared_places:
        if p.parent_module_id is not None:
            assert p.parent_module_id in valid


def test_place_ids_globally_unique(fresh_layout):
    all_ids = [c.place_id for c in fresh_layout.cells] + [
        p.place_id for p in fresh_layout.shared_places
    ]
    assert len(set(all_ids)) == len(all_ids)


def test_generate_agents_unique_id(fresh_layout, params_no_overflow, tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    agents = DataFrame(generate_agents.generate_persons(
        fresh_layout, params_no_overflow["residents"]["count"], os.path.join(str(d), "ng_places.csv")
    ))
    assert agents["person_id"].is_unique, "Agent ids are non-unique"

def test_cells_not_full(fresh_layout, params_no_overflow, tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    DataFrame(generate_agents.generate_persons(
        fresh_layout, params_no_overflow["residents"]["count"], os.path.join(str(d), "ng_agents.csv")
    ))

    agents = read_csv(os.path.join(str(d), "ng_agents.csv"))
    occupants = agents.groupby("cell_place_id").count()["person_id"]
    assert min(occupants) == 1, f"Cells should have at least 1 occupant, found {min(occupants)}"
    assert max(occupants) == params_no_overflow["cells"]["gp"]["default_bunk_capacity"], f"Expected no overflow, found overflow {max(occupants)} per cell"

def test_cells_overflow(overflow_layout, params_with_overflow, tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    DataFrame(generate_agents.generate_persons(overflow_layout, params_with_overflow["residents"]["count"], os.path.join(str(d), "ng_agents.csv")))

    agents = read_csv(os.path.join(str(d), "ng_agents.csv"))
    occupants = agents.groupby("cell_place_id").count()["person_id"]
    assert min(occupants) >= params_with_overflow["cells"]["gp"]["default_bunk_capacity"], f"Cells must have at least default occupancy. Current min occupancy: {min(occupants)}"
    assert max(occupants) > params_with_overflow["cells"]["gp"]["default_bunk_capacity"], f"Cells must overflow. Current max occupancy: {max(occupants)}"
    

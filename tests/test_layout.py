"""Tests for the v1 structural layout (see references/specs/structural-layout-v1.md)."""

import os
import string
import pytest

from genpop import generate
from radmodel import layout as layout_loader


@pytest.fixture(scope="session")
def fresh_layout(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
        os.path.join(str(d), "ng_places.csv"),
    )
    return layout_loader.load_layout(str(d))


@pytest.fixture(scope="session")
def params_no_overflow():
    return generate.get_params("./tests/test_params/module_no_overflow.yaml")[
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


def test_each_module_has_58_gp_cells(fresh_layout):
    for m in fresh_layout.modules:
        gp = [
            c
            for c in fresh_layout.cells_by_module(m.module_id)
            if c.housing_category == "GP"
        ]
        assert len(gp) == 58


def test_each_module_has_two_tiers_of_29(fresh_layout):
    for m in fresh_layout.modules:
        cells = fresh_layout.cells_by_module(m.module_id)
        bottom = [c for c in cells if c.tier == "bottom"]
        top = [c for c in cells if c.tier == "top"]
        assert len(bottom) == 29
        assert len(top) == 29


def test_rh_cell_count(fresh_layout):
    assert len(fresh_layout.cells_by_category("RH")) == 30


def test_mi_cell_count(fresh_layout):
    assert len(fresh_layout.cells_by_category("MI")) == 20


def test_overflow_is_four_triples_per_module_in_bottom_tier(fresh_layout):
    for m in fresh_layout.modules:
        triples = [
            c for c in fresh_layout.cells_by_module(m.module_id) if c.bunk_capacity == 3
        ]
        assert len(triples) == 4
        assert all(c.tier == "bottom" for c in triples)


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
    # 10 dayrooms + 10 showers + 2 dining + 9 single-instance facility-shared
    assert len(fresh_layout.shared_places) == 31


def test_shared_places_per_type(fresh_layout):
    expected = {
        "dayroom": 10,
        "shower": 10,
        "dining_room": 2,
        "gym": 1,
        "yard": 1,
        "education": 1,
        "industry": 1,
        "visit_room": 1,
        "medical": 1,
        "chapel": 1,
        "barber": 1,
        "segregation": 1,
    }
    for place_type, count in expected.items():
        assert len(fresh_layout.shared_places_by_type(place_type)) == count, place_type


def test_module_subplaces_have_parent_others_dont(fresh_layout):
    for p in fresh_layout.shared_places:
        if p.place_type in ("dayroom", "shower"):
            assert p.parent_module_id is not None
        else:
            assert p.parent_module_id is None


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

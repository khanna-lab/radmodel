"""Tests for the v1 structural layout (see references/specs/structural-layout-v1.md)."""

import os
import string
import pytest
from collections import Counter
from pandas import read_csv
import numpy as np

from genpop import generate
from radmodel.layout import Layout


@pytest.fixture(scope="session")
def fresh_layout(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
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


def test_place_ids_globally_unique(places):
    assert len(places["place_id"]) == len(set(places["place_id"]))


def test_get_counts_no_agents(fresh_layout):
    idxs = [i for i in fresh_layout.places_id_map.values()]
    assert not fresh_layout.get_counts(idxs).any(), "New array of counts should be zero."
    assert not fresh_layout.get_all_counts().any(), "New array of counts should be zero."

def test_update_get_counts(fresh_layout):
    idxs = [i for i in fresh_layout.places_id_map.values()]
    counts = [np.random.choice([0,3]) for _ in idxs]
    fresh_layout.update_counts(places=idxs, counts=counts)
    # all counts
    actual_get_counts = [i[0] for i in fresh_layout.get_counts(idxs)]
    actual_get_all_counts = [i[0] for i in fresh_layout.get_all_counts()]
    assert counts == actual_get_counts
    assert counts == actual_get_all_counts
    # Only get first 20
    actual_get_counts = [i[0] for i in fresh_layout.get_counts(idxs[0:20])]
    assert actual_get_counts == counts[0:20]


def test_update_infected_get_infected_counts(fresh_layout):
    idxs = [i for i in fresh_layout.places_id_map.values()]
    infected_counts = [np.random.choice([0,3]) for _ in idxs]
    fresh_layout.update_infected_counts(places=idxs, counts=infected_counts)
    found_counts = [i[1] for i in fresh_layout.get_counts(idxs)]
    assert infected_counts == found_counts


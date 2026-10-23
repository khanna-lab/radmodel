import os
import random

import pytest
from mpi4py import MPI
from pandas import read_csv

from genpop import generate_agents, generate_layout
from radmodel.core import Model, create_duration_matrix, create_trans_matrix
from radmodel.layout import Layout
from radmodel.population import Places, create_residents, create_schedules


@pytest.fixture(scope="session")
def fresh_layout(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate_layout.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
        os.path.join(str(d), "places.csv"),
    )
    layout = Layout()
    layout.load_places(str(d))
    return layout


@pytest.fixture(scope="session")
def places(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate_layout.generate_places(
        "./tests/test_params/module_no_overflow.yaml",
        os.path.join(str(d), "places.csv"),
    )
    return read_csv(os.path.join(str(d), "places.csv"))


@pytest.fixture(scope="session")
def params_no_overflow():
    return generate_layout.get_params("./tests/test_params/module_no_overflow.yaml")[
        "facility"
    ]


@pytest.fixture(scope="session")
def agents(tmp_path_factory):
    # set seed for reproducibility
    random.seed(1)
    d = tmp_path_factory.mktemp("agents")
    return generate_agents.generate_agents(
        100, "./tests/test_params", os.path.join(str(d), "residents.csv")
    )


@pytest.fixture(scope="session")
def model_params(tmp_path_factory):
    params = generate_layout.get_params("./tests/test_params/radmodel_params.yaml")
    params["schedule_file"] = "./tests/test_params/schedules.csv"
    params["places_file"] = "./tests/test_params/places.csv"
    params["residents_file"] = "./tests/test_params/residents.csv"
    d = tmp_path_factory.mktemp("outputs")
    params["output_dir"] = d
    params["counts_log_file"] = os.path.join(str(d), "counts.csv")
    params["places_log_file"] = os.path.join(str(d), "counts_by_place.csv")
    return params


@pytest.fixture(scope="session")
def fresh_model(model_params, fresh_layout):
    schedule = create_schedules(model_params["schedule_file"])
    return Model(
        comm=MPI.COMM_WORLD,
        schedule_data=schedule,
        person_data=create_residents("./tests/test_params/residents.csv"),
        place_data=Places(fresh_layout.place_data),
        stoe=model_params["stoe"],
        trans_matrix=create_trans_matrix(model_params["transition_matrix"]),
        duration_matrix=create_duration_matrix(model_params),
        seed=model_params["random_seed"],
        params=model_params,
    )

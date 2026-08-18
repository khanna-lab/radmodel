import os

import pytest
from pandas import read_csv

from genpop import generate_agents, generate_layout
from radmodel.layout import Layout

# from radmodel.population import Schedule


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
def places(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    generate_layout.generate_places(
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
def agents(tmp_path_factory):
    d = tmp_path_factory.mktemp("agents")
    generate_agents.generate_agents(100, "test_params/places.csv", os.path.join(str(d), "ng_agents.csv"))

# @pytest.fixture(scope="session")
# def schedule(tmp_path_factory, places):
#     d = tmp_path_factory.mktemp("layout")
#     generate_layout.generate_places(
#         "./tests/test_params/module_no_overflow.yaml",
#         os.path.join(str(d), "ng_places.csv"),
#     )
#     generate_agents.generate_agents(
#         100,
#         os.path.join(str(d), "ng_places.csv"),
#         os.path.join(str(d), "ng_agents.csv"),
#     )
#     return Schedule.create_schedules()

    # d = tmp_path_factory.mktemp("agents")
    # agents = generate_agents.generate_agents(100, places, )
    # return Schedule.create_schedules("./tests/test_params/schedule.csv")

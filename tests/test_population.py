import polars as pl
from polars.testing import assert_frame_equal

from radmodel.layout import Layout
from radmodel.population import Places, create_residents, create_schedules


def test_create_schedules():
    schedules = create_schedules("./tests/test_params/schedules.csv")
    num_schedules = schedules.unique("schedule_id").select(pl.len()).item(0, 0)
    assert schedules.shape[0] == num_schedules * 1440, (
        f"Wrong number of schedules or timesteps. Expected 10*1440, got {schedules.shape[0]}."
    )
    assert schedules.shape[1] == 6, (
        f"Wrong number of columns in schedules df. Expected 6, got {schedules.shape[1]}."
    )


def test_create_residents():
    residents = create_residents("./tests/test_params/residents.csv")
    assert residents.shape == residents.unique("agent_id").shape, residents


def test_update_infected_counts():
    place_data = Layout.load_from_csv("./tests/test_params")
    residents = create_residents("./tests/test_params/residents.csv")
    new_states = ["susceptible"] * 50 + ["infected_asymp"] * 25 + ["hospitalized"] * 25
    residents = residents.with_columns(state=pl.Series(new_states))
    places = Places(place_data.place_data)
    places.update_infected_counts(residents)
    assert_frame_equal(
        places.place_data.sum().select("infected_count"),
        pl.DataFrame({"infected_count": 50}),
        check_dtypes=False,
    )

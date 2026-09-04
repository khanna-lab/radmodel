import polars as pl

from radmodel.layout import Layout
from radmodel.population import create_residents, create_schedules, Places


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
    assert residents.shape[0] == residents.unique("agent_id").select(pl.len()).item(
        0, 0
    )


def test_update_infected_counts():
    place_data = Layout.load_from_csv("./tests/test_params")
    places = Places(place_data.place_data)
    places.update_infected_counts(
        pl.DataFrame({"place_id": [1002], "infected_count": [20]})
    )
    assert places.place_data.filter(pl.col("place_id") == 1002).select("infected_count").item(0,0) == 20, "Infected count did not update."
    all_zero = places.place_data.filter(pl.col("place_id")!=1002).select("infected_count")
    assert all_zero.unique("infected_count").shape[0] == 1, "Some incorrect infection counts updated."
    assert all_zero.select("infected_count").item(0,0) == 0, "Incorrect infection counts updated."


import polars as pl
from polars.testing import assert_frame_equal


def test_init_model(fresh_model, model_params):
    assert fresh_model.agent_data.shape == (100, 11)
    assert fresh_model.agent_data.columns == [
        "module_id",
        "schedule_id",
        "cafeteria",
        "morning_act",
        "afternoon_act",
        "evening_act",
        "agent_id",
        "cell",
        "state",
        "next_transition",
        "current_place",
    ]
    assert fresh_model.current_agent_data.columns == [
        "module_id",
        "schedule_id",
        "cafeteria",
        "morning_act",
        "afternoon_act",
        "evening_act",
        "agent_id",
        "cell",
        "state",
        "next_transition",
        "current_place",
        "start",
        "end",
        "place_type",
        "risk",
        "t",
    ]
    assert fresh_model.current_agent_data.shape == (100, 16)
    exposed = fresh_model.agent_data.filter(pl.col("state") == "exposed")
    assert len(exposed) == model_params["init_exposed"], (
        f"Number of exposed agents should be {model_params['init_exposed']}. Got {len(exposed)}."
    )
    assert len(exposed.select(pl.col("next_transition")).unique()) == len(exposed), (
        "Next transition values should be unique."
    )  # TODO this may not hold, tests need a set seed


def test_select_next_place_cell(fresh_model):
    # All agents in cell at t=0
    fresh_model.select_next_place(0)
    joined = fresh_model.current_agent_data.join(fresh_model.agent_data, on="agent_id")
    assert_frame_equal(
        joined,
        joined.filter(pl.col("cell") == pl.col("current_place")),
    )


def test_select_next_place_cafeteria(fresh_model):
    fresh_model.select_next_place(360)
    joined = fresh_model.current_agent_data.join(fresh_model.agent_data, on="agent_id")
    assert_frame_equal(
        joined,
        joined.filter(pl.col("cafeteria") == pl.col("current_place")),
    )


def test_select_next_place_morning(fresh_model):
    # agent morning activities
    fresh_model.select_next_place(420)
    joined = fresh_model.current_agent_data.join(fresh_model.agent_data, on="agent_id")
    assert_frame_equal(
        joined,
        joined.filter(pl.col("morning_act") == pl.col("current_place")),
    )
    assert len(joined.unique("current_place")) != 1, (
        "All agents should not have same morning activities."
    )
    assert len(joined.unique("current_place")) != len(joined), (
        "Morning activities should not be fully unique."
    )

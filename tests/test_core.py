import polars as pl
from polars.testing import assert_frame_equal


def test_init_model(fresh_model, model_params):
    assert fresh_model.agent_data.shape == (100, 14)
    exposed = fresh_model.agent_data.filter(pl.col("state") == "exposed")
    assert len(exposed) == model_params["init_exposed"], (
        f"Number of exposed agents should be {model_params['init_exposed']}. Got {len(exposed)}."
    )
    assert len(exposed.select(pl.col("next_transition")).unique()) == len(exposed), (
        "Next transition values should be unique."
    )  # TODO this may not hold, tests need a set seed


def test_select_next_place(fresh_model):
    # All agents in cell at t=0
    fresh_model.select_next_place(0)
    assert_frame_equal(
        fresh_model.current_agent_data.filter(
            pl.col("cell") == pl.col("current_place")
        ),
        fresh_model.current_agent_data,
    )
    # Agents should be at cafeteria at t=360
    fresh_model.select_next_place(360)
    assert_frame_equal(
        fresh_model.current_agent_data.filter(
            pl.col("cafeteria") == pl.col("current_place")
        ),
        fresh_model.current_agent_data,
    )

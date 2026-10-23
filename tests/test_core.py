import polars as pl


def test_init_model(fresh_model, model_params):
    assert fresh_model.agent_data.shape == (100, 13)
    exposed = fresh_model.agent_data.filter(pl.col("state") == "exposed")
    assert len(exposed) == model_params["init_exposed"], (
        f"Number of exposed agents should be {model_params['init_exposed']}. Got {len(exposed)}."
    )
    assert len(exposed.select(pl.col("next_transition")).unique()) == len(exposed), (
        "Next transition values should be unique."
    )  # TODO this may not hold, tests need a set seed

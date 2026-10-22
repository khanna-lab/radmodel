# TODO rewrite core tests


def test_init_model(fresh_model):
    assert fresh_model.agent_data.shape == (100, 13)

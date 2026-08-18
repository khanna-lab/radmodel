from radmodel.population import Schedule


def test_parse_schedules():
    schedule = Schedule._parse_schedules("./tests/test_params/schedules.csv")
    assert len(schedule.keys()) == 10, f"Should have 10 schedules, got {len(schedule.keys())}"
    for key, sched in schedule.items():
        assert key in range(10), "Key not recognized. Got {key}, should be in 1-10."
        for val in sched:
            assert val.place_type in ["cell", "cafeteria", "morning_act", "noon_act", "outdoor"], f"Place type not recognized. Found {val.place_type}"
            assert val.id == key


def test_schedule_rows_to_array():
    schedule_data = Schedule._parse_schedules("./tests/test_params/schedules.csv")
    rows = next(iter(schedule_data.values()))
    (np_data, risks) = Schedule._schedule_rows_to_array(rows)
    for row in np_data:
        assert row in ["cell", "cafeteria", "morning_act", "noon_act", "outdoor"], f"Place type not recognized. Found {row}"
    for risk in risks:
        assert risk == 1

def test_create_schedules():
    schedule = Schedule.create_schedules("./tests/test_params/schedules.csv")
    assert len(schedule.schedule_data.keys()) == 10, f"Should have 10 schedules, got {len(schedule.schedule_data.keys())}"
    for key, sched in schedule.schedule_data.items():
        assert key in range(10), "Key not recognized. Got {key}, should be in 1-10."
        for val in sched:
            assert val.place_type in ["cell", "cafeteria", "morning_act", "noon_act", "outdoor"], f"Place type not recognized. Found {val.place_type}"
            assert val.id == key


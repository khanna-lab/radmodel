import numpy as np
import yaml

from radmodel import population, common, core


def _create_s1_expected():
    vals = [population.P_CELL_IDX for _ in range(int((420 - 0) / 15))]
    vals += [population.P_CAFS_IDX for _ in range(int((480 - 420) / 15))]
    vals += [population.P_ACTS_IDX for _ in range(int((660 - 480) / 15))]
    vals += [population.P_CAFS_IDX for _ in range(int((720 - 660) / 15))]
    vals += [population.P_ACTS_IDX for _ in range(int((840 - 720) / 15))]
    vals += [population.P_OUTDOOR_IDX for _ in range(int((900 - 840) / 15))]
    vals += [population.P_ACTS_IDX for _ in range(int((1020 - 900) / 15))]
    vals += [population.P_CAFS_IDX for _ in range(int((1140 - 1020) / 15))]
    vals += [population.P_CELL_IDX for _ in range(int((1440 - 1140) / 15))]
    place_idxs = np.array(vals, dtype=np.int32)

    vals = [1.0 for _ in range(int((420 - 0) / 15))]
    vals += [1.0 for _ in range(int((480 - 420) / 15))]
    vals += [1.0 for _ in range(int((600 - 480) / 15))]
    vals += [1.5 for _ in range(int((660 - 600) / 15))]
    vals += [1.0 for _ in range(int((720 - 660) / 15))]
    vals += [1.0 for _ in range(int((780 - 720) / 15))]
    vals += [0.8 for _ in range(int((840 - 780) / 15))]
    vals += [1.0 for _ in range(int((900 - 840) / 15))]
    vals += [1.0 for _ in range(int((1020 - 900) / 15))]
    vals += [1.0 for _ in range(int((1140 - 1020) / 15))]
    vals += [1.0 for _ in range(int((1440 - 1140) / 15))]
    risks = np.array(vals, dtype=np.float32)

    return place_idxs, risks


def _init_data():
    fname = "./test_data/schedules.csv"
    schedule_id_map, schedule_data, risks = population.create_schedules(fname)
    fname = "./test_data/places.csv"
    place_id_map, place_data = population.create_places(fname)

    fname = "./test_data/residents.csv"
    residents = population.create_residents(fname, place_id_map, schedule_id_map)

    params_fname = "./test_data/params.yaml"
    with open(params_fname) as fin:
        params = yaml.safe_load(fin)

    return schedule_data, risks, place_data, residents, params


def test_create_schedule():
    fname = "./test_data/schedules.csv"
    id_map, schedules, risks = population.create_schedules(fname)
    assert 10 == len(id_map)
    assert {i: i for i in range(10)} == id_map
    # 1D array of place types
    assert ((common.TICKS_PER_DAY * len(id_map),)) == schedules.shape
    assert ((common.TICKS_PER_DAY * len(id_map),)) == risks.shape
    s1 = schedules[96: 192]
    r1 = risks[96: 192]
    s1_exp, risks_exp = _create_s1_expected()
    assert np.array_equal(s1, s1_exp)
    assert np.array_equal(r1, risks_exp)


def test_create_places():
    fname = "./test_data/places.csv"
    place_id_map, places = population.create_places(fname)
    assert (113, 3) == places.shape
    assert {i: i for i in range(113)} == place_id_map


def test_create_residents():
    residents = _init_data()[3]
    assert (20, population.N_P_ELEMENTS) == residents.shape

    resident = residents[17]
    assert np.array_equal(np.array([17, 5, 4, 4, 102, 104, 106, 107, 108,
                                    common.SUSCEPTIBLE, np.iinfo(np.uint32).max], dtype=np.uint32),
                          resident)


def test_select_next_place():
    schedule_data, _, place_data, residents, params = _init_data()
    duration_matrix = core.create_duration_matrix(params)
    trans_matrix = core.create_trans_matrix(params["transition_matrix"])
    model = core.Model(schedule_data, residents, place_data, 0.0, trans_matrix, duration_matrix,
                       params["random_seed"])
    for i in range(144):
        model.select_next_place(i)
        for x in range(20):
            schedule_idx = residents[x, population.P_SCHEDULE_IDX] * 96 + (i % common.TICKS_PER_DAY)
            person_place_col_idx = schedule_data[schedule_idx]
            assert residents[x, population.P_CURRENT_PLACE_IDX] == residents[x, person_place_col_idx]


def test_select_next_place_count():
    schedule_data, _, place_data, residents, params = _init_data()
    duration_matrix = core.create_duration_matrix(params)
    trans_matrix = core.create_trans_matrix(params["transition_matrix"])

    model = core.Model(schedule_data, residents, place_data, 0.0, trans_matrix, duration_matrix,
                       params["random_seed"])
    for i in range(144):
        model.select_next_place(i)
        counts = {}
        for x in range(20):
            place_idx = residents[x, population.P_CURRENT_PLACE_IDX]
            if place_idx in counts:
                counts[place_idx] += 1
            else:
                counts[place_idx] = 1

        for k, v in counts.items():
            assert model.place_data[k, population.PL_PERSON_COUNT_IDX] == v


def test_select_next_place_inf_count():
    schedule_data, _, place_data, residents, params = _init_data()
    duration_matrix = core.create_duration_matrix(params)
    trans_matrix = core.create_trans_matrix(params["transition_matrix"])

    model = core.Model(schedule_data, residents, place_data, 0.0, trans_matrix, duration_matrix,
                       params["random_seed"])
    residents[0, population.P_STATE_IDX] = common.INFECTED_ASYMP
    residents[1, population.P_STATE_IDX] = common.PRESYMPTOMATIC
    residents[17, population.P_STATE_IDX] = common.INFECTED_SYMP

    for i in range(144):
        model.select_next_place(i)
        inf_counts = {}
        for x in range(20):
            inf_x = x == 0 or x == 1 or x == 17
            place_idx = residents[x, population.P_CURRENT_PLACE_IDX]
            if inf_x:
                if place_idx in inf_counts:
                    inf_counts[place_idx] += 1
                else:
                    inf_counts[place_idx] = 1

        for k, v in inf_counts.items():
            assert model.place_data[k, population.PL_INFECTED_COUNT_IDX] == v


def test_transition_matrix():
    schedule_data, _, place_data, all_residents, params = _init_data()
    # update everyone with schedule 17 to same restaurant
    residents = all_residents[all_residents[:, population.P_SCHEDULE_IDX] == 17]

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)

    # test cum sum output
    np_trans_matrix = model.trans_matrix
    exp = np.array([[0.0, 0.0, 0., 0., 0., 0., 0., 0., ],
                    [0., 0., 0.8, 0., 0.2, 0., 0., 0.],
                    [0., 0., 0., 1., 0., 0., 0., 0.],
                    [0., 0., 0., 0., 0., 0.9, 0.1, 0.],
                    [0., 0., 0., 0., 0., 1., 0., 0., ],
                    [1., 0., 0., 0., 0., 0., 0., 0., ],
                    [0., 0., 0., 0., 0., 0.95, 0., 0.05],
                    [0., 0., 0., 0., 0., 0., 0., 0.]], dtype=np.float32).cumsum(1)
    assert np.array_equal(np_trans_matrix, exp)


def test_duration_matrix():
    params = _init_data()[-1]
    dur_matrix = core.create_duration_matrix(params)
    exp = np.array([
        [0, 0],
        [6, 3.5 / 6],
        [6, 2.5 / 6],
        [6, 10 / 6.0],
        [6, 10 / 6.0],
        [6, 200 / 6],
        [6, 6.5 / 6],
        [0, 0]
    ], dtype=np.float32)
    assert np.array_equal(dur_matrix, exp)


def test_disease_update_always_inf():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect resident 0
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    params["stoe"] = 1.0
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)

    model.select_next_place(44)
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)
    assert residents[0, population.P_STATE_IDX] == common.INFECTED_SYMP

    infected_place = residents[0, population.P_CURRENT_PLACE_IDX]
    colocated = set()
    for x in range(1, residents.shape[0]):
        current_place = residents[x, population.P_CURRENT_PLACE_IDX]
        if current_place == infected_place:
            colocated.add(x)

    colocated_a = np.array(list(colocated))
    for _ in range(100):
        model.update_disease_state(44)
        assert residents[0, population.P_STATE_IDX] == common.INFECTED_SYMP
        # exlude 0 from test
        for x in range(1, residents.shape[0]):
            if x in colocated:
                assert residents[x, population.P_STATE_IDX] == common.EXPOSED
            else:
                assert residents[x, population.P_STATE_IDX] == common.SUSCEPTIBLE
        # reset colocated back to SUSCEPTIBLE
        residents[colocated_a, population.P_STATE_IDX] = common.SUSCEPTIBLE


def test_disease_update_never_inf():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect resident 0
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    params["stoe"] = 0.0
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)

    model.select_next_place(44)
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)
    assert residents[0, population.P_STATE_IDX] == common.INFECTED_SYMP

    infected_place = residents[0, population.P_CURRENT_PLACE_IDX]
    colocated = set()
    for x in range(1, residents.shape[0]):
        current_place = residents[x, population.P_CURRENT_PLACE_IDX]
        if current_place == infected_place:
            colocated.add(x)

    assert len(colocated) > 0

    for _ in range(100):
        model.update_disease_state(44)
        assert residents[0, population.P_STATE_IDX] == common.INFECTED_SYMP
        # exlude 0 from test
        for x in range(1, residents.shape[0]):
            assert residents[x, population.P_STATE_IDX] == common.SUSCEPTIBLE


def test_disease_update_50p_inf():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect resident 0
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    params["stoe"] = 0.5
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)

    model.select_next_place(44)
    assert np.all(residents[1:, population.P_STATE_IDX] == common.SUSCEPTIBLE)
    assert residents[0, population.P_STATE_IDX] == common.INFECTED_SYMP

    infected_place = residents[0, population.P_CURRENT_PLACE_IDX]
    colocated = set()
    for x in range(1, residents.shape[0]):
        current_place = residents[x, population.P_CURRENT_PLACE_IDX]
        if current_place == infected_place:
            colocated.add(x)

    assert len(colocated) > 0

    n_exposed = 0
    for _ in range(1000):
        model.update_disease_state(44)
        n_exposed += np.count_nonzero(residents[1:, population.P_STATE_IDX] == common.EXPOSED)
        residents[1:, population.P_STATE_IDX] = common.SUSCEPTIBLE

    # 2K chances to be exposed with 50% probability so 100 either way
    # should be good
    assert n_exposed < 1100 and n_exposed > 900


def test_update_disease_states1():
    schedule_data, _, place_data, residents, params = _init_data()

    # resident 0 to exposed, transitions at 10
    residents[:2, population.P_STATE_IDX] = common.EXPOSED
    residents[:2, population.P_NEXT_STATE_T_IDX] = 10

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P
    transition_matrix["E"]["P"] = 1.0
    transition_matrix["E"]["I_A"] = 0
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    model.update_disease_state(10)
    assert np.all(residents[:2, population.P_STATE_IDX] == common.PRESYMPTOMATIC)
    assert np.all(residents[2:, population.P_STATE_IDX] == common.SUSCEPTIBLE)

    # try 75, 25 chance
    transition_matrix["E"]["P"] = .75
    transition_matrix["E"]["I_A"] = .25
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    n_presym = 0
    n_ia = 0
    for _ in range(4000):
        residents[:2, population.P_STATE_IDX] = common.EXPOSED
        residents[:2, population.P_NEXT_STATE_T_IDX] = 10
        model.update_disease_state(10)
        n_presym += np.count_nonzero(residents[:2, population.P_STATE_IDX] == common.PRESYMPTOMATIC)
        n_ia += np.count_nonzero(residents[:2, population.P_STATE_IDX] == common.INFECTED_ASYMP)

    assert n_presym > 5900 and n_presym < 6100
    assert n_ia > 1900 and n_ia < 2100


def test_update_disease_states2():
    schedule_data, _, place_data, residents, params = _init_data()

    # assign states to persons
    residents[1, population.P_STATE_IDX] = common.EXPOSED
    residents[1, population.P_NEXT_STATE_T_IDX] = 11
    residents[2, population.P_STATE_IDX] = common.PRESYMPTOMATIC
    residents[2, population.P_NEXT_STATE_T_IDX] = 10

    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P
    transition_matrix["E"]["P"] = 1.0
    transition_matrix["E"]["I_A"] = 0
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    model.update_disease_state(10.0)
    assert residents[1, population.P_STATE_IDX] == common.EXPOSED
    assert residents[2, population.P_STATE_IDX] == common.INFECTED_SYMP

    model.update_disease_state(11.0)
    assert residents[1, population.P_STATE_IDX] == common.PRESYMPTOMATIC
    assert residents[2, population.P_STATE_IDX] == common.INFECTED_SYMP


def test_disease_state_paths1():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect 1 to infect others
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P

    transition_matrix["E"]["P"] = 1.0
    transition_matrix["E"]["I_A"] = 0

    transition_matrix["I_S"]["H"] = 1.0
    transition_matrix["I_S"]["R"] = 0

    transition_matrix["H"]["R"] = 1.0
    params["stoe"] = 1.0

    params["presymptomatic_duration_k"] = 12
    params["presymptomatic_duration_mean"] = 4.92
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    # go to caf and become exposed
    tick = 44
    model.select_next_place(tick)
    model.update_disease_state(tick)

    # 9 and 13 should be colocated and exposed to 0
    assert residents[9, population.P_STATE_IDX] == common.EXPOSED
    assert residents[13, population.P_STATE_IDX] == common.EXPOSED
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    # https://homepage.divms.uiowa.edu/~mbognar/applets/gamma.html
    assert duration_t > 0.5 * 96 + tick and duration_t < 8.0 * 96 + tick
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    # https://homepage.divms.uiowa.edu/~mbognar/applets/gamma.html
    assert duration_t > 0.5 * 96 + tick and duration_t < 8.0 * 96 + tick

    # now follow just 13 using its duration_t
    model.update_disease_state(duration_t - 1)
    assert residents[13, population.P_STATE_IDX] == common.EXPOSED

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.PRESYMPTOMATIC
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 1.9 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    model.update_disease_state(duration_t - 1)
    assert residents[13, population.P_STATE_IDX] == common.PRESYMPTOMATIC

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.INFECTED_SYMP
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 2.5 * common.TICKS_PER_DAY + tick and duration_t < 20.0 * common.TICKS_PER_DAY + tick

    model.update_disease_state(duration_t - 1)
    assert residents[13, population.P_STATE_IDX] == common.INFECTED_SYMP

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.HOSPITALIZED
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 1.5 * common.TICKS_PER_DAY + tick and duration_t < 12.5 * common.TICKS_PER_DAY + tick

    model.update_disease_state(duration_t - 1)
    assert residents[13, population.P_STATE_IDX] == common.HOSPITALIZED

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.RECOVERED
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 50 * common.TICKS_PER_DAY + tick and duration_t < 400 * common.TICKS_PER_DAY + tick

    model.update_disease_state(duration_t - 1)
    assert residents[13, population.P_STATE_IDX] == common.RECOVERED

    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.SUSCEPTIBLE


def test_disease_state_paths2():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect 1 to infect others
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P
    params["stoe"] = 1.0

    transition_matrix["E"]["P"] = 0
    transition_matrix["E"]["I_A"] = 1.0

    params["asymptomatic_duration_k"] = 10
    params["asymptomatic_duration_mean"] = 1
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)

    # go to lunch and become exposed
    tick = 44
    model.select_next_place(tick)
    model.update_disease_state(tick)
    assert residents[9, population.P_STATE_IDX] == common.EXPOSED
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    # https://homepage.divms.uiowa.edu/~mbognar/applets/gamma.html
    assert duration_t > 0.5 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.INFECTED_ASYMP
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 0.5 * common.TICKS_PER_DAY + tick and duration_t < 2.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.RECOVERED
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 50 * common.TICKS_PER_DAY + tick and duration_t < 400 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.SUSCEPTIBLE
    duration_t = residents[0, population.P_NEXT_STATE_T_IDX]


def test_disease_state_paths3():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect 1 to infect others
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P
    params["stoe"] = 1.0

    transition_matrix["E"]["P"] = 1.0
    transition_matrix["E"]["I_A"] = 0

    transition_matrix["I_S"]["H"] = 0
    transition_matrix["I_S"]["R"] = 1.0

    params["presymptomatic_duration_k"] = 12
    params["presymptomatic_duration_mean"] = 4.92
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    # go to lunch and become exposed
    tick = 44
    model.select_next_place(tick)
    model.update_disease_state(tick)
    assert residents[13, population.P_STATE_IDX] == common.EXPOSED
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    # https://homepage.divms.uiowa.edu/~mbognar/applets/gamma.html
    assert duration_t > 0.5 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.PRESYMPTOMATIC
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 1.9 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.INFECTED_SYMP
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 2.5 * common.TICKS_PER_DAY + tick and duration_t < 20.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.RECOVERED
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 50 * common.TICKS_PER_DAY + tick and duration_t < 400 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[13, population.P_STATE_IDX] == common.SUSCEPTIBLE
    duration_t = residents[13, population.P_NEXT_STATE_T_IDX]


def test_disease_state_paths4():
    schedule_data, _, place_data, residents, params = _init_data()

    # infect 1 to infect others
    residents[0, population.P_STATE_IDX] = common.INFECTED_SYMP
    transition_matrix = params["transition_matrix"]
    seed = params["random_seed"]
    # force transition from E to P
    params["stoe"] = 1.0

    transition_matrix["E"]["P"] = 1.0
    transition_matrix["E"]["I_A"] = 0

    transition_matrix["I_S"]["H"] = 1.0
    transition_matrix["I_S"]["R"] = 0

    transition_matrix["H"]["D"] = 1.0
    transition_matrix["H"]["R"] = 0.0

    params["presymptomatic_duration_k"] = 12
    params["presymptomatic_duration_mean"] = 4.92
    model = core.Model(schedule_data, residents, place_data, params["stoe"], core.create_trans_matrix(transition_matrix),
                       core.create_duration_matrix(params), seed)
    # go to lunch and become exposed
    tick = 44
    model.select_next_place(tick)
    model.update_disease_state(tick)
    assert residents[9, population.P_STATE_IDX] == common.EXPOSED
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    # https://homepage.divms.uiowa.edu/~mbognar/applets/gamma.html
    assert duration_t > 0.5 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.PRESYMPTOMATIC
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 1.9 * common.TICKS_PER_DAY + tick and duration_t < 8.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.INFECTED_SYMP
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 2.5 * common.TICKS_PER_DAY + tick and duration_t < 20.0 * common.TICKS_PER_DAY + tick

    tick = duration_t
    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.HOSPITALIZED
    duration_t = residents[9, population.P_NEXT_STATE_T_IDX]
    assert duration_t > 1.5 * common.TICKS_PER_DAY + tick and duration_t < 12.5 * common.TICKS_PER_DAY + tick

    model.update_disease_state(duration_t)
    assert residents[9, population.P_STATE_IDX] == common.DEAD

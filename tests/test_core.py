import numpy as np
from mpi4py import MPI

from radmodel import schedule, agents, model


def _create_s0_expected():
    exp = np.zeros((96, 2))
    a = np.array([0, 1])
    exp[0:25][:] = np.tile(a, (25, 1))
    a = np.array([2, 1.5])
    exp[25:30][:] = np.tile(a, (5, 1))
    a = np.array([1, 2])
    exp[30:42][:] = np.tile(a, (12, 1))
    a = np.array([0, 1])
    exp[42:50][:] = np.tile(a, (8, 1))
    a = np.array([2, 1.5])
    exp[50:54][:] = np.tile(a, (4, 1))
    a = np.array([1, 0.5])
    exp[54:66][:] = np.tile(a, (12, 1))
    a = np.array([0, 1])
    exp[66:78][:] = np.tile(a, (12, 1))
    a = np.array([2, 2])
    exp[78:82][:] = np.tile(a, (4, 1))
    a = np.array([0, 0.35])
    exp[82:96][:] = np.tile(a, (14, 1))
    return exp


def test_create_schedule():
    fname = "./data/schedule.csv"
    id_map, schedules = schedule.create_schedules(fname)
    assert 2 == len(id_map)
    assert {0: 0, 3: 1} == id_map
    assert (96 * 2, 2) == schedules.shape
    s0 = schedules[0:96]
    assert np.array_equal(s0, _create_s0_expected())


def test_updater():
    params = {
        "schedule.file": "./data/schedule.csv",
        "prisoner.file": "./data/prisoners.csv"
    }
    updater: model.Updater = model.create_updater(params)
    updater.select_next_place(4)
    assert np.array_equal(updater.next_place[:, 0:2], np.array([[0, 1], [0, 1]]))
    updater.select_next_place(34)
    assert np.array_equal(updater.next_place[:, 0:2], np.array([[1, 2], [0, 1]]))
    updater.select_next_place(94)
    print(updater.next_place)
    assert np.array_equal(updater.next_place[:, 0:2], np.array([[0, 0.35], [0, 0.45]]))


def test_create_prisoners():
    rank = MPI.COMM_WORLD.Get_rank()
    fname = "./data/schedule.csv"
    schedule_id_map, _ = schedule.create_schedules(fname)

    fname = "./data/prisoners.csv"
    prisoner_data = agents.init_prisoner_data(fname, schedule_id_map)
    prisoners = [x for x in agents.create_prisoners(prisoner_data, rank)]
    assert 2 == len(prisoners)
    p1 = prisoners[0]
    assert 0 == p1.idx
    assert 0 == p1.pid
    assert 0 == p1.cell_id
    assert 0 == p1.schedule_id

    p2 = prisoners[1]
    assert 1 == p2.idx
    assert 2 == p2.pid
    assert 1 == p2.schedule_id
    assert 0 == p2.cell_id

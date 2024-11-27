import csv
from typing import Union, Dict, List, Tuple
import os
import numpy as np
from dataclasses import dataclass

from .common import TICKS_PER_DAY, TICK_DURATION, MIDNIGHT, SUSCEPTIBLE

P_DATA_ID_IDX = 0
P_DATA_SCHEDULE_IDX = 1
P_DATA_CELL_IDX = 2
P_DATA_ACTS_IDX = 3
P_DATA_CAFS_IDX = 4
P_DATA_OUT_IDX = 5

P_ACTS_COUNT = 2
P_CAFS_COUNT = 2

P_ID_IDX = 0
P_SCHEDULE_IDX = 1
P_CURRENT_PLACE_IDX = 2
P_CELL_IDX = 3
P_ACTS_IDX = 4
P_CAFS_IDX = P_ACTS_IDX + P_ACTS_COUNT
P_OUTDOOR_IDX = P_CAFS_IDX + P_CAFS_COUNT
# person's current disease state
P_STATE_IDX = P_OUTDOOR_IDX + 1
# next transition time
P_NEXT_STATE_T_IDX = P_STATE_IDX + 1
# total number columns in residents data
N_P_ELEMENTS = P_NEXT_STATE_T_IDX + 1

PL_PERSON_COUNT_IDX = 1
PL_INFECTED_COUNT_IDX = 2


# Maps activity type string in schedule to
# index into the np array of the person data
SCHEDULE_PLACE_TYPE_MAP = {
    "cell": P_CELL_IDX,
    "activity": P_ACTS_IDX,
    "cafeteria": P_CAFS_IDX,
    "outdoor": P_OUTDOOR_IDX,
}


@dataclass
class ScheduleRow:
    id: int
    start: int
    end: int
    place_type: int
    risk: float


def _validate_row(row: ScheduleRow):
    if row.start < 0 or row.start > MIDNIGHT:
        raise ValueError(f"Schedule {row.id} is invalid: {row}")


def _schedule_rows_to_array(rows: List[ScheduleRow]):
    np_data = np.zeros((TICKS_PER_DAY), dtype=np.int32)
    risks = np.zeros((TICKS_PER_DAY), dtype=np.float32)
    rows_index = 0
    row = rows[rows_index]
    for idx in range(0, TICKS_PER_DAY):
        t = idx * TICK_DURATION
        # sorted so can ignore start
        while t >= row.end:
            rows_index += 1
            row = rows[rows_index]

        np_data[idx] = row.place_type
        risks[idx] = row.risk

    return np_data, risks


def _parse_schedules(fname: str | os.PathLike) -> Dict[int, List[ScheduleRow]]:
    schedule_data = {}
    with open(fname) as fin:
        reader = csv.reader(fin)
        next(reader)
        for row in reader:
            srow = ScheduleRow(int(row[0]), int(row[1]), 0, SCHEDULE_PLACE_TYPE_MAP[row[2]], float(row[3]))
            _validate_row(srow)
            if srow.id in schedule_data:
                schedule_data[srow.id].append(srow)
            else:
                schedule_data[srow.id] = [srow]

    for sid, rows in schedule_data.items():
        rows.sort(key=lambda x: x.start)

        if rows[0].start != 0:
            raise ValueError(f"Schedule {sid} does not start time 0")
        for i, row in enumerate(rows[:-1]):
            row.end = rows[i + 1].start
        rows[-1].end = 1440

    return schedule_data


def create_schedules(fname: str | os.PathLike) -> Tuple[Dict[int, int], np.array]:
    schedule_data = _parse_schedules(fname)
    schedules = []
    risks = []
    id_map = {}
    i = 0
    for sid, rows in schedule_data.items():
        id_map[sid] = i
        i += 1
        sched_places, risk = _schedule_rows_to_array(rows)
        schedules.append(sched_places)
        risks.append(risk)

    schedule_array = np.concatenate(schedules, axis=0)
    risks_array = np.concatenate(risks, axis=0)
    return id_map, schedule_array, risks_array


def create_places(fname: Union[str, os.PathLike]) -> Tuple[Dict[int, int], np.array]:
    n_places = 0
    with open(fname) as fin:
        next(fin)
        for _ in fin:
            n_places += 1

    # place_id, n_persons, n_infecteds
    place_data = np.zeros((n_places, 3), dtype=np.uint32)
    places_id_map = {}
    with open(fname) as fin:
        reader = csv.reader(fin)
        next(reader)
        for i, row in enumerate(reader):
            n_id = int(row[0])
            places_id_map[n_id] = i
            place_data[i, 0] = n_id

    return places_id_map, place_data


def _parse_resident_place_entry(entry: str):
    entry = entry.strip()
    vals = entry.split("|")
    return [int(v) for v in vals]


def create_residents(name: Union[str, os.PathLike], place_id_map: Dict[int, int],
                     schedule_id_map: Dict[int, int]) -> np.array:
    n_persons = 0
    with open(name) as fin:
        next(fin)
        for _ in fin:
            n_persons += 1

    resident_data = np.zeros((n_persons, N_P_ELEMENTS), dtype=np.uint32)
    resident_data[:, P_STATE_IDX] = SUSCEPTIBLE
    resident_data[:, P_NEXT_STATE_T_IDX] = np.iinfo(np.uint32).max
    with open(name) as fin:
        reader = csv.reader(fin)
        next(reader)
        for i, row in enumerate(reader):
            pid = int(row[P_DATA_ID_IDX])
            sched_id = schedule_id_map[int(row[P_DATA_SCHEDULE_IDX])]
            cell_id = place_id_map[int(row[P_DATA_CELL_IDX])]
            act_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_ACTS_IDX])]
            caf_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_CAFS_IDX])]
            outdoor_id = place_id_map[int(row[P_DATA_OUT_IDX])]
            # set current place to cell id
            resident_data[i, : -2] = pid, sched_id, cell_id, cell_id, act_ids[0], act_ids[1], caf_ids[0], caf_ids[1], \
                outdoor_id

    return resident_data


# class Prisoner(core.Agent):

#     TYPE = 0

#     PID_IDX = 0
#     CELL_IDX = 1
#     CURRENT_PLANCE = 2
#     SCHEDULE_IDX = 3

#     def __init__(self, idx: int, prisoner_data: np.array, rank):
#         super().__init__(id=idx, type=Prisoner.TYPE, rank=rank)
#         self.idx = idx
#         self.pid = prisoner_data[idx, Prisoner.PID_IDX]
#         self.schedule_id = prisoner_data[idx, Prisoner.SCHEDULE_IDX]
#         self.cell_id = prisoner_data[idx, Prisoner.CELL_IDX]
#         self.prisoner_data = prisoner_data


# def init_prisoner_data(fname: Union[str, os.PathLike], schedule_id_map: Dict[int, int]):
#     n_persons = 0
#     with open(fname) as fin:
#         next(fin)
#         for _ in fin:
#             n_persons += 1

#     prisoner_data = np.zeros((n_persons, 4), dtype=np.int64)
#     with open(fname) as fin:
#         reader = csv.reader(fin)
#         next(reader)
#         for i, row in enumerate(reader):
#             pid, cell, schedule = [int(x) for x in row]
#             prisoner_data[i, :] = pid, cell, cell, schedule_id_map[schedule]

#     return prisoner_data


# def create_prisoners(prisoner_data: np.array, rank: int):
#     for i in range(prisoner_data.shape[0]):
#         yield Prisoner(i, prisoner_data, rank)

import csv
from typing import Union, Dict, List, Tuple
import os
import numpy as np
from dataclasses import dataclass

from .common import TICKS_PER_DAY, TICK_DURATION, MIDNIGHT, SUSCEPTIBLE

P_DATA_ID_IDX = 0
P_DATA_SCHEDULE_IDX = 1
P_DATA_CELL_IDX = 2
P_DATA_CAF_IDX = 3
P_DATA_MACT_IDX = 4
P_DATA_NACT_IDX = 5
P_DATA_EACT_IDX = 6

# P_ACTS_COUNT = 2
# P_CAFS_COUNT = 2

P_ID_IDX = 0
P_SCHEDULE_IDX = 1
P_CURRENT_PLACE_IDX = 2
P_CELL_IDX = 3
P_CAF_IDX = 4
P_MACT_IDX = 5
P_NACT_IDX = 6
P_EACT_IDX = 7
# person's current disease state
P_STATE_IDX = 8
# next transition time
P_NEXT_STATE_T_IDX = 9
# total number columns in residents data
N_P_ELEMENTS = P_NEXT_STATE_T_IDX + 1

PL_PERSON_COUNT_IDX = 1
PL_INFECTED_COUNT_IDX = 2


# Maps activity type string in schedule to
# index into the np array of the person data
SCHEDULE_PLACE_TYPE_MAP = {
    "cell": P_CELL_IDX,
    "noon_act": P_NACT_IDX,
    "morning_act": P_MACT_IDX,
    "evening_act": P_EACT_IDX,
    "cafeteria": P_CAF_IDX
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


class Places:

    def __init__(self, place_id_map: Dict[int, int], place_data: np.array):
        self.place_data = place_data
        self.place_id_map = place_id_map

    def update_counts(self, places: np.array, counts: np.array):
        self.place_data[:, PL_PERSON_COUNT_IDX:] = 0
        self.place_data[places, PL_PERSON_COUNT_IDX] = counts

    def update_infected_counts(self, places: np.array, counts: np.array):
        self.place_data[:, PL_INFECTED_COUNT_IDX:] = 0
        self.place_data[places, PL_INFECTED_COUNT_IDX] = counts

    def get_counts(self, place_idxs: np.array):
        return self.place_data[np.ix_(place_idxs, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX))]

    def get_all_counts(self):
        return self.place_data[:, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX)]


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

    return Places(places_id_map, place_data)


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
            caf_id = place_id_map[int(row[P_DATA_CAF_IDX])]
            mact_id = place_id_map[int(row[P_DATA_MACT_IDX])]
            nact_id = place_id_map[int(row[P_DATA_NACT_IDX])]
            eact_id = place_id_map[int(row[P_DATA_EACT_IDX])]
            resident_data[i, : -2] = pid, sched_id, cell_id, cell_id, caf_id, mact_id, nact_id, eact_id

            # act_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_ACTS_IDX])]
            # caf_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_CAFS_IDX])]
            # outdoor_id = place_id_map[int(row[P_DATA_OUT_IDX])]
            # set current place to cell id

    return resident_data

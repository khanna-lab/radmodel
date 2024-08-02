import csv
import os
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass

TICK_DURATION = 15
TICKS_PER_DAY = int(24 * (60 / TICK_DURATION))
# midnight in mins
MIDNIGHT = 24 * 60

SCHEDULE_ID_IDX = 0


@dataclass
class ScheduleRow:
    id: int
    start: int
    end: int
    place: int
    risk: float


def _rows_to_array(rows: List[ScheduleRow]):
    np_data = np.zeros((TICKS_PER_DAY, 2))
    rows_index = 0
    row = rows[rows_index]
    for idx in range(0, TICKS_PER_DAY):
        t = idx * TICK_DURATION
        # sorted so can ignore start
        while (t >= row.end):
            rows_index += 1
            row = rows[rows_index]

        np_data[idx][:] = row.place, row.risk

    return np_data


def _validate_row(row: ScheduleRow):
    if row.start < 0 or row.start > MIDNIGHT:
        raise ValueError(f"Schedule {row.id} is invalid: {row}")


def _parse_schedules(fname: str | os.PathLike) -> Dict[int, List[ScheduleRow]]:
    schedule_data = {}
    with open(fname) as fin:
        reader = csv.reader(fin)
        next(reader)
        for row in reader:
            srow = ScheduleRow(int(row[0]), int(row[1]), 0, int(row[2]),
                               float(row[3]))
            _validate_row(srow)
            if srow.id in schedule_data:
                schedule_data[srow.id].append(srow)
            else:
                schedule_data[srow.id] = [srow]

    for sid, rows in schedule_data.items():
        rows.sort(key=lambda x: x.start)

        if rows[0].start != 0:
            raise ValueError(f"Schedule {sid} does not start time 0")

        for i, row in enumerate(rows):
            end = MIDNIGHT + 1 if i + 1 == len(rows) else rows[i + 1].start
            row.end = end

    return schedule_data


def create_schedules(fname: str | os.PathLike) -> Tuple[Dict[int, int], np.array]:
    schedule_data = _parse_schedules(fname)
    schedules = []
    id_map = {}
    i = 0
    for sid, rows in schedule_data.items():
        id_map[sid] = i
        i += 1
        schedules.append(_rows_to_array(rows))

    schedule_array = np.concatenate(schedules, axis=0)
    return id_map, schedule_array

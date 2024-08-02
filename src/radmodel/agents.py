import csv
from typing import Union, Dict
import os
import numpy as np

from repast4py import core


class Prisoner(core.Agent):

    TYPE = 0

    PID_IDX = 0
    CELL_IDX = 1
    CURRENT_PLANCE = 2
    SCHEDULE_IDX = 3

    def __init__(self, idx: int, prisoner_data: np.array, rank):
        super().__init__(id=idx, type=Prisoner.TYPE, rank=rank)
        self.idx = idx
        self.pid = prisoner_data[idx, Prisoner.PID_IDX]
        self.schedule_id = prisoner_data[idx, Prisoner.SCHEDULE_IDX]
        self.cell_id = prisoner_data[idx, Prisoner.CELL_IDX]
        self.prisoner_data = prisoner_data


def init_prisoner_data(fname: Union[str, os.PathLike], schedule_id_map: Dict[int, int]):
    n_persons = 0
    with open(fname) as fin:
        next(fin)
        for _ in fin:
            n_persons += 1

    prisoner_data = np.zeros((n_persons, 4), dtype=np.int64)
    with open(fname) as fin:
        reader = csv.reader(fin)
        next(reader)
        for i, row in enumerate(reader):
            pid, cell, schedule = [int(x) for x in row]
            prisoner_data[i, :] = pid, cell, cell, schedule_id_map[schedule]

    return prisoner_data


def create_prisoners(prisoner_data: np.array, rank: int):
    for i in range(prisoner_data.shape[0]):
        yield Prisoner(i, prisoner_data, rank)

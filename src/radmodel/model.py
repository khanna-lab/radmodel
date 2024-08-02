from typing import Dict, Any
import numpy as np

from . import schedule
from . import agents


class Updater:

    def __init__(self, schedule_data: np.array, person_data: np.array):
        n_schedules = int(schedule_data.shape[0] / schedule.TICKS_PER_DAY)
        self.schedule_data = schedule_data
        self.offsets = np.arange(0, n_schedules, dtype=np.int64) * schedule.TICKS_PER_DAY
        self.idx = np.zeros((n_schedules), dtype=np.int64)
        self.next_place = np.zeros((n_schedules, 3))
        self.person_data = person_data

    def select_next_place(self, tick: int):
        # add tick index to offset to get the schedule inidices
        np.add(self.offsets, tick % schedule.TICKS_PER_DAY, out=self.idx)
        # set the place id and risk to the schedule entries
        self.next_place[:, 0:2] = self.schedule_data[self.idx]

        # Algorithm:
        # 1. a = Get the number of schedules a "next place" appears in.
        # 2. b = Get the number of persons with each schedule
        # 3. a * b is the number of persons at that place
        # Key here is that next_place is ordered by schedule (row 0 corresponds to schedule 0, and so on)
        # -----------
        # Get a count of each place in next_place, together with the inverse array
        _, inverse, counts = np.unique(self.next_place[:, 0], return_inverse=True, return_counts=True)
        # inverse element is index into counts, counts[inverse] then gives count for all schedules (i.e.,
        # all rows in self.next_place)
        self.next_place[:, 2] = counts[inverse]

        # Get a count of the schedule indices in the person data
        schedule_idxs, p_counts = np.unique(self.person_data[:, agents.Prisoner.SCHEDULE_IDX], return_counts=True)
        self.next_place[schedule_idxs, 2] *= p_counts


def create_updater(params: Dict[str, Any]):
    schedule_fname = params["schedule.file"]
    schedule_id_map, schedule_data = schedule.create_schedules(schedule_fname)

    prisoners_fname = params["prisoner.file"]
    person_data = agents.init_prisoner_data(prisoners_fname, schedule_id_map)
    return Updater(schedule_data, person_data)

# class Model():

#     def __init__(self, params: Dict[str, Any], comm):
#         self.ctx: context.SharedContext = context.SharedContext(comm)
#         self.rank = comm.Get_rank()

#         schedule_fname = params["schedule.file"]
#         schedule_id_map, schedules = schedule.create_schedules(schedule_fname)
#         self.schedules: schedule.Schedules = schedules

#         prisoners_fname = params["prisoners.file"]
#         for prisoner in agents.create_prisoners(prisoners_fname, schedule_id_map, self.rank):
#             self.ctx.add(prisoner)

#         self.prisoners: np.array = next(iter(self.ctx.agents(agent_type=agents.Prisoner.TYPE))).prisoner_data

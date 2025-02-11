from dataclasses import dataclass
import numpy as np
import os
from typing import Dict
from mpi4py import MPI

from repast4py import logging, schedule

from .common import TICKS_PER_DAY, SUSCEPTIBLE, EXPOSED, PRESYMPTOMATIC, INFECTED_SYMP, INFECTED_ASYMP, \
    RECOVERED, HOSPITALIZED, STATE_MAP, DEAD
from .population import P_SCHEDULE_IDX, P_CURRENT_PLACE_IDX, PL_PERSON_COUNT_IDX, P_STATE_IDX, P_NEXT_STATE_T_IDX, \
    PL_INFECTED_COUNT_IDX


@dataclass
class Counts:
    susceptible: int = 0
    exposed: int = 0
    presymp: int = 0
    infected_symp: int = 0
    infected_asymp: int = 0
    recovered: int = 0
    hospitalized: int = 0
    dead: int = 0

    newly_susceptible: int = 0
    newly_exposed: int = 0
    newly_presymp: int = 0
    newly_infected_symp: int = 0
    newly_infected_asymp: int = 0
    newly_recovered: int = 0
    newly_hospitalized: int = 0
    newly_dead: int = 0

    def reset(self):
        self.susceptible = 0
        self.exposed = 0
        self.presymp = 0
        self.infected_symp = 0
        self.infected_asymp = 0
        self.recovered = 0
        self.hospitalized = 0
        self.dead = 0

        self.newly_susceptible = 0
        self.newly_exposed = 0
        self.newly_presymp = 0
        self.newly_infected_symp = 0
        self.newly_infected_asymp = 0
        self.newly_recovered = 0
        self.newly_hospitalized = 0
        self.newly_dead = 0


class Model:

    def __init__(self, comm: MPI.Intracomm, schedule_data: np.array, person_data: np.array,
                 place_data: np.array, stoe: float, trans_matrix: np.array, duration_matrix: np.array, seed: int,
                 params: Dict[str, any]):
        self.rng: np.random.Generator = np.random.default_rng(seed)
        n_schedules = int(schedule_data.shape[0] / TICKS_PER_DAY)
        self.schedule_data = schedule_data
        self.offsets = np.arange(0, n_schedules, dtype=np.int64) * TICKS_PER_DAY
        self.idx = np.zeros((n_schedules), dtype=np.int64)
        # array of indices into resident's place columns, 1 for each schedule
        self.next_place_idxs = np.zeros((n_schedules), dtype=np.uint32)
        # self.risks = np.zeros((n_schedules))
        self.person_data = person_data
        self.place_data = place_data
        self.stoe: np.float32 = np.float32(stoe)
        self.row_idxs = np.arange(len(self.person_data))
        self.trans_matrix: np.array = trans_matrix.cumsum(axis=1)
        self.duration_matrix: np.array = duration_matrix
        self.params = params
        self.comm = comm

        self._init_logging(comm, params["log_file"])
        self._init_schedule(comm)
        self._init_exposed(params["init_exposed"])
        self._log(0)

    def _init_exposed(self, n_exposed: int):
        idxs = self.rng.choice(self.person_data.shape[0], n_exposed, replace=False)
        np.put(self.person_data[:, P_STATE_IDX], idxs, EXPOSED)

        k, scale = self.duration_matrix[EXPOSED]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX], idxs,
               self.rng.gamma(k, scale, n_exposed) * TICKS_PER_DAY)
        print(self.person_data[:, P_NEXT_STATE_T_IDX])

    def _init_logging(self, comm: MPI.Intracomm, log_file: str | os.PathLike):
        self.counts = Counts()
        loggers = logging.create_loggers(self.counts, op=MPI.SUM, rank=comm.Get_rank())
        self.data_set = logging.ReducingDataSet(loggers, comm, log_file)

    def _init_schedule(self, comm):
        self.runner = schedule.init_schedule_runner(comm)
        self.runner.schedule_repeating_event(1, 1, self.step)
        self.runner.schedule_stop(self.params["stop.at"])
        self.runner.schedule_end_event(self.at_end)
        # write at the end of every day (4 * 24)
        self.runner.schedule_repeating_event(96.1, 96, self.data_set.write)

    def at_end(self):
        self.data_set.close()

    def select_next_place(self, tick: int):
        # add tick index to offset to get the schedule inidices
        np.add(self.offsets, tick % TICKS_PER_DAY, out=self.idx)
        # Sets the next place type (person place column idx) for each schedule
        self.next_place_idxs[:] = self.schedule_data[self.idx]

        # Set the current place for each person by
        # 1. Getting the column idxs for the next places via next_place_idxs and each persons schedule_idx
        # 2. Set the current place id column to the value in the selected next_place_column idxs
        residents_next_place_idxs = self.next_place_idxs[self.person_data[:, P_SCHEDULE_IDX]]
        self.person_data[:, P_CURRENT_PLACE_IDX] = self.person_data[self.row_idxs, residents_next_place_idxs]

        # reset person counts in each place to 0
        self.place_data[:, PL_PERSON_COUNT_IDX:] = 0
        # sets total persons in each place: unique place ids (which are also row indexs in place data),
        #                                   and how many times they occur
        places, counts = np.unique(self.person_data[:, P_CURRENT_PLACE_IDX], return_counts=True)
        # Using the places place row idxs set number of persons in those places
        self.place_data[places, PL_PERSON_COUNT_IDX] = counts
        states = self.person_data[:, P_STATE_IDX]

        # Same counts but only for infected persons
        places, counts = np.unique(self.person_data[(states == PRESYMPTOMATIC)
                                   | (states == INFECTED_ASYMP)
                                   | (states == INFECTED_SYMP)][:, P_CURRENT_PLACE_IDX],
                                   return_counts=True)
        self.place_data[places, PL_INFECTED_COUNT_IDX] = counts

    def update_disease_state(self, tick: int):
        # row indices of susceptibles - calc if exposed
        sus_idxs = np.nonzero(self.person_data[:, P_STATE_IDX] == SUSCEPTIBLE)[0]
        n_sus = sus_idxs.shape[0]
        # get the place row indices for all the susceptibles
        sus_place_idxs = self.person_data[sus_idxs, P_CURRENT_PLACE_IDX]
        # each row corresponds to person, cols are total person count, infected count
        # .ix_ applies the column indices to each row index
        counts = self.place_data[np.ix_(sus_place_idxs, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX))]
        # array of n_sus stoe probs - if no one in place, then set prob to 0
        # TODO: risk and shielding scaling
        stoe_p = np.full((n_sus, ), self.stoe, dtype=np.float32) * (counts[:, 1] > 0)
        # if tick >= 317:
        #     print(self.place_data[:, PL_INFECTED_COUNT_IDX])
        #     print(counts)
        #     print(self.stoe)
        #     print(stoe_p)
        # sus_idxs[self ...] removes the indexes that don't pass the condition (random draw <= stoe_p)
        stoe_idxs = sus_idxs[self.rng.random(n_sus) <= stoe_p]
        # set state to exposed for those that passed
        np.put(self.person_data[:, P_STATE_IDX], stoe_idxs, EXPOSED)
        self.counts.newly_exposed += stoe_idxs.shape[0]

        # set the how long to stay exposed
        k, scale = self.duration_matrix[EXPOSED]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX], stoe_idxs,
               tick + self.rng.gamma(k, scale, stoe_idxs.shape[0]) * TICKS_PER_DAY)

        # get non_susceptibles whose next transition time == tick
        candidates_idxs = np.nonzero((self.person_data[:, P_STATE_IDX] != SUSCEPTIBLE)
                                     & (self.person_data[:, P_NEXT_STATE_T_IDX] == np.int(tick)))[0]
        n_candidates = candidates_idxs.shape[0]

        # Compute n_candidates updated states from the transition matrix
        updated_states = (self.trans_matrix[self.person_data[candidates_idxs, P_STATE_IDX]]
                          > self.rng.random((n_candidates, 1))).argmax(1)
        # Update the states
        np.put(self.person_data[:, P_STATE_IDX], candidates_idxs, updated_states)

        # Set next transition tick for candidates
        duration_candidates = candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == PRESYMPTOMATIC]
        k, scale = self.duration_matrix[PRESYMPTOMATIC]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX],
               duration_candidates, tick + self.rng.gamma(k, scale, duration_candidates.shape[0]) * TICKS_PER_DAY)
        self.counts.newly_presymp += duration_candidates.shape[0]

        duration_candidates = candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == INFECTED_SYMP]
        k, scale = self.duration_matrix[INFECTED_SYMP]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX],
               duration_candidates, tick + self.rng.gamma(k, scale, duration_candidates.shape[0]) * TICKS_PER_DAY)
        self.counts.newly_infected_symp += duration_candidates.shape[0]

        duration_candidates = candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == INFECTED_ASYMP]
        k, scale = self.duration_matrix[INFECTED_ASYMP]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX],
               duration_candidates, tick + self.rng.gamma(k, scale, duration_candidates.shape[0]) * TICKS_PER_DAY)
        self.counts.newly_infected_asymp += duration_candidates.shape[0]

        duration_candidates = candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == HOSPITALIZED]
        k, scale = self.duration_matrix[HOSPITALIZED]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX],
               duration_candidates, tick + self.rng.gamma(k, scale, duration_candidates.shape[0]) * TICKS_PER_DAY)
        self.counts.newly_hospitalized += duration_candidates.shape[0]

        duration_candidates = candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == RECOVERED]
        k, scale = self.duration_matrix[RECOVERED]
        np.put(self.person_data[:, P_NEXT_STATE_T_IDX],
               duration_candidates, tick + self.rng.gamma(k, scale, duration_candidates.shape[0]) * TICKS_PER_DAY)
        self.counts.newly_recovered += duration_candidates.shape[0]

        self.counts.newly_dead += candidates_idxs[self.person_data[candidates_idxs, P_STATE_IDX] == DEAD].shape[0]

    def run(self):
        self.runner.execute()

    def _log(self, tick):
        # sum of persons in categories with np.count_nonzero
        # np.count_nonzero(self.person_data[:, P_STATE_IDX] == SUSCEPTIBLE)
        self.counts.susceptible += np.count_nonzero(self.person_data[:, P_STATE_IDX] == SUSCEPTIBLE)
        self.counts.exposed += np.count_nonzero(self.person_data[:, P_STATE_IDX] == EXPOSED)
        self.counts.presymp += np.count_nonzero(self.person_data[:, P_STATE_IDX] == PRESYMPTOMATIC)
        self.counts.infected_symp += np.count_nonzero(self.person_data[:, P_STATE_IDX] == INFECTED_SYMP)
        self.counts.infected_asymp += np.count_nonzero(self.person_data[:, P_STATE_IDX] == INFECTED_ASYMP)
        self.counts.recovered += np.count_nonzero(self.person_data[:, P_STATE_IDX] == RECOVERED)
        self.counts.hospitalized += np.count_nonzero(self.person_data[:, P_STATE_IDX] == HOSPITALIZED)
        self.counts.dead += np.count_nonzero(self.person_data[:, P_STATE_IDX] == DEAD)

        self.data_set.log(tick)

    def step(self):
        self.counts.reset()

        tick = self.runner.tick()
        self.select_next_place(tick)
        self.update_disease_state(tick)

        self._log(tick)


def create_duration_matrix(params: Dict[str, float]):
    # 8 states, but we won"t use all of them (e.g. dead duration)
    durations = np.zeros((len(STATE_MAP), 2), dtype=np.float32)
    durations[EXPOSED] = params["exposed_duration_k"], \
        params["exposed_duration_mean"] / params["exposed_duration_k"]
    durations[INFECTED_ASYMP] = params["asymptomatic_duration_k"], \
        params["asymptomatic_duration_mean"] / params["asymptomatic_duration_k"]
    durations[INFECTED_SYMP] = params["symptomatic_duration_k"], \
        params["symptomatic_duration_mean"] / params["symptomatic_duration_k"]
    durations[PRESYMPTOMATIC] = params["presymptomatic_duration_k"], \
        params["presymptomatic_duration_mean"] / params["presymptomatic_duration_k"]
    durations[HOSPITALIZED] = params["hospital_duration_k"], \
        params["hospital_duration_mean"] / params["hospital_duration_k"]
    durations[RECOVERED] = params["recovered_duration_k"], \
        params["recovered_duration_mean"] / params["recovered_duration_k"]
    return durations


def create_trans_matrix(transition_matrix: Dict[str, Dict[str, float]]):
    n_states = len(STATE_MAP)
    trans_matrix = np.zeros((n_states, n_states), dtype=np.float32)
    for i_key, v in transition_matrix.items():
        i = STATE_MAP[i_key]
        for j_key, prob in v.items():
            j = STATE_MAP[j_key]
            trans_matrix[i, j] = prob

    return trans_matrix

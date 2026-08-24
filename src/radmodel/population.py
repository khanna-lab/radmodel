import csv
import os

import numpy as np
import polars as pl
import pydantic_numpy.typing as pnd
from pydantic import BaseModel, Field

from .common import MIDNIGHT, SUSCEPTIBLE, TICK_DURATION, TICKS_PER_DAY

# P_DATA_ID_IDX = 0
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

def create_schedules(
    fname: str,
) -> pl.DataFrame:
    """Create tick-indexed schedule places and risks for all schedules in the file.

    Parameters
    ==========
    fname: str | os.PathLike
        Path to the schedule CSV file.

    Returns
    =======
    Schedule
        Full schedule for all schedule IDs
    """
    schedules = pl.read_csv(fname)
    schedules = schedules.with_columns(t=pl.int_ranges("start", "end"))
    return schedules.explode("t", empty_as_null=False)


class Places:
    def __init__(self, place_id_map: dict[int, int], place_data: np.ndarray):
        """Class to hold place data and provide methods to update and retrieve counts.

        Parameters
        ==========
        place_id_map: Dict[int, int]
            Mapping from place ID to index in the place array.
        place_data: np.ndarray
            2d-array of shape (n_places, 3) containing place data,
            where each row corresponds to a place and the columns are:
                0: place ID
                1: number of persons
                2: number of infecteds
        """
        self.place_data = place_data
        self.place_id_map = place_id_map

    def update_counts(self, places: np.ndarray, counts: np.ndarray):
        """Update the counts of persons in the specified places.

        Parameters
        ==========
        places: np.ndarray
            Array of place indices to update.
        counts: np.ndarray
            Array of counts corresponding to the places.
        """
        self.place_data[:, PL_PERSON_COUNT_IDX:] = 0
        self.place_data[places, PL_PERSON_COUNT_IDX] = counts

    def update_infected_counts(self, places: np.ndarray, counts: np.ndarray):
        """Update the counts of infected persons in the specified places.

        Parameters
        ==========
        places: np.ndarray
            Array of place indices to update.
        counts: np.ndarray
            Array of counts corresponding to the places.
        """
        self.place_data[:, PL_INFECTED_COUNT_IDX:] = 0
        self.place_data[places, PL_INFECTED_COUNT_IDX] = counts

    def get_counts(self, place_idxs: np.ndarray):
        """Get the counts of persons and infected persons for the specified places.

        Parameters
        ==========
        place_idxs: np.ndarray
            Array of place indices to retrieve counts for.

        Returns
        =======
        np.ndarray
            Array of shape (len(place_idxs), 2) containing counts of persons and infected persons.
        """
        return self.place_data[
            np.ix_(place_idxs, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX))  # type: ignore
        ]

    def get_all_counts(self):
        """Get the counts of persons and infected persons for all places.

        Returns
        =======
        np.ndarray
            Array of shape (n_places, 2) containing counts of persons and infected persons.
        """
        return self.place_data[:, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX)]


def create_places(fname: str | os.PathLike) -> Places:
    """Create places data array from CSV file.

    Parameters
    ==========
    fname: str | os.PathLike
        Path to the places CSV file.

    Returns
    =======
    Places
        Places object containing two pieces of information:
        1. place_id_map: dict[int, int] - Mapping from place ID to index in the place array.
        2. place_data: np.ndarray - 2d-array of shape (n_places, 3) containing place data,
           where each row corresponds to a place and the columns are:
            0: place ID
            1: number of persons
            2: number of infecteds
    """
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


def create_residents(
    fname: str,
    place_id_map: dict[int, int],
    schedule_id_map: dict[int, int],
) -> np.ndarray:
    """Create residents data array from CSV file.

    This mainly involves mapping the place and schedule IDs to their corresponding indices
    in the place and schedule arrays.Also adds two additional columns for the resident's
    current disease state and the next transition time.

    Parameters
    ==========
    fname: str | os.PathLike
        Path to the residents CSV file.
    place_id_map: dict[int, int]
        Mapping from place ID to index in the place array.
    schedule_id_map: dict[int, int]
        Mapping from schedule ID to index in the schedule array.

    Returns
    =======
    np.ndarray
        2d-array of shape (n_persons, N_P_ELEMENTS) containing resident data.
    """
    pl.read_csv(fname)
    # n_persons = 0
    # with open(fname) as fin:
    #     next(fin)
    #     for _ in fin:
    #         n_persons += 1

    # resident_data = np.zeros((n_persons, N_P_ELEMENTS), dtype=np.uint32)
    # # Everyone is susceptible at the start of the simulation, and no next transition time
    # resident_data[:, P_STATE_IDX] = SUSCEPTIBLE
    # # Set next transition time to max value, which indicates no transition is scheduled
    # resident_data[:, P_NEXT_STATE_T_IDX] = np.iinfo(np.uint32).max

    # with open(fname) as fin:
    #     reader = csv.reader(fin)
    #     next(reader)
    #     for i, row in enumerate(reader):
    #         pid = int(row[P_DATA_ID_IDX])
    #         sched_id = schedule_id_map[int(row[P_DATA_SCHEDULE_IDX])]
    #         cell_id = place_id_map[int(row[P_DATA_CELL_IDX])]
    #         caf_id = place_id_map[int(row[P_DATA_CAF_IDX])]
    #         mact_id = place_id_map[int(row[P_DATA_MACT_IDX])]
    #         nact_id = place_id_map[int(row[P_DATA_NACT_IDX])]
    #         eact_id = place_id_map[int(row[P_DATA_EACT_IDX])]
    #         resident_data[i, :-2] = (
    #             pid,
    #             sched_id,
    #             cell_id,
    #             cell_id,
    #             caf_id,
    #             mact_id,
    #             nact_id,
    #             eact_id,
            # )

            # act_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_ACTS_IDX])]
            # caf_ids = [place_id_map[i] for i in _parse_resident_place_entry(row[P_DATA_CAFS_IDX])]
            # outdoor_id = place_id_map[int(row[P_DATA_OUT_IDX])]
            # set current place to cell id

    return resident_data

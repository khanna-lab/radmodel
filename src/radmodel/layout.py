"""Reader for the structural-layout CSVs (see references/specs/structural-layout-v1.md).

Exposes facility structure (modules, cells, shared places, cell assignments)
as queryable dataclasses. The simulation core does not yet consume this; it
is descriptive metadata for future schedule/movement work.
"""

import csv
import os
from dataclasses import dataclass, field
import string
from numpy import uint32, zeros, ndarray, ix_
from typing import TypeVar

T = TypeVar("T")

PL_PERSON_COUNT_IDX = 1
PL_INFECTED_COUNT_IDX = 2


@dataclass
class Agent:
    person_id: int
    module_id: int
    cell_place_id: int


@dataclass
class Cell:
    place_id: int
    module_id: int | None
    tier: str | None
    cell_number: int
    housing_category: str  # "GP", "RH", "MI"
    bunk_capacity: int
    name: str
    occupants: list[Agent] = field(default_factory=list)


@dataclass
class SharedPlace:
    place_id: int
    name: str
    place_type: str
    module_id: int | None
    occupants: list[Agent] = field(default_factory=list)


@dataclass
class BaseModule:
    cells: list[Cell] = field(default_factory=list)

    def add_cell(self, **r):
        self.cells.append(
            Cell(
                place_id=int(r["place_id"]),
                module_id=_opt_int(r["parent_id"]),
                tier=r["tier"],
                cell_number=int(r["place_id"]),
                housing_category=r["subtype"],
                bunk_capacity=int(r["capacity"]),
                name=r["name"],
            )
        )


@dataclass
class Module(BaseModule):
    module_id: int = 0
    letter: str = ""
    shared_places: list[SharedPlace] = field(default_factory=list)


@dataclass
class SharedModule(BaseModule):
    module_id: str = ""
    pass


@dataclass
class Layout:
    """Class to hold the hierarchical layout of the prison.

    Generates variables needed for the Places class:
      a structural `Layout` containing `Module`s and their associated `Cell`s
      a places_id_map: dict[int, int]
      and place_data: ndarray
    """

    places_id_map: dict[int, int] = field(default_factory=dict)
    n_places = 0
    place_data: ndarray = field(default_factory=lambda: zeros((), dtype=uint32))
    modules: dict[int, Module] = field(default_factory=dict)
    shared_places: dict[str, SharedPlace] = field(default_factory=dict)
    shared_modules: dict[str, SharedModule] = field(default_factory=dict)

    def add_module(self, **r):
        letter = string.ascii_uppercase[int(r["place_id"]) - 2012]
        self.modules.update(
            {int(r["place_id"]): Module(module_id=int(r["place_id"]), letter=letter)}
        )

    def add_shared_module(self, **r):
        self.shared_modules.update(
            {r["subtype"]: SharedModule(module_id=r["place_id"])}
        )

    def add_shared_place(self, **r):
        self.shared_places.update(
            {
                r["name"]: SharedPlace(
                    place_id=int(r["place_id"]),
                    name=r["name"],
                    place_type=r["subtype"],
                    module_id=_opt_int(r["parent_id"]),
                )
            }
        )

    def load_places(self, path: str | os.PathLike):
        """Loads the csv generated from the generate.generate_places function.

        Parameters
        ==========
        path: str | os.PathLike
            path to folder containing ng_places.csv
        """
        with open(os.path.join(path, "ng_places.csv")) as f:
            self.n_places = len(f.readlines()) - 1
        with open(os.path.join(path, "ng_places.csv")) as f:
            self.place_data = zeros((self.n_places, 3), dtype=uint32)
            i = 0
            reader = csv.DictReader(f)
            for r in reader:
                if r["type"] == "facility":
                    continue
                n_id = int(r["place_id"])
                self.places_id_map[n_id] = i
                self.place_data[i, 0] = n_id
                # TODO this should probably have some sort of mapping for the functions instead of an if
                if r["type"] == "module":
                    self.add_module(**r)
                elif r["type"] == "cell":
                    if r["subtype"] == "gp":
                        self.modules[int(r["parent_id"])].add_cell(**r)
                    elif r["subtype"] == "mi":
                        self.shared_modules["medical"].add_cell(**r)
                    elif r["subtype"] == "rh":
                        self.shared_modules["segregation"].add_cell(**r)

                else:
                    if r["subtype"] in ["segregation", "medical"]:
                        self.add_shared_module(**r)
                    else:
                        self.add_shared_place(**r)
                i += 1

    @classmethod
    def load_from_csv(cls, data_dir: str | os.PathLike) -> "Layout":
        """Load the structural CSV from a directory."""
        layout = Layout()
        layout.load_places(data_dir)
        return layout

    def update_counts(self, places: ndarray, counts: ndarray):
        """Update the counts of agents in the specified places.

        Parameters
        ==========
        places: np.ndarray
            Array of place indices to update.
        counts: np.ndarray
            Array of counts corresponding to the places.
        """
        self.place_data[:, PL_PERSON_COUNT_IDX:] = 0
        self.place_data[places, PL_PERSON_COUNT_IDX] = counts

    def update_infected_counts(self, places: ndarray, counts: ndarray):
        """Update the counts of infected agents in the specified places.

        Parameters
        ==========
        places: np.ndarray
            Array of place indices to update
        counts: np.ndarray
            Array of counts corresponding to the places
        """
        self.place_data[:, PL_INFECTED_COUNT_IDX:] = 0
        self.place_data[places, PL_INFECTED_COUNT_IDX] = counts

    def get_counts(self, places_idxs: ndarray):
        """Get the counts of agents and infected agents for the specified places.
        Parameters
        ==========
        place_idxs: np.ndarray
            Array of place indices to retrieve counts for

        Returns
        =======
        np.ndarray
            Array of shape (len(place_idxs), 2) containing counts of persons and infected persons.
        """

        return self.place_data[
            #TODO review why this is causing a lint error, works if you make the latter two an array
            ix_(places_idxs, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX))
        ]

    def get_all_counts(self):
        """Get the counts of persons and infected persons for all places.
        
        Returns
        =======
        np.ndarray
            Array of shape (n_places, 2) containing counts of persons and infected persons.
        """
        return self.place_data[:, (PL_PERSON_COUNT_IDX, PL_INFECTED_COUNT_IDX)]

def _opt_int(s: str) -> int | None:
    return int(s) if s != "" else None


def _opt_str(s: str) -> str | None:
    return s if s != "" else None

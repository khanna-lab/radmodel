"""Reader for the structural-layout CSVs (see references/specs/structural-layout-v1.md).

Exposes facility structure (modules, cells, shared places, cell assignments)
as queryable dataclasses. The simulation core does not yet consume this; it
is descriptive metadata for future schedule/movement work.
"""

import os
import string
from dataclasses import dataclass, field
from typing import TypeVar

import polars as pl

T = TypeVar("T")


@dataclass
class Cell:
    place_id: int
    module_id: int | None
    tier: str | None
    cell_number: int
    housing_category: str  # "GP", "RH", "MI"
    bunk_capacity: int
    name: str
    occupants: pl.DataFrame = field(default_factory=pl.DataFrame)


@dataclass
class SharedPlace:
    place_id: int
    name: str
    place_type: str
    module_id: int | None
    occupants: pl.DataFrame = field(default_factory=pl.DataFrame)


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
    showers: list[SharedPlace] = field(default_factory=list)
    dayrooms: list[SharedPlace] = field(default_factory=list)

    def add_shared_place(self, **r):
        if r["subtype"] == "shower":
            self.showers.append(
                SharedPlace(
                    place_id=int(r["place_id"]),
                    name=r["name"],
                    place_type=r["subtype"],
                    module_id=_opt_int(r["parent_id"]),
                )
            )
        elif r["subtype"] == "dayroom":
            self.dayrooms.append(
                SharedPlace(
                    place_id=int(r["place_id"]),
                    name=r["name"],
                    place_type=r["subtype"],
                    module_id=_opt_int(r["parent_id"]),
                )
            )


@dataclass
class SharedModule(BaseModule):
    module_id: str = ""


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
    place_data: pl.DataFrame = field(default_factory=pl.DataFrame)
    # place_data: ndarray = field(default_factory=lambda: zeros((), dtype=uint32))
    modules: dict[int, Module] = field(default_factory=dict)
    shared_places: dict[str, SharedPlace] = field(default_factory=dict)
    cafeterias: dict[str, SharedPlace] = field(default_factory=dict)
    shared_modules: dict[str, SharedModule] = field(default_factory=dict)
    gp_count = 0

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

    def add_cafeterias(self, **r):
        self.cafeterias.update(
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
            path to folder containing places.csv
        """
        self.place_data = pl.read_csv(os.path.join(path, "places.csv"))
        # TODO I assume there's a way to do this without looping, but I'm not sure how!
        for row in self.place_data.filter(pl.col("type") == "module").to_dicts():
            self.add_module(**row)

        for housing_type in ["restricted", "medical"]:
            r = {"subtype": housing_type, "place_id": -1}
            self.add_shared_module(**r)

        for row in self.place_data.filter(
            ~pl.col("type").is_in(["cell", "module", "facility"]),
        ).to_dicts():
            if row["subtype"] in ["rh", "mi"]:
                self.add_shared_module(**row)
            elif row["subtype"] == "dining_room":
                self.add_cafeterias(**row)
            elif row["subtype"] in ["shower", "dayroom"]:
                self.modules[int(row["parent_id"])].add_shared_place(**row)
            else:
                self.add_shared_place(**row)

        for row in self.place_data.filter(pl.col("type") == "cell").to_dicts():
            match row["subtype"]:
                case "gp":
                    self.modules[int(row["parent_id"])].add_cell(**row)
                    self.gp_count += 1
                case "mi":
                    self.shared_modules["medical"].add_cell(**row)
                case "rh":
                    self.shared_modules["restricted"].add_cell(**row)
        self.place_data = self.place_data.with_columns(person_count=0, infected_count=0)

    @classmethod
    def load_from_csv(cls, data_dir: str | os.PathLike) -> "Layout":
        """Load the structural CSV from a directory."""
        layout = Layout()
        layout.load_places(data_dir)
        return layout


def _opt_int(s: str) -> int | None:
    return int(s) if s != "" else None

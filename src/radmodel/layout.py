"""Reader for the structural-layout CSVs (see references/specs/structural-layout-v1.md).

Exposes facility structure (modules, cells, shared places, cell assignments)
as queryable dataclasses. The simulation core does not yet consume this; it
is descriptive metadata for future schedule/movement work.
"""

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Module:
    module_id: int
    letter: str
    cells = []


@dataclass
class Cell:
    place_id: int
    module_id: Optional[int]
    tier: Optional[str]
    cell_number: int
    housing_category: str  # "GP", "RH", "MI"
    bunk_capacity: int
    name: str


@dataclass
class SharedPlace:
    place_id: int
    name: str
    place_type: str
    parent_module_id: Optional[int]
    capacity: Optional[int]


@dataclass
class CellAssignment:
    person_id: int
    cell_place_id: int
    bunk_position: str  # "bottom", "top", "third"


@dataclass
class Layout:
    modules: List[Module] = field(default_factory=list)
    cells: List[Cell] = field(default_factory=list)
    shared_places: List[SharedPlace] = field(default_factory=list)
    cell_assignments: List[CellAssignment] = field(default_factory=list)

    def cells_by_module(self, module_id: int) -> List[Cell]:
        return [c for c in self.cells if c.module_id == module_id]

    def cells_by_category(self, housing_category: str) -> List[Cell]:
        return [c for c in self.cells if c.housing_category == housing_category]

    def shared_places_by_type(self, place_type: str) -> List[SharedPlace]:
        return [p for p in self.shared_places if p.place_type == place_type]


def _opt_int(s: str) -> Optional[int]:
    return int(s) if s != "" else None


def _opt_str(s: str) -> Optional[str]:
    return s if s != "" else None


def load_places(path: str | os.PathLike) -> Dict:
    loaded_places = {"cells": [], "modules": []}
    with open(path) as f:
        for place in csv.DictReader(f):
            match place["type"]:
                case "cell":
                    loaded_places["cells"].append(
                        Cell(
                            place_id=int(place["place_id"]),
                            module_id=_opt_int(place["module_id"]),
                            tier=_opt_str(place["tier"]),
                            cell_number=int(place["cell_number"]),
                            housing_category=place["housing_category"],
                            bunk_capacity=int(place["bunk_capacity"]),
                            name=place["name"],
                        )
                    )
                case "module":
                    loaded_places["modules"].append(
                        Module(
                            module_id=int(place["module_id"]), letter=place["letter"]
                        )
                    )
                case "shared_place":
                    loaded_places["shared_places"].append(
                        SharedPlace(
                            place_id=int(place["place_id"]),
                            name=place["name"],
                            place_type=place["place_type"],
                            parent_module_id=_opt_int(place["parent_module_id"]),
                            capacity=_opt_int(place["capacity"]),
                        )
                    )
    return loaded_places


def load_cell_assignments(path: str | os.PathLike) -> List[CellAssignment]:
    with open(path) as f:
        return [
            CellAssignment(
                person_id=int(r["person_id"]),
                cell_place_id=int(r["cell_place_id"]),
                bunk_position=r["bunk_position"],
            )
            for r in csv.DictReader(f)
        ]


def load_layout(data_dir: str | os.PathLike) -> Layout:
    """Load all four structural CSVs from a directory."""
    places = load_places(os.path.join(data_dir, "layout.csv"))
    return Layout(
        modules=places["modules"],
        cells=places["cells"],
        shared_places=places["shared_places"],
        cell_assignments=load_cell_assignments(
            os.path.join(data_dir, "ng_cell_assignments.csv")
        ),
    )

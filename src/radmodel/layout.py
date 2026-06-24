"""Reader for the structural-layout CSVs (see references/specs/structural-layout-v1.md).

Exposes facility structure (modules, cells, shared places, cell assignments)
as queryable dataclasses. The simulation core does not yet consume this; it
is descriptive metadata for future schedule/movement work.
"""

import csv
import os
from dataclasses import dataclass, field
import string
from typing import Dict, List, Optional


@dataclass
class Agent:
    person_id: int
    module_id: int
    cell_id: int
    cell_place_id: int


@dataclass
class Cell:
    place_id: int
    module_id: Optional[int]
    tier: Optional[str]
    cell_number: int
    housing_category: str  # "GP", "RH", "MI"
    bunk_capacity: int
    name: str
    occupants: List[Agent] = field(default_factory=list)


@dataclass
class SharedPlace:
    place_id: int
    name: str
    place_type: str
    module_id: Optional[int]
    occupants: List[Agent] = field(default_factory=list)


@dataclass
class Module:
    module_id: int
    letter: str
    cells: List[Cell] = field(default_factory=list)
    shared_places: List[SharedPlace] = field(default_factory=list)

    def add_cell(self, cell):
        self.cells.append(cell)


@dataclass
class Layout:
    modules: Dict[int, Module] = field(default_factory=dict)
    shared_places: Dict[str, SharedPlace] = field(default_factory=dict)

    def add_module(self, module: Module):
        self.modules.update({module.module_id: module})

    def add_shared_place(self, shared_place: SharedPlace):
        self.shared_places.update({shared_place.name: shared_place})

    def load_places(self, path: str | os.PathLike):
        with open(os.path.join(path, "ng_places.csv")) as f:
            for r in csv.DictReader(f):
                if r["type"] == "facility":
                    print(int(r["place_id"]))
                    self.add_module(Module(module_id=int(r["place_id"]), letter="Z"))
                elif r["type"] == "module":
                    letter = string.ascii_lowercase[int(r["place_id"]) - 2012]
                    self.add_module(Module(module_id=int(r["place_id"]), letter=letter))
                elif r["type"] == "cell":
                    self.modules[int(r["parent_id"])].add_cell(
                        Cell(
                            place_id=int(r["place_id"]),
                            module_id=_opt_int(r["parent_id"]),
                            tier=_opt_str(r["tier"]),
                            cell_number=int(r["place_id"]),
                            housing_category=r["subtype"],
                            bunk_capacity=int(r["capacity"]),
                            name=r["name"],
                        )
                    )

                elif r["type"] == "shared":
                    print(int(r["place_id"]))
                    print(r["subtype"])
                    if r["subtype"] == "module":
                        print(int(r["place_id"]))
                        self.add_module(Module(module_id=int(r["place_id"]), letter=""))
                    else:
                        self.add_shared_place(
                            SharedPlace(
                                place_id=int(r["place_id"]),
                                name=r["name"],
                                place_type=r["subtype"],
                                module_id=_opt_int(r["parent_id"]),
                                # capacity=_opt_int(r["capacity"]),
                            )
                        )


def _opt_int(s: str) -> Optional[int]:
    return int(s) if s != "" else None


def _opt_str(s: str) -> Optional[str]:
    return s if s != "" else None


def load_layout(data_dir: str | os.PathLike) -> Layout:
    """Load all four structural CSVs from a directory."""
    layout = Layout()
    layout.load_places(data_dir)
    return layout

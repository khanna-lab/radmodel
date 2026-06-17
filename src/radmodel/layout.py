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
    capacity: Optional[int]
    occupants: List[Agent] = field(default_factory=list)


@dataclass
class Module:
    module_id: int
    letter: str
    cells: List[Cell] = field(default_factory=list)

    def add_cell(self, cell):
        self.cells.append(cell)


@dataclass
class Layout:
    modules: Dict[str, Module] = field(default_factory=Dict)

    def add_module(self, module):
        self.modules.update(module)


def _opt_int(s: str) -> Optional[int]:
    return int(s) if s != "" else None


def _opt_str(s: str) -> Optional[str]:
    return s if s != "" else None


def load_modules(path: str | os.PathLike) -> Dict[str, Module]:
    with open(path) as f:
        modules = {
            r["module_id"]: Module(module_id=int(r["module_id"]), letter=r["letter"])
            for r in csv.DictReader(f)
        }
        modules["-1"] = Module(module_id=-1, letter="NA")
        return modules


def load_cells(path, modules):
    with open(path) as f:
        for r in csv.DictReader(f):
            module_id = r["module_id"] if r["module_id"] != "" else "-1"
            if "type" not in r or r["type"] == "cell":
                modules[module_id].add_cell(
                    Cell(
                        place_id=int(r["place_id"]),
                        module_id=_opt_int(r["module_id"]),
                        tier=_opt_str(r["tier"]),
                        cell_number=int(r["cell_number"]),
                        housing_category=r["housing_category"],
                        bunk_capacity=int(r["bunk_capacity"]),
                        name=r["name"],
                    )
                )
            elif r["type"] == "shared":
                modules[module_id]["shared_places"].append(
                    SharedPlace(
                        place_id=int(r["place_id"]),
                        name=r["name"],
                        place_type=r["place_type"],
                        module_id=_opt_int(r["module_id"]),
                        capacity=_opt_int(r["capacity"]),
                    )
                )


def load_layout(data_dir: str | os.PathLike) -> Layout:
    """Load all four structural CSVs from a directory."""
    modules = load_modules(os.path.join(data_dir, "ng_modules.csv"))
    print(modules["0"].cells)
    load_cells(os.path.join(data_dir, "ng_cells.csv"), modules)
    return Layout(
        modules=modules,
    )

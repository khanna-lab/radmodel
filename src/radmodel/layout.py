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


@dataclass
class Cell:
    place_id: int
    module_id: Optional[int]
    tier: Optional[str]
    cell_number: int
    housing_category: str          # "GP", "RH", "MI"
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
    bunk_position: str             # "bottom", "top", "third"


@dataclass
class Layout:
    modules: List[Module] = field(default_factory=list)
    cells: List[Cell] = field(default_factory=list)
    shared_places: List[SharedPlace] = field(default_factory=list)
    cell_assignments: List[CellAssignment] = field(default_factory=list)

    def module_by_letter(self) -> Dict[str, Module]:
        return {m.letter: m for m in self.modules}

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


def load_modules(path: str | os.PathLike) -> List[Module]:
    with open(path) as f:
        return [Module(module_id=int(r["module_id"]), letter=r["letter"])
                for r in csv.DictReader(f)]


def load_cells(path: str | os.PathLike) -> List[Cell]:
    with open(path) as f:
        return [
            Cell(
                place_id=int(r["place_id"]),
                module_id=_opt_int(r["module_id"]),
                tier=_opt_str(r["tier"]),
                cell_number=int(r["cell_number"]),
                housing_category=r["housing_category"],
                bunk_capacity=int(r["bunk_capacity"]),
                name=r["name"],
            )
            for r in csv.DictReader(f)
        ]


def load_shared_places(path: str | os.PathLike) -> List[SharedPlace]:
    with open(path) as f:
        return [
            SharedPlace(
                place_id=int(r["place_id"]),
                name=r["name"],
                place_type=r["place_type"],
                parent_module_id=_opt_int(r["parent_module_id"]),
                capacity=_opt_int(r["capacity"]),
            )
            for r in csv.DictReader(f)
        ]


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
    return Layout(
        modules=load_modules(os.path.join(data_dir, "ng_modules.csv")),
        cells=load_cells(os.path.join(data_dir, "ng_cells.csv")),
        shared_places=load_shared_places(os.path.join(data_dir, "ng_shared_places.csv")),
        cell_assignments=load_cell_assignments(
            os.path.join(data_dir, "ng_cell_assignments.csv")
        ),
    )

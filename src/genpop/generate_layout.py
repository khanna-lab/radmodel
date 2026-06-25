"""Structural layout generator (Moran Medium Security).

Implements `references/specs/structural-layout-v1.md`. Emits four CSVs
describing facility structure as descriptive metadata; the running simulation
is unaffected.

Outputs (into the target directory):
  - ng_modules.csv           modules A..J
  - ng_cells.csv             all cells (GP module cells + RH + MI) with
                             tier, cell_number, housing_category, bunk_capacity
  - ng_shared_places.csv     dayrooms, showers, dining, gym, yard, education,
                             industries, visit, medical, chapel, barber, seg
  - ng_cell_assignments.csv  1200 residents mapped to GP cells with bunk position
"""
import csv
import os
from typing import Dict, List


N_MODULES = 10
MODULE_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
TIERS = ["bottom", "top"]
N_CELLS_PER_TIER = 29
N_CELLS_PER_MODULE = len(TIERS) * N_CELLS_PER_TIER
N_MODULE_CELLS = N_MODULES * N_CELLS_PER_MODULE  # 580

N_RH_CELLS = 30
N_MI_CELLS = 20

N_RESIDENTS = 1200
# 1200 residents - 1160 nominal capacity (580 cells * 2 bunks) = 40 overflow.
# Spread evenly: 4 triple-bunked cells per module, lowest cell_numbers in bottom tier.
OVERFLOW = max(0, N_RESIDENTS - N_MODULE_CELLS * 2)
N_TRIPLE_PER_MODULE = OVERFLOW // N_MODULES  # 4

# Place_id namespaces (gaps reserved for forward compatibility)
CELL_ID_START = 0          # cells: GP + RH + MI
SUBPLACE_ID_START = 1000   # dayrooms + showers (one of each per module)
SHARED_ID_START = 2000     # facility-shared places

SHARED_PLACES = [
    ("dining_room_1", "dining_room"),
    ("dining_room_2", "dining_room"),
    ("gym", "gym"),
    ("yard", "yard"),
    ("education_building", "education"),
    ("industries_building", "industry"),
    ("visiting_room", "visit_room"),
    ("medical", "medical"),
    ("chapel", "chapel"),
    ("barber", "barber"),
    ("segregation_unit", "segregation"),
]


def generate_modules() -> List[Dict]:
    return [{"module_id": i, "letter": MODULE_LETTERS[i]} for i in range(N_MODULES)]


def generate_cells() -> List[Dict]:
    rows: List[Dict] = []
    place_id = CELL_ID_START

    for m_id in range(N_MODULES):
        letter = MODULE_LETTERS[m_id]
        triple_numbers = set(range(1, N_TRIPLE_PER_MODULE + 1))
        for tier in TIERS:
            for cell_number in range(1, N_CELLS_PER_TIER + 1):
                bunks = 3 if (tier == "bottom" and cell_number in triple_numbers) else 2
                rows.append({
                    "place_id": place_id,
                    "module_id": m_id,
                    "tier": tier,
                    "cell_number": cell_number,
                    "housing_category": "GP",
                    "bunk_capacity": bunks,
                    "name": f"cell_{letter}_{tier}_{cell_number}",
                })
                place_id += 1

    for i in range(N_RH_CELLS):
        rows.append({
            "place_id": place_id,
            "module_id": "",
            "tier": "",
            "cell_number": i + 1,
            "housing_category": "RH",
            "bunk_capacity": 1,
            "name": f"seg_cell_{i + 1}",
        })
        place_id += 1

    for i in range(N_MI_CELLS):
        rows.append({
            "place_id": place_id,
            "module_id": "",
            "tier": "",
            "cell_number": i + 1,
            "housing_category": "MI",
            "bunk_capacity": 1,
            "name": f"mi_cell_{i + 1}",
        })
        place_id += 1

    return rows


def generate_shared_places() -> List[Dict]:
    rows: List[Dict] = []

    place_id = SUBPLACE_ID_START
    for m_id in range(N_MODULES):
        letter = MODULE_LETTERS[m_id]
        rows.append({
            "place_id": place_id,
            "name": f"dayroom_{letter}",
            "place_type": "dayroom",
            "parent_module_id": m_id,
            "capacity": "",
        })
        place_id += 1
        rows.append({
            "place_id": place_id,
            "name": f"shower_{letter}",
            "place_type": "shower",
            "parent_module_id": m_id,
            "capacity": "",
        })
        place_id += 1

    place_id = SHARED_ID_START
    for name, place_type in SHARED_PLACES:
        rows.append({
            "place_id": place_id,
            "name": name,
            "place_type": place_type,
            "parent_module_id": "",
            "capacity": "",
        })
        place_id += 1

    return rows


def generate_cell_assignments(cells: List[Dict]) -> List[Dict]:
    gp_cells = [c for c in cells if c["housing_category"] == "GP"]
    total_capacity = sum(c["bunk_capacity"] for c in gp_cells)
    if total_capacity < N_RESIDENTS:
        raise ValueError(
            f"GP capacity {total_capacity} < residents {N_RESIDENTS}"
        )

    rows: List[Dict] = []
    person_id = 0
    bunk_names = ["bottom", "top", "third"]
    for cell in gp_cells:
        for bunk in bunks_for(cell["bunk_capacity"], bunk_names):
            if person_id >= N_RESIDENTS:
                return rows
            rows.append({
                "person_id": person_id,
                "cell_place_id": cell["place_id"],
                "bunk_position": bunk,
            })
            person_id += 1
    return rows


def bunks_for(capacity: int, names: List[str]) -> List[str]:
    return names[:capacity]


def write_csv(path: str | os.PathLike, rows: List[Dict], fieldnames: List[str]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def generate_all(output_dir: str | os.PathLike) -> Dict[str, int]:
    os.makedirs(output_dir, exist_ok=True)

    modules = generate_modules()
    cells = generate_cells()
    shared = generate_shared_places()
    assignments = generate_cell_assignments(cells)

    write_csv(
        os.path.join(output_dir, "ng_modules.csv"),
        modules,
        ["module_id", "letter"],
    )
    write_csv(
        os.path.join(output_dir, "ng_cells.csv"),
        cells,
        ["place_id", "module_id", "tier", "cell_number",
         "housing_category", "bunk_capacity", "name"],
    )
    write_csv(
        os.path.join(output_dir, "ng_shared_places.csv"),
        shared,
        ["place_id", "name", "place_type", "parent_module_id", "capacity"],
    )
    write_csv(
        os.path.join(output_dir, "ng_cell_assignments.csv"),
        assignments,
        ["person_id", "cell_place_id", "bunk_position"],
    )

    return {
        "modules": len(modules),
        "cells": len(cells),
        "shared_places": len(shared),
        "cell_assignments": len(assignments),
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    p.add_argument("output_dir", help="Directory to write the layout CSVs")
    args = p.parse_args()
    counts = generate_all(args.output_dir)
    print(f"Wrote layout to {args.output_dir}: {counts}")

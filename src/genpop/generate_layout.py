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
import string
from pathlib import Path
from typing import Dict, List
import yaml


def get_params(input_dir="params", input_file="module_definition.yaml"):
    input_dir = Path(input_dir, input_file)
    with open(input_dir, "r") as f:
        return yaml.safe_load(f)["facility"]


# N_MODULES = 10
# MODULE_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
# TIERS = ["bottom", "top"]
# N_CELLS_PER_TIER = 29
# N_CELLS_PER_MODULE = len(TIERS) * N_CELLS_PER_TIER
# N_MODULE_CELLS = N_MODULES * N_CELLS_PER_MODULE  # 580

# N_RH_CELLS = 30
# N_MI_CELLS = 20

# N_RESIDENTS = 1200
# # 1200 residents - 1160 nominal capacity (580 cells * 2 bunks) = 40 overflow.
# # Spread evenly: 4 triple-bunked cells per module, lowest cell_numbers in bottom tier.
# OVERFLOW = max(0, N_RESIDENTS - N_MODULE_CELLS * 2)
# N_TRIPLE_PER_MODULE = OVERFLOW // N_MODULES  # 4

# # Place_id namespaces (gaps reserved for forward compatibility)
# SUBPLACE_ID_START = 1000   # dayrooms + showers (one of each per module)
# SHARED_ID_START = 2000     # facility-shared places

# SHARED_PLACES = [
#     ("dining_room_1", "dining_room"),
#     ("dining_room_2", "dining_room"),
#     ("gym", "gym"),
#     ("yard", "yard"),
#     ("education_building", "education"),
#     ("industries_building", "industry"),
#     ("visiting_room", "visit_room"),
#     ("medical", "medical"),
#     ("chapel", "chapel"),
#     ("barber", "barber"),
#     ("segregation_unit", "segregation"),
# ]


def generate_modules(params) -> List[Dict]:
    return [
        {"module_id": i, "letter": string.ascii_uppercase[i]}
        for i in range(params["modules"]["count"])
    ]


def generate_cells(params, modules) -> List[Dict]:
    rows: List[Dict] = []
    place_id = params["place_ids"]["cell_id_start"]
    num_cells_per_module = sum(
        [tier["cells_per_tier"] for tier in params["tiers"]]
    )
    overflow = max(
        0,
        params["residents"]["count"]
        - num_cells_per_module
        * len(modules)
        * params["cells"]["gp"]["default_bunk_capacity"],
    )
    n_triple_per_module = overflow // len(modules)

    for module in modules:
        letter = module["letter"]
        # overflow_cells = set(range(n_triple_per_module))
        overflow = 0
        for tier in params["tiers"]:
            cell_params = params["cells"]["gp"]
            for cell_number in range(tier["cells_per_tier"]):
                # TO_REVIEW this breaks if more triples than fit on one tier
                capacity = cell_params["overflow"]["overflow_bunk_capacity"] if overflow < n_triple_per_module else cell_params["default_bunk_capacity"]
                overflow += 1
                rows.append(
                    {
                        "place_id": place_id,
                        "module_id": module["module_id"],
                        "tier": tier["name"],
                        "cell_number": cell_number,
                        "housing_category": cell_params["housing_category"],
                        "bunk_capacity": capacity,
                        "name": f"cell_{letter}_{tier['name']}_{cell_number}",
                    }
                )
                place_id += 1
        for special_cell in params["cells"]["special"]:
            for i in range(special_cell["count"]):
                rows.append(
                    {
                        "place_id": place_id,
                        "module_id": "",
                        "tier": "",
                        "cell_number": i,
                        "housing_category": special_cell["housing_category"],
                        "bunk_capacity": special_cell["bunk_capacity"],
                        "name": f"{special_cell['name_prefix']}_{i}",
                    }
                )
                place_id += 1

    return rows


def generate_shared_places(params, modules) -> List[Dict]:
    rows: List[Dict] = []

    place_id = params["place_ids"]["subplace_id_start"]
    for module in modules:
        for place in params["subplaces"]:
            rows.append(
                {
                    "place_id": place_id,
                    "name": f"{place['place_type']}_{module['letter']}",
                    "place_type": place["place_type"],
                    "parent_module_id": module["module_id"],
                    "capacity": place["capacity"],
                }
            )
            place_id += 1


    place_id = params["place_ids"]["shared_id_start"]
    for place in params["shared_places"]:
        rows.append(
            {
                "place_id": place_id,
                "name": place["name"],
                "place_type": place["place_type"],
                "parent_module_id": "",
                "capacity": "",
            }
        )
        place_id += 1

    return rows


def generate_cell_assignments(params, cells: List[Dict]) -> List[Dict]:
    gp_cells = [c for c in cells if c["housing_category"] == "GP"]
    total_capacity = sum(c["bunk_capacity"] for c in gp_cells)
    if total_capacity < params["residents"]["count"]:
        raise ValueError(f"GP capacity {total_capacity} < residents {params['residents']['count']}")

    rows: List[Dict] = []
    person_id = 0
    bunk_names = ["bottom", "top", "third"]
    for cell in gp_cells:
        for bunk in bunks_for(cell["bunk_capacity"], bunk_names):
            if person_id >= params["residents"]["count"]:
                return rows
            rows.append(
                {
                    "person_id": person_id,
                    "cell_place_id": cell["place_id"],
                    "bunk_position": bunk,
                }
            )
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
    params = get_params()
    modules = generate_modules(params)
    cells = generate_cells(params, modules)
    shared = generate_shared_places(params, modules)
    assignments = generate_cell_assignments(params, cells)

    write_csv(
        os.path.join(output_dir, "ng_modules.csv"),
        modules,
        ["module_id", "letter"],
    )
    write_csv(
        os.path.join(output_dir, "ng_cells.csv"),
        cells,
        [
            "place_id",
            "module_id",
            "tier",
            "cell_number",
            "housing_category",
            "bunk_capacity",
            "name",
        ],
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


get_params()

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    p.add_argument("output_dir", help="Directory to write the layout CSVs")
    args = p.parse_args()
    counts = generate_all(args.output_dir)
    print(f"Wrote layout to {args.output_dir}: {counts}")

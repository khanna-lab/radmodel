import csv
import os
import string
import random
import yaml
from typing import Any


def parse_schedule_ids(schedules_file: str | os.PathLike) -> list[int]:
    with open(schedules_file) as fin:
        reader = csv.reader(fin)
        header = next(reader)
        id_idx = header.index("schedule_id")
        ids = [int(row[id_idx]) for row in reader]

    return ids


# def generate_persons(
#     num_persons: int,
#     places_file: str | os.PathLike,
#     mod_def_file: str | os.PathLike,
#     output_file: str | os.PathLike,
# ):
#     print("Warning: Using Single Schedule 0")

#     places = parse_places(places_file)
#     n_cells = len(places["cell"])

#     with open(mod_def_file) as fin:
#         mod_def = yaml.safe_load(fin)
#     n_mods = len(mod_def)

#     cell_idx = 0
#     mod_idx = 0
#     mod_acts = mod_def[mod_idx]

#     # Round robin assignment of persons to cells, and within
#     # than round robin assignment of mods
#     with open(output_file, "w") as fout:
#         writer = csv.writer(fout)
#         writer.writerow(
#             [
#                 "person_id",
#                 "schedule_id",
#                 "cell",
#                 "cafeteria",
#                 "morning_act",
#                 "noon_act",
#                 "evening_act",
#                 "mod",
#             ]
#         )
#         for i in range(num_persons):
#             cell_id = places["cell"][cell_idx]
#             schedule_id = 0
#             cafeteria = random.choice(places["cafeteria"])
#             morning_act = random.choice(places[mod_acts[0]])
#             afternoon_act = random.choice(places[mod_acts[1]])
#             evening_act = random.choice(places[mod_acts[2]])

#             writer.writerow(
#                 [
#                     i,
#                     schedule_id,
#                     cell_id,
#                     cafeteria,
#                     morning_act,
#                     afternoon_act,
#                     evening_act,
#                     mod_idx,
#                 ]
#             )

#             mod_idx += 1
#             if mod_idx == n_mods:
#                 mod_idx = 0
#             mod_acts = mod_def[mod_idx]

#             cell_idx += 1
#             if cell_idx == n_cells:
#                 cell_idx = 0


def generate_schedule(schedule_id: int):
    # in cell from midnight to 6AM, 7PM to midnight
    acts = [[schedule_id, 0, "cell", 1], [schedule_id, 19 * 60, "cell", 1]]

    breakfast = random.choice([6, 7])
    lunch = random.choice([11, 12, 13])
    dinner = random.choice([17, 18])

    acts += [
        [schedule_id, breakfast * 60, "cafeteria", 1],
        [schedule_id, lunch * 60, "cafeteria", 1],
        [schedule_id, dinner * 60, "cafeteria", 1],
    ]

    # activities between breakfast and lunch
    morning_acts = [
        [schedule_id, h * 60, "activity", 1] for h in range(breakfast + 1, lunch)
    ]
    afternoon_acts = [
        [schedule_id, h * 60, random.choice(["outdoor", "activity", "activity"]), 1]
        for h in range(lunch + 1, dinner)
    ]
    acts += morning_acts + afternoon_acts

    acts.sort(key=lambda x: x[1])
    return acts


def generate_schedules(num_schedules: int, output_file: str | os.PathLike):
    with open(output_file, "w") as fout:
        writer = csv.writer(fout)
        writer.writerow(["schedule_id", "start", "place_type", "risk"])

        for i in range(num_schedules):
            acts = generate_schedule(i)
            writer.writerows(acts)


def get_params(mod_def_file: str | os.PathLike) -> dict[str, Any]:
    with open(mod_def_file) as fin:
        return yaml.safe_load(fin)


def generate_places(mod_def_file: str | os.PathLike, output_file: str | os.PathLike):
    """Generates a csv containing all places, fields:
    place_id | name | type | subtype | tier | capacity | parent_id

    Parameters
    ==========
    mod_def_file: str | os.PathLike
        Path to a .yaml file containing parameters to define the setting
    output_file: str | os.PathLike
        Path to file location to save the place csv.
    """

    data = get_params(mod_def_file)

    module = data.get("facility")
    assert module is not None
    module_name = module["name"]
    n_modules = module["modules"]["count"]
    module_letters = [string.ascii_uppercase[i] for i in range(n_modules)]
    tiers = module["tiers"]
    gp_cells = module["cells"]["gp"]
    special_cells = module["cells"]["special"]
    subplaces = module["subplaces"]
    shared_places = module["shared_places"]

    cell_id = module["place_ids"]["cell_id_start"]
    subplace_id = module["place_ids"]["subplace_id_start"]
    shared_id = module["place_ids"]["shared_id_start"]

    facility_id = max(
        shared_id + len(shared_places), subplace_id + len(subplaces) * n_modules
    )
    module_id_start = facility_id + 1

    module_parent_by_letter = {
        letter: module_id_start + i for i, letter in enumerate(module_letters)
    }

    rows = [
        {
            "place_id": facility_id,
            "name": module_name,
            "type": "facility",
            "parent_id": "",
        }
    ]
    for letter in module_letters:
        rows.append(
            {
                "place_id": module_parent_by_letter[letter],
                "name": f"module_{letter}",
                "type": "module",
                "parent_id": facility_id,
            }
        )

    special_parent_ids: dict[str, int] = {}

    for place in shared_places:
        rows.append(
            {
                "place_id": shared_id,
                "name": place["name"],
                "type": "shared",
                "subtype": place["place_type"],
                "parent_id": facility_id,
            }
        )
        special_parent_ids[place["place_type"]] = shared_id
        shared_id += 1

    for letter in module_letters:
        parent_id = module_parent_by_letter[letter]
        for tier in tiers:
            tier_name = tier["name"]
            cells_per_tier = tier["cells_per_tier"]
            for n in range(1, cells_per_tier + 1):
                rows.append(
                    {
                        "place_id": cell_id,
                        "name": f"cell_{letter}_{tier_name}_{n}",
                        "type": "cell",
                        "subtype": gp_cells["housing_category"].lower(),
                        "tier": tier["name"],
                        "capacity": gp_cells["default_bunk_capacity"],
                        "overflow_capacity": gp_cells["overflow"][
                            "overflow_bunk_capacity"
                        ],
                        "parent_id": parent_id,
                    }
                )
                cell_id += 1

    for special in special_cells:  # cells outside the general population category
        housing_category = special["housing_category"]
        place_type = housing_category.lower()
        if housing_category == "RH":
            parent_id = special_parent_ids.get("segregation", facility_id)
        elif housing_category == "MI":
            parent_id = special_parent_ids.get("medical", facility_id)
        else:
            parent_id = facility_id

        for i in range(1, special["count"] + 1):
            rows.append(
                {
                    "place_id": cell_id,
                    "name": f"{special['name_prefix']}_{i}",
                    "type": "cell",
                    "subtype": place_type,
                    "capacity": special["bunk_capacity"],
                    "overflow_capacity": special["bunk_capacity"],
                    "parent_id": parent_id,
                }
            )
            cell_id += 1

    for letter in module_letters:
        parent_id = module_parent_by_letter[letter]
        for subplace in subplaces:
            rows.append(
                {
                    "place_id": subplace_id,
                    "name": subplace["name_template"].format(module_letter=letter),
                    "type": "subplace",
                    "subtype": subplace["place_type"],
                    "parent_id": parent_id,
                }
            )
            subplace_id += 1

    with open(output_file, "w") as fout:
        writer = csv.DictWriter(
            fout,
            fieldnames=[
                "place_id",
                "name",
                "type",
                "subtype",
                "tier",
                "capacity",
                "parent_id",
                "overflow_capacity",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def generate_cell_assignments(
    mod_def_file, cells: list[dict], output_file: str | os.PathLike
) -> list[dict]:
    data = get_params(mod_def_file)
    module = data.get("facility")
    assert module is not None
    n_residents = module["residents"]["count"]

    gp_cells = [c for c in cells if c.get("subtype") == "gp"]
    total_capacity = sum(c["overflow_capacity"] for c in gp_cells)
    if total_capacity < n_residents:
        raise ValueError(f"GP capacity {total_capacity} < residents {n_residents}")

    rows: list[dict] = []
    bunk_names = ["bottom", "top", "third"]
    for i in range(n_residents):
        cell = gp_cells.pop(0)
        cell["occupants"] = cell["occupants"] + 1 if cell.get("occupants") else 1
        rows.append(
            {
                "person_id": i,
                "module_id": cell["parent_id"],
                "cell_place_id": cell["place_id"],
                "bunk_position": bunk_names[cell["occupants"] - 1],
            }
        )
        if cell["occupants"] < cell["overflow_capacity"]:
            gp_cells.append(cell)
    with open(output_file, "w") as fout:
        writer = csv.DictWriter(
            fout,
            fieldnames=[
                "person_id",
                "module_id",
                "cell_place_id",
                "bunk_position",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


def generate_residents(
    mod_def_file, places: list[dict], output_file: str | os.PathLike
):
    generate_cell_assignments(mod_def_file, places, output_file)


if __name__ == "__main__":
    places = generate_places("params/module_definition.yaml", "data/ng_places.csv")
    generate_cell_assignments(
        "params/module_definition.yaml", places, "data/ng_cell_assignments_test.csv"
    )

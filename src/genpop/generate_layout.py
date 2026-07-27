import csv
import os
import string
from typing import Dict, List
import yaml


def get_params(mod_def_file):
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

    special_parent_ids: Dict[str, int] = {}

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
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    generate_places("params/module_definition.yaml", "data/ng_places.csv")

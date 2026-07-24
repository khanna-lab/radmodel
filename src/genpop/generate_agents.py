def generate_persons(
    num_persons: int,
    places_file: str | os.PathLike,
    mod_def_file: str | os.PathLike,
    output_file: str | os.PathLike,
):
    print("Warning: Using Single Schedule 0")

    places = parse_places(places_file)
    n_cells = len(places["cell"])

    with open(mod_def_file) as fin:
        mod_def = yaml.safe_load(fin)
    n_mods = len(mod_def)

    cell_idx = 0
    mod_idx = 0
    mod_acts = mod_def[mod_idx]

    # Round robin assignment of persons to cells, and within
    # than round robin assignment of mods
    with open(output_file, "w") as fout:
        writer = csv.writer(fout)
        writer.writerow(
            [
                "person_id",
                "schedule_id",
                "cell",
                "cafeteria",
                "morning_act",
                "noon_act",
                "evening_act",
                "mod",
            ]
        )
        for i in range(num_persons):
            cell_id = places["cell"][cell_idx]
            schedule_id = 0
            cafeteria = random.choice(places["cafeteria"])
            morning_act = random.choice(places[mod_acts[0]])
            afternoon_act = random.choice(places[mod_acts[1]])
            evening_act = random.choice(places[mod_acts[2]])

            writer.writerow(
                [
                    i,
                    schedule_id,
                    cell_id,
                    cafeteria,
                    morning_act,
                    afternoon_act,
                    evening_act,
                    mod_idx,
                ]
            )

            mod_idx += 1
            if mod_idx == n_mods:
                mod_idx = 0
            mod_acts = mod_def[mod_idx]

            cell_idx += 1
            if cell_idx == n_cells:
                cell_idx = 0

                
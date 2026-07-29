import csv
import os
import random

from radmodel.layout import Layout


def parse_schedule_ids(schedules_file: str | os.PathLike) -> list[int]:
    with open(schedules_file) as fin:
        reader = csv.reader(fin)
        header = next(reader)
        id_idx = header.index("schedule_id")
        ids = [int(row[id_idx]) for row in reader]

    return ids


def get_layout(places_file):
    layout = Layout()
    layout.load_places(places_file)


def generate_persons(
    layout: Layout,
    num_persons: int,
    output_file: str | os.PathLike,
):
    print("Warning: Using Single Schedule 0")

    n_mods = len(layout.modules)
    agents_per_module = num_persons // n_mods
    agent_id = 0
    cell_idx = 0
    agents = []

    for module_id, module in layout.modules.items():
        # TODO too few values to ensure even distribution, this should be redone
        cafeteria = random.choice(
            list(layout.cafeterias.values())
        )  # cafeteria is for whole module

        for i in range(agents_per_module):
            cell = module.cells[cell_idx]
            schedule_id = 0  # TODO need multiple schedule ids?

            morning_activity = random.choice(list(layout.shared_places.values()))
            afternoon_activity = random.choice(list(layout.shared_places.values()))
            evening_activity = random.choice(list(layout.shared_places.values()))
            agents.append(
                {
                    "person_id": agent_id,
                    "module_id": module_id,
                    "cell_place_id": cell.place_id,
                    "morning_act_name": morning_activity.name,
                    "afternoon_act_name": afternoon_activity.name,
                    "evening_act_name": evening_activity.name,
                    "schedule_id": schedule_id,
                    "cafeteria": cafeteria,
                }
            )
            agent_id += 1
            cell_idx += 1
            if cell_idx == len(module.cells):
                cell_idx = 0

    with open(output_file, "w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "person_id",
                "module_id",
                "cell_place_id",
                "morning_act_name",
                "afternoon_act_name",
                "evening_act_name",
                "schedule_id",
                "cafeteria",
            ],
        )
        writer.writeheader()
        for i in agents:
            writer.writerow(i)
    return agents


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

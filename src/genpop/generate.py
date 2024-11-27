import csv
import os
from typing import Dict, List
import random


def parse_places(places_file: str | os.PathLike) -> Dict[str, int]:
    places = {}
    with open(places_file) as fin:
        reader = csv.reader(fin)
        header = next(reader)
        id_idx = header.index("place_id")
        type_idx = header.index("type")
        for row in reader:
            id = int(row[id_idx])
            p_type = row[type_idx]
            if p_type in places:
                places[p_type].append(id)
            else:
                places[p_type] = [id]

        return places


def parse_schedule_ids(schedules_file: str | os.PathLike) -> List[int]:
    with open(schedules_file) as fin:
        reader = csv.reader(fin)
        header = next(reader)
        id_idx = header.index("schedule_id")
        ids = [int(row[id_idx]) for row in reader]

    return ids


def generate_persons(num_persons: int, persons_per_cell: int, places_file: str | os.PathLike,
                     schedules_file: str | os.PathLike, output_file: str | os.PathLike):
    places = parse_places(places_file)
    schedule_ids = parse_schedule_ids(schedules_file)
    n_cells = len(places["cell"])
    if num_persons / persons_per_cell > n_cells:
        raise ValueError(f"Not enough cells for {num_persons} and {persons_per_cell} persons per cell")

    cell_idx = 0
    n_in_cell = 0
    with open(output_file, "w") as fout:
        writer = csv.writer(fout)
        writer.writerow(["person_id", "schedule_id", "cell", "activities", "cafeterias", "outdoors"])
        for i in range(num_persons):
            cell_id = places["cell"][cell_idx]
            schedule_id = random.choice(schedule_ids)
            acts = [str(x) for x in random.sample(places["activity"], 2)]
            cafs = [str(x) for x in random.sample(places["cafeteria"], 2)]
            outdoors = places["outdoor"][0]
            writer.writerow([i, schedule_id, cell_id, "|".join(acts), "|".join(cafs), outdoors])

            n_in_cell += 1
            if n_in_cell == persons_per_cell:
                cell_idx += 1
                n_in_cell = 0


def generate_schedule(schedule_id: int):
    # in cell from midnight to 6AM, 7PM to midnight
    acts = [[schedule_id, 0, "cell", 1],
            [schedule_id, 19 * 60, "cell", 1]]

    breakfast = random.choice([6, 7])
    lunch = random.choice([11, 12, 13])
    dinner = random.choice([17, 18])

    acts += [[schedule_id, breakfast * 60, "cafeteria", 1],
             [schedule_id, lunch * 60, "cafeteria", 1],
             [schedule_id, dinner * 60, "cafeteria", 1]]

    # activities between breakfast and lunch
    morning_acts = [[schedule_id, h * 60, "activity", 1] for h in range(breakfast + 1, lunch)]
    afternoon_acts = [[schedule_id, h * 60, random.choice(["outdoor", "activity", "activity"]), 1]
                      for h in range(lunch + 1, dinner)]
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

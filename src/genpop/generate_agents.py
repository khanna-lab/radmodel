import os
import random

import polars as pl

from radmodel.layout import Layout


def generate_agents(
    num_persons: int,
    places_file: str | os.PathLike,
    output_file: str | os.PathLike | None = None,
    save_output: bool = True,
) -> pl.DataFrame:
    """Generate agents with the given parameters.

    Parameters
    ==========
    num_persons: int
        number of agents to generate
    places_file: str | os.PathLike
        Path to a .csv file containing places
    output_file: str | os.PathLike
        Path to save outputs

    Returns
    =======
    pl.Dataframe
        Agent data
    """
    print("Warning: Using Single Schedule 0")

    layout = Layout.load_from_csv(places_file)
    n_mods = len(layout.modules)
    agents_per_module = num_persons // n_mods
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
            # n.b. making and printing a concat df doesn't make sense until we remove intermediate i/o
            agents.append(
                pl.DataFrame(
                    {
                        "person_id": i,
                        "module_id": module_id,
                        "cell_place_id": cell.place_id,
                        "morning_act_name": morning_activity.name,
                        "afternoon_act_name": afternoon_activity.name,
                        "evening_act_name": evening_activity.name,
                        "schedule_id": schedule_id,
                        "cafeteria": cafeteria.place_id,
                    }
                )
            )
            
            cell_idx += 1
            if cell_idx == len(module.cells):
                cell_idx = 0

    agents_df = pl.concat(agents)
    if save_output:
        agents_df.write_csv(output_file)

    return agents_df


def generate_schedule(schedule_id: int) -> pl.DataFrame:
    """Generates a schedule for an agent.

    Parameters
    ==========
    schedule_id: int
        A number indicating the baseline schedule the agent adheres to

    Returns
    pl.DataFrame
        Schedule information
    """
    # in cell from midnight to 6AM, 7PM to midnight
    # acts = [(schedule_id, 0, "cell", 1), (schedule_id, 19 * 60, "cell", 1)]
    acts = {
        "schedule_id": schedule_id,
        "start": [0, 19 * 60],
        "place_type": ["cell", "cell"],
        "risk": 1,
    }

    breakfast = random.choice([6, 7])
    lunch = random.choice([11, 12, 13])
    dinner = random.choice([17, 18])

    acts["start"] += [breakfast * 60, lunch * 60, dinner * 60]
    acts["place_type"] += ["cafeteria"] * 3

    # acts = pl.DataFrame(acts)
    # activities between breakfast and lunch
    morning_acts = [a*60 for a in range(breakfast + 1, lunch)]
    acts["start"] += morning_acts
    acts["place_type"] += ["morning_act"] * len(morning_acts)
    for a in range(lunch + 1, dinner):
        acts["start"].append(a * 60)
        acts["place_type"].append(random.choice(["outdoor", "noon_act", "noon_act"]))

    acts_df = pl.DataFrame(acts)
    acts_df.sort(by="start")
    # TODO are there evening acts?

    return acts_df


def generate_schedules(num_schedules: int, output_file: str) -> pl.DataFrame:
    """Generates all baseline schedules.

    Parameters
    ==========
    num_schedules: int
        Number of different schedules to produce
    output_file
        File location to save.
    """
    dfs = pl.concat([generate_schedule(i) for i in range(num_schedules)])
    dfs.write_csv(output_file)
    return dfs

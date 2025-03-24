from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd 

# Load Data -------

input_path = Path("data")

input_residents = Path(input_path, "ng_residents.csv")
input_residents_df = pd.read_csv(input_residents)
#print(input_residents_df.head(), "\n")

input_places = Path(input_path, "ng_places.csv")
input_places_df = pd.read_csv(input_places)
#print(input_places_df.head(), "\n")

input_schedules = Path(input_path, "ng_schedules.csv")
input_schedules_df = pd.read_csv(input_schedules)
#print(input_schedules_df.head(), "\n")

movement_counts_csv = Path("output", "counts_by_place_5.csv")
movement_counts_df = pd.read_csv(movement_counts_csv)
#print(movement_counts_df.head(), "\n")


# Merge places with output data ---------

merged_movement_places = movement_counts_df.merge(input_places_df, 
    on="place_id")
print(merged_movement_places.head(), "\n")


# Visualize movement by space ---------

## gym
gym_counts = merged_movement_places[merged_movement_places["type"] == "gym"]
print(gym_counts.head())

## plot


plt.figure(figsize=(10, 5))
for gym_name, group in gym_counts.groupby("name"):
    plt.plot(group["tick"], group["person_count"], label=gym_name)
plt.show()
plt.savefig(Path("analysis", "gym_occupancy.png", dpi=300))


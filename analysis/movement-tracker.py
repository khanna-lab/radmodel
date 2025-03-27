# interpreter at /users/akhann16/sfw/pyenvs/radmodel-py3.11/bin/python

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd 
from matplotlib.ticker import MultipleLocator, FuncFormatter


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


# Helpfer functions ---------
# Format ticks as HH:MM
def format_time(x, pos):
    hours = int(x) // 60
    minutes = int(x) % 60
    return f"{hours:02d}:{minutes:02d}"


# Merge places with output data ---------

merged_movement_places = movement_counts_df.merge(input_places_df, 
    on="place_id")
print(merged_movement_places.head(), "\n")


# Visualize movement by space ---------

## gym

### data
gym_counts = merged_movement_places[merged_movement_places["type"] == "gym"]
print(gym_counts.head())


### plot
plt.figure(figsize=(10, 5))
for gym_name, group in gym_counts.groupby("name"):
    plt.plot(group["tick"], group["person_count"], label=gym_name)

hour_ticks = list(range(0, 96, 4))  

hour_labels = [f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]
print(hour_labels)

plt.xticks(hour_ticks, hour_labels, rotation=45)


plt.xlim(0, 96)
plt.xlabel("Time of Day")
plt.ylabel("People in Gym")
plt.title("Gym Occupancy – First Day Only")
plt.legend()
plt.grid(True)
plt.tight_layout()

#plt.show()
plt.savefig(Path("analysis", "gym_occupancy.png"))


## cafeteria
### data
cafeteria_counts = merged_movement_places[merged_movement_places["type"] == "cafeteria"]
print(cafeteria_counts.head())

### plot
plt.figure(figsize=(10, 5))
for cafeteria_name, group in cafeteria_counts.groupby("name"):
    plt.plot(group["tick"], group["person_count"], label=cafeteria_name)

hour_ticks = list(range(0, 96, 4))  

hour_labels = [f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]
print(hour_labels)

plt.xticks(hour_ticks, hour_labels, rotation=45)


plt.xlim(0, 96)
plt.xlabel("Time of Day")
plt.ylabel("People in cafeteria")
plt.title("cafeteria Occupancy – First Day Only")
plt.legend()
plt.grid(True)
plt.tight_layout()


plt.savefig(Path("analysis", "cafeteria_occupancy.png"))


## yard
### data
yard_counts = merged_movement_places[merged_movement_places["type"] == "yard"]
print(yard_counts.head())

### plot
plt.figure(figsize=(10, 5))
for yard_name, group in yard_counts.groupby("name"):
    plt.plot(group["tick"], group["person_count"], label=yard_name)

hour_ticks = list(range(0, 96, 4))  

hour_labels = [f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]
print(hour_labels)

plt.xticks(hour_ticks, hour_labels, rotation=45)


plt.xlim(0, 96)
plt.xlabel("Time of Day")
plt.ylabel("People in yard")
plt.title("yard Occupancy – First Day Only")
plt.legend()
plt.grid(True)
plt.tight_layout()


plt.savefig(Path("analysis", "yard_occupancy.png"))



# Visualize movement by person ---------


# Select person
person_id = 5

# distribution of schedules
input_residents_df["schedule_id"].describe()

# Get schedule_id and the person's place assignments
person_row = input_residents_df.loc[input_residents_df["person_id"] == person_id].iloc[0]
schedule_id = person_row["schedule_id"]

# Get full schedule for that ID
person_schedule = input_schedules_df[input_schedules_df["schedule_id"] == schedule_id].copy()


# Map place_type (like "cell", "cafeteria", etc.) to the actual place_id from this person
person_schedule["place_id"] = person_schedule["place_type"].apply(lambda pt: person_row[pt])

# Merge to get place names and types (now that we have place_id)
schedule_annotated = person_schedule.merge(input_places_df, on="place_id")
schedule_annotated["duration"] = schedule_annotated["start"].shift(-1) - schedule_annotated["start"] #duration computations
schedule_annotated.loc[schedule_annotated.index[-1], "duration"] = 1440 - schedule_annotated["start"].iloc[-1] #last row

print(schedule_annotated)
print(schedule_annotated["place_type"].value_counts())
print(schedule_annotated[["place_type", "name", "type"]])

# Define y-axis code for plotting
place_type_order = ["cell", "cafeteria", "gym", "yard", "education"]
place_type_to_code = {ptype: i for i, ptype in enumerate(place_type_order)}
print(place_type_to_code)
schedule_annotated["y"] = schedule_annotated["type"].map(place_type_to_code)

plt.figure(figsize=(8, 3))
plt.plot(schedule_annotated["time"], schedule_annotated["y"], marker="o", linestyle="-")
plt.yticks(range(len(place_type_order)), place_type_order)

plt.xlabel("Time (24 hour format)")
plt.ylabel("Location")
plt.title(f"Movement Schedule for Person {person_id}")
plt.grid(True)
plt.tight_layout()

plt.savefig(Path("analysis", f"person_{person_id}_movement.png"), dpi=300)
plt.show()


# grantt chart
plt.figure(figsize=(10, 3))

print(schedule_annotated.tail(1)[["start", "duration"]])

for _, row in schedule_annotated.iterrows():
    start = row["start"]
    duration = row["duration"]
    y_pos = place_type_to_code[row["type"]]
    plt.broken_barh([(start, duration)], (y_pos - 0.4, 0.8), facecolors="tab:blue")

plt.yticks(range(len(place_type_order)), place_type_order)

plt.xlim(0, 1460) #limit to one day
plt.gca().xaxis.set_major_locator(MultipleLocator(120))  # every 2 hours
plt.gca().xaxis.set_major_formatter(FuncFormatter(format_time))
plt.xticks(rotation=45)

plt.xlabel("Time (HH:MM format)")
plt.ylabel("Location")
plt.title(f"Movement Schedule for Person {person_id}")
plt.grid(True)
plt.tight_layout()

plt.savefig(Path("analysis", f"person_{person_id}_gantt.png"), dpi=300)
plt.show()
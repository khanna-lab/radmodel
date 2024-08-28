import csv
import random
import parameters as parameters

# Set a seed for reproducibility
random.seed(42)

# Step 1: Define places
places = []

# Add cells
for i in range(parameters.NUM_CELLS):
    places.append({"id": i, "name": f"cell_{i + 1}", "type": "cell"})

# Add activity rooms
for i in range(parameters.NUM_ACTIVITY_ROOMS):
    places.append({"id": parameters.NUM_CELLS + i, "name": f"activity_room_{i + 1}", "type": "activity_room"})

# Add cafeterias
for i in range(parameters.NUM_CAFETERIAS):
    places.append({"id": parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + i, "name": f"cafeteria_{i + 1}", "type": "cafeteria"})

# Add outdoor area
for i in range(parameters.NUM_OUTDOOR_AREAS):
    places.append({"id": parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + i, "name": f"outdoor_area_{i + 1}", "type": "outdoor_area"})

# Add medical facility
for i in range(parameters.NUM_MEDICAL_FACILITIES):
    places.append({"id": parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + parameters.NUM_OUTDOOR_AREAS + i, "name": f"medical_facility_{i + 1}", "type": "medical"})

# Add administrative offices
for i in range(parameters.NUM_ADMIN_OFFICES):
    places.append({"id": parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + parameters.NUM_OUTDOOR_AREAS + parameters.NUM_MEDICAL_FACILITIES + i, "name": f"admin_office_{i + 1}", "type": "administrative"})

# Write places.csv
with open("places.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "name", "type"])
    writer.writeheader()
    writer.writerows(places)

# Step 2: Define residents
residents = [{"id": i, "cell": random.randint(0, parameters.NUM_CELLS - 1), "schedule": i} for i in range(parameters.NUM_RESIDENTS)]

# Write residents.csv
with open("residents.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "cell", "schedule"])
    writer.writeheader()
    writer.writerows(residents)

# Step 3: Define schedules
schedules = []

# Define offsets for place types
activity_room_offset = parameters.NUM_CELLS
cafeteria_offset = parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS
outdoor_area_offset = cafeteria_offset + parameters.NUM_CAFETERIAS

# Generate schedules for each resident
for resident in residents:
    resident_id = resident["id"]
    cell_id = resident["cell"]

    # Define time intervals and location types using offsets
    schedule_times = [
        (0, cell_id),  # In cell
        (360, random.randint(activity_room_offset, activity_room_offset + parameters.NUM_ACTIVITY_ROOMS - 1)),  # Activity room
        (480, random.randint(cafeteria_offset, cafeteria_offset + parameters.NUM_CAFETERIAS - 1)),  # Cafeteria
        (720, random.randint(activity_room_offset, activity_room_offset + parameters.NUM_ACTIVITY_ROOMS - 1)),  # Activity room again
        (1020, outdoor_area_offset),  # Outdoor yard
        (1260, cell_id)  # Back to cell
    ]

    # Simplify by ensuring the resident stays in the same place until the next scheduled move
    previous_place = cell_id
    resident_schedule = []

    for time, place in schedule_times:
        if time > 0 and previous_place == place:
            continue  # Skip unnecessary transitions
        resident_schedule.append({"resident_id": resident_id, "start": time, "place": place, "risk": 1})
        previous_place = place

    schedules.extend(resident_schedule)

# Write schedule.csv
with open("schedule.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["resident_id", "start", "place", "risk"])
    writer.writeheader()
    writer.writerows(schedules)

print("CSV files generated: places.csv, residents.csv, schedule.csv")

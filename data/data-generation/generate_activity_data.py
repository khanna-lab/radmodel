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

# Add outdoor areas
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

# Define fixed schedule locations
for resident in residents:
    resident_id = resident["id"]
    cell_id = resident["cell"]

    # Fixed schedule with logical transitions
    schedule_times = [
        (0, cell_id),  # Morning in cell
        (360, parameters.NUM_CELLS + random.randint(0, parameters.NUM_ACTIVITY_ROOMS - 1)),  # Activity room
        (480, parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + random.randint(0, parameters.NUM_CAFETERIAS - 1)),  # Cafeteria
        (720, parameters.NUM_CELLS + random.randint(0, parameters.NUM_ACTIVITY_ROOMS - 1)),  # Activity room again
        (900, parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + parameters.NUM_OUTDOOR_AREAS + random.randint(0, parameters.NUM_ADMIN_OFFICES - 1)),  # Administrative office visit
        (1020, parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + random.randint(0, parameters.NUM_OUTDOOR_AREAS - 1)),  # Outdoor area
        (1140, parameters.NUM_CELLS + parameters.NUM_ACTIVITY_ROOMS + parameters.NUM_CAFETERIAS + parameters.NUM_OUTDOOR_AREAS + parameters.NUM_ADMIN_OFFICES + random.randint(0, parameters.NUM_MEDICAL_FACILITIES - 1)),  # Medical facility visit
        (1260, cell_id)  # Return to cell
    ]

    # Generate the schedule for this resident
    resident_schedule = [{"resident_id": resident_id, "start": time, "place": place, "risk": 1} for time, place in schedule_times]
    schedules.extend(resident_schedule)

# Write schedule.csv
with open("schedule.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["resident_id", "start", "place", "risk"])
    writer.writeheader()
    writer.writerows(schedules)

print("CSV files generated: places.csv, residents.csv, schedule.csv")

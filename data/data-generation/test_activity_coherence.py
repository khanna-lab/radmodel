import csv
import parameters  

def load_schedule(schedule_file):
    """Load the schedule data from CSV file."""
    with open(schedule_file, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def check_time_ordering(schedules):
    """Check that the activities for each resident are in chronological order."""
    # Group schedules by resident_id
    schedules_by_resident = {}
    for schedule in schedules:
        resident_id = int(schedule["resident_id"])
        if resident_id not in schedules_by_resident:
            schedules_by_resident[resident_id] = []
        schedules_by_resident[resident_id].append(schedule)

    # Check if activities are in chronological order
    for resident_id, resident_schedule in schedules_by_resident.items():
        times = [int(activity["start"]) for activity in resident_schedule]
        if times != sorted(times):
            print(f"Resident {resident_id}'s activities are not in chronological order.")
            return False

    return True

def check_no_overlap(schedules):
    """Check that there are no overlapping activities for each resident."""
    schedules_by_resident = {}
    for schedule in schedules:
        resident_id = int(schedule["resident_id"])
        if resident_id not in schedules_by_resident:
            schedules_by_resident[resident_id] = []
        schedules_by_resident[resident_id].append(schedule)

    for resident_id, resident_schedule in schedules_by_resident.items():
        end_times = []
        for i, activity in enumerate(resident_schedule[:-1]):
            start_time = int(activity["start"])
            next_start_time = int(resident_schedule[i + 1]["start"])
            if start_time + (next_start_time - start_time) > next_start_time:
                print(f"Resident {resident_id} has overlapping activities.")
                return False

    return True

def test_place_counts():
    expected_cells = parameters.NUM_CELLS
    expected_activity_rooms = parameters.NUM_ACTIVITY_ROOMS
    expected_cafeterias = parameters.NUM_CAFETERIAS
    expected_outdoor_areas = parameters.NUM_OUTDOOR_AREAS
    expected_medical_facilities = parameters.NUM_MEDICAL_FACILITIES
    expected_admin_offices = parameters.NUM_ADMIN_OFFICES

    # Count actual numbers in places.csv
    place_counts = {
        "cell": 0,
        "activity_room": 0,
        "cafeteria": 0,
        "outdoor_area": 0,
        "medical": 0,
        "administrative": 0
    }

    with open("places.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            place_counts[row["type"]] += 1

    # Test assertions
    assert place_counts["cell"] == expected_cells, f"Expected {expected_cells} cells, but found {place_counts['cell']}"
    assert place_counts["activity_room"] == expected_activity_rooms, f"Expected {expected_activity_rooms} activity rooms, but found {place_counts['activity_room']}"
    assert place_counts["cafeteria"] == expected_cafeterias, f"Expected {expected_cafeterias} cafeterias, but found {place_counts['cafeteria']}"
    assert place_counts["outdoor_area"] == expected_outdoor_areas, f"Expected {expected_outdoor_areas} outdoor areas, but found {place_counts['outdoor_area']}"
    assert place_counts["medical"] == expected_medical_facilities, f"Expected {expected_medical_facilities} medical facilities, but found {place_counts['medical']}"
    assert place_counts["administrative"] == expected_admin_offices, f"Expected {expected_admin_offices} administrative offices, but found {place_counts['administrative']}"

    print("All place counts are correct.")

def check_place_continuity(schedules):
    """Check that each resident's activities have a consistent place-to-place flow across cycles."""
    schedules_by_resident = {}

    for schedule in schedules:
        resident_id = int(schedule["resident_id"])
        if resident_id not in schedules_by_resident:
            schedules_by_resident[resident_id] = []
        schedules_by_resident[resident_id].append(schedule)

    for resident_id, resident_schedule in schedules_by_resident.items():
        # Ensure the schedule is sorted by start time
        resident_schedule.sort(key=lambda x: int(x["start"]))

        # Check transitions between each consecutive activity
        for i in range(len(resident_schedule) - 1):
            current_place = int(resident_schedule[i]["place"])
            next_place = int(resident_schedule[i + 1]["place"])
            current_start = int(resident_schedule[i]["start"])
            next_start = int(resident_schedule[i + 1]["start"])

            if next_start <= current_start:
                print(f"Resident {resident_id} has an inconsistent time transition: {current_start} -> {next_start}.")
                return False

        # Check the continuity between the last activity of the day and the first activity of the next day
        first_place = int(resident_schedule[0]["place"])
        last_place = int(resident_schedule[-1]["place"])
        last_start = int(resident_schedule[-1]["start"])

        if last_start == 1260 and int(resident_schedule[0]["start"]) == 0:
            if last_place != first_place:
                print(f"Resident {resident_id} has an inconsistent place transition from {last_place} at 1260 to {first_place} at time 0.")
                return False

    return True



def main():
    """Main function to run all coherence checks."""
    schedule_file = 'schedule.csv'
    schedules = load_schedule(schedule_file)
    
    # Call the test function
    test_place_counts()

    if not check_time_ordering(schedules):
        print("Schedule has time ordering issues.")
    elif not check_no_overlap(schedules):
        print("Schedule has overlapping activities.")
    elif not check_place_continuity(schedules):
        print("Schedule has place continuity issues.")
    else:
        print("Schedule passed all coherence checks.")

if __name__ == "__main__":
    main()

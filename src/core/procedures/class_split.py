from heapq import heappush, heappop

from irsdk import TrkLoc

from core.drivers import Driver
from util.generator_utils import positions_from_safety_car

def get_split_class_commands(drivers: list[Driver], pace_car_idx: int) -> list[str]:
    """ Provide the commands that need to be sent to make sure the cars behind the SC are sorted by their classes.

        Args:
            drivers: The list of Driver objects from the Drivers data model.
            pace_car_idx: The index of the pacecar in the drivers list.

        Returns:
            List[str]: The commands to send, in order, to split the classes.
    """
    # Get the car positions as seen from the SC
    car_positions = [driver["lap_distance"] for driver in drivers]
    pos_from_sc = positions_from_safety_car(car_positions, pace_car_idx)

    # Figure out what classes are driving, their est_lap_time to determine the
    # ordering and what drivers belong to each class
    classes = {}
    drivers_to_class = {}
    for idx, driver in enumerate(drivers):
        if driver["is_pace_car"]:
            continue
        if driver["track_loc"] == TrkLoc.not_in_world:
            continue

        class_info = classes.get(driver["car_class_id"], { "est_lap_time": 0.0, "drivers": set(), "drivers_ordered": [] })
        class_info["est_lap_time"] = driver["car_class_est_lap_time"]

        # Ignore cars that are currently in the pit for the sorting order
        if not driver["on_pit_road"]:
            class_info["drivers"].add(idx)

        # we are keeping a sorted list of drivers based on their position to be able to send EOL in order
        # Note that we do include anyone in the pit here since they could otherwise end up at the front of their class
        heappush(class_info["drivers_ordered"], (pos_from_sc[idx], idx))
        classes[driver["car_class_id"]] = class_info

        # Keep track of a driver -> class map to easily check if they are out of order
        drivers_to_class[idx] = driver["car_class_id"]

    # If there is only one class, skip
    if len(classes) == 1:
        return []

    # Sort by fastest lap time; this returns a list of (CarClassID, { ... }) tuples
    classes_sorted = sorted(classes.items(), key=lambda item: item[1]["est_lap_time"])

    # Check if we need to split the classes by checking for anyone out of order
    pos_and_idx = zip(pos_from_sc, list(range(len(pos_from_sc))))
    pos_and_idx_filtered = [entry for entry in pos_and_idx if entry[0] != -1]
    idx_all_sorted = [entry[1] for entry in sorted(pos_and_idx_filtered, key=lambda item: item[0])]

    class_pointer = 0
    pos_pointer = 0
    classes_out_of_order = set()
    drivers_out_of_order = set()
    # Go through the classes from fastest to slowest
    while class_pointer < len(classes_sorted):
        current_class = classes_sorted[class_pointer][0]
        current_class_drivers = classes_sorted[class_pointer][1]["drivers"]

        # remove any drivers we have already seen out of order
        for driver in drivers_out_of_order:
            current_class_drivers.discard(driver)
        # now go through our grid until we have seen all cars in this class
        while len(current_class_drivers) > 0:
            current_car = idx_all_sorted[pos_pointer]

            # Skip the SC, anyone on pit road, and disconnected drivers
            if current_car == pace_car_idx or drivers[current_car]["on_pit_road"] or drivers[current_car]["track_loc"] == TrkLoc.not_in_world:
                pos_pointer += 1
                continue

            # if a car is not in the current class, they are out of order
            if current_car not in current_class_drivers:
                classes_out_of_order.add(drivers_to_class[current_car])
                drivers_out_of_order.add(current_car)
            else:
                current_class_drivers.remove(current_car)

            pos_pointer += 1
        class_pointer += 1

    # No one is out of order!
    if len(classes_out_of_order) == 0:
        return []

    commands = []
    add_rest = False
    for c in classes_sorted:
        current_class = c[0]
        if add_rest or current_class in classes_out_of_order:
            # as soon as a class is out of order, then any slower classes also need to be send EOL commands
            add_rest = True
            drivers_ordered = c[1]["drivers_ordered"]
            while len(drivers_ordered) > 0:
                _, idx = heappop(drivers_ordered)
                car_number = drivers[idx]["car_number"]
                commands.append(f"!eol {car_number} Splitting classes")

    return commands

from copy import deepcopy
from typing import TypedDict, Optional
from irsdk import TrkLoc
import logging

logger = logging.getLogger(__name__)

class Driver(TypedDict):
    driver_idx: int
    laps_completed: int
    lap_distance: float
    track_loc: TrkLoc
    current_lap: int
    on_pit_road: bool
    car_class_id: int
    car_number: Optional[str]
    is_pace_car: bool

class Drivers:
    """The Drivers class is responsible for tracking the state of the drivers.
    
    The Drivers class is responsible for tracking the state of the drivers in
    the current session. It uses the iRacing API to gather the latest data
    about the drivers and stores it in a dictionary.
    """
    def __init__(self, master=None):
        """Initialize the Drivers class.
        
        Args:
            master (object): The master object that is responsible for the
                connection to the iRacing API.
        """
        self.master = master

        # Dictionaries to track the state of the drivers
        logger.debug("Creating drivers dictionaries")
        self.current_drivers: list[Driver] = []
        self.previous_drivers: list[Driver] = []

        # Do the initial update
        self.update()

    def update(self):
        """Update the current drivers with the latest data from the iRacing API.
        
        This method is called at the beginning of each loop to update the
        current drivers with the latest data from the iRacing API.
        
        Args:
            None
        """
        # Copy the current drivers to the previous drivers
        logger.debug("Copying current drivers to previous drivers")
        self.previous_drivers = deepcopy(self.current_drivers)

        # Clear the current drivers
        logger.debug("Clearing current drivers")
        self.current_drivers = []

        # Gather the updated driver data
        logger.debug("Gathering updated driver data")
        try:
            laps_completed = self.master.ir["CarIdxLapCompleted"]
            lap_distance = self.master.ir["CarIdxLapDistPct"]
            track_loc = self.master.ir["CarIdxTrackSurface"]
            current_lap = self.master.ir["CarIdxLap"]
            on_pit_road = self.master.ir["CarIdxOnPitRoad"]
            car_class = self.master.ir["CarIdxClass"]

            # Get driver info for car numbers and pace car identification
            driver_info = self.master.ir["DriverInfo"]["Drivers"]
        except Exception as e:
            # Handle cases where iRacing SDK data is not available (e.g., in tests)
            logger.warning(f"Failed to gather driver data: {e}")
            return  # Skip update if data is not available

        # Organize the updated driver data and update the current drivers
        logger.debug("Organizing updated driver data")
        for i in range(len(laps_completed)):
            # Find matching driver info for this car index
            car_number = None
            is_pace_car = False
            car_class_id = car_class[i] if i < len(car_class) else 0
            
            for driver in driver_info:
                if driver["CarIdx"] == i:
                    car_number = driver["CarNumber"]
                    is_pace_car = driver["CarIsPaceCar"] == 1
                    break

            self.current_drivers.append(
                {
                "driver_idx": i,
                "laps_completed": laps_completed[i],
                "lap_distance": lap_distance[i],
                "track_loc": track_loc[i],
                "current_lap": current_lap[i] if i < len(current_lap) else 0,
                "on_pit_road": on_pit_road[i] if i < len(on_pit_road) else False,
                "car_class_id": car_class_id,
                "car_number": car_number,
                "is_pace_car": is_pace_car,
                }
            )

    def get_driver_number(self, car_idx: int) -> Optional[str]:
        """Get the driver number from car index.
        
        Args:
            car_idx: The car index
            
        Returns:
            The driver number, or None if not found
        """
        for driver in self.current_drivers:
            if driver["driver_idx"] == car_idx:
                return driver["car_number"]
        return None

    def get_lead_lap_cars(self, target_lap: int = None) -> list[int]:
        """Get indices of cars on the lead lap or a specific lap.
        
        Args:
            target_lap: The lap number to filter for. If None, uses highest current lap.
            
        Returns:
            List of car indices on the target lap
        """
        if target_lap is None:
            # Find the highest lap number
            target_lap = max((driver["current_lap"] for driver in self.current_drivers), default=0)
        
        lead_lap_cars = []
        for driver in self.current_drivers:
            if driver["current_lap"] >= target_lap and not driver["on_pit_road"]:
                lead_lap_cars.append(driver["driver_idx"])
        
        return lead_lap_cars

    def get_cars_by_class(self) -> dict[int, list[int]]:
        """Get car indices organized by class ID.
        
        Returns:
            Dictionary mapping class IDs to lists of car indices
        """
        cars_by_class = {}
        for driver in self.current_drivers:
            if not driver["is_pace_car"]:  # Skip pace car
                class_id = driver["car_class_id"]
                if class_id not in cars_by_class:
                    cars_by_class[class_id] = []
                cars_by_class[class_id].append(driver["driver_idx"])
        
        return cars_by_class

    def get_class_ids(self) -> list[int]:
        """Get all unique class IDs (excluding pace car).
        
        Returns:
            List of unique class IDs
        """
        class_ids = []
        for driver in self.current_drivers:
            if not driver["is_pace_car"] and driver["car_class_id"] not in class_ids:
                class_ids.append(driver["car_class_id"])
        
        return class_ids

    def get_max_lap(self) -> int:
        """Get the maximum lap number across all cars.
        
        Returns:
            The highest lap number
        """
        return max((driver["current_lap"] for driver in self.current_drivers), default=0)

    def get_cars_not_on_pit_road(self) -> list[int]:
        """Get indices of cars not on pit road.
        
        Returns:
            List of car indices not on pit road
        """
        return [driver["driver_idx"] for driver in self.current_drivers 
                if not driver["on_pit_road"]]
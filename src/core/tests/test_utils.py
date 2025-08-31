"""Test utilities for mocking common objects across test files."""

from unittest.mock import Mock
from irsdk import TrkLoc
from configparser import ConfigParser


def create_mock_drivers(num_drivers=60, include_previous=True):
    """Create a mock Drivers object for testing.
    
    Args:
        num_drivers (int): Number of drivers to create. Defaults to 65.
        include_previous (bool): Whether to include previous_drivers list. Defaults to True.
    
    Returns:
        Mock: Mock Drivers object with current_drivers and optionally previous_drivers.
    """
    mock_drivers = Mock()
    mock_drivers.current_drivers = []
    
    for i in range(num_drivers):
        driver_data = {
            "driver_idx": i,
            "lap_distance": 0.5,
            "laps_completed": 1,
            "track_loc": TrkLoc.on_track,
            "current_lap": 1,
            "on_pit_road": False,
            "car_class_id": 1,
            "car_number": f"{i}",
            "is_pace_car": False,
        }
        mock_drivers.current_drivers.append(driver_data)
    
    if include_previous:
        mock_drivers.previous_drivers = []
        for i in range(num_drivers):
            driver_data = {
                "driver_idx": i,
                "lap_distance": 0.49,
                "laps_completed": 1,
                "track_loc": TrkLoc.on_track,
                "current_lap": 1,
                "on_pit_road": False,
                "car_class_id": 1,
                "car_number": f"{i}",
                "is_pace_car": False,
            }
            mock_drivers.previous_drivers.append(driver_data)
    
    # Add helper methods that the Drivers model provides
    def mock_get_driver_number(car_idx):
        for driver in mock_drivers.current_drivers:
            if driver["driver_idx"] == car_idx:
                return driver["car_number"]
        return None
    
    def mock_get_lead_lap_cars(target_lap=None):
        if target_lap is None:
            target_lap = max((driver["current_lap"] for driver in mock_drivers.current_drivers), default=0)
        return [driver["driver_idx"] for driver in mock_drivers.current_drivers 
                if driver["current_lap"] >= target_lap and not driver["on_pit_road"]]
    
    def mock_get_class_ids():
        return list(set(driver["car_class_id"] for driver in mock_drivers.current_drivers if not driver["is_pace_car"]))
    
    def mock_get_max_lap():
        return max((driver["current_lap"] for driver in mock_drivers.current_drivers), default=0)
        
    def mock_get_cars_not_on_pit_road():
        return [driver["driver_idx"] for driver in mock_drivers.current_drivers if not driver["on_pit_road"]]
    
    mock_drivers.get_driver_number = mock_get_driver_number
    mock_drivers.get_lead_lap_cars = mock_get_lead_lap_cars
    mock_drivers.get_class_ids = mock_get_class_ids
    mock_drivers.get_max_lap = mock_get_max_lap
    mock_drivers.get_cars_not_on_pit_road = mock_get_cars_not_on_pit_road
    
    return mock_drivers


class MockDrivers:
    def __init__(self, current = [], previous = []):
        self.current_drivers = current
        self.previous_drivers = previous

        # This is a fix to account for the SC entry in the drivers list
        # Ideally, we filter this out in the Drivers class so we don't have to account for this in all of our logic.
        self.current_drivers.append(make_driver(TrkLoc.not_in_world))
        self.previous_drivers.append(make_driver(TrkLoc.not_in_world))


def make_driver(track_loc, laps_completed = 0, lap_distance = 0.0, driver_idx = 0):
    return {
        "driver_idx": driver_idx,
        "track_loc": track_loc,
        "laps_completed": laps_completed,
        "lap_distance": lap_distance
    }


def dict_to_config(settings_dict):
    """Convert a dictionary to a ConfigParser object for testing."""
    config = ConfigParser()
    for section_name, section_data in settings_dict.items():
        config.add_section(section_name)
        for key, value in section_data.items():
            config.set(section_name, key, str(value))
    return config
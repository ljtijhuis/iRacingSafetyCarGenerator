import pytest

from core.procedures.class_split import get_split_class_commands
from core.tests.test_utils import make_driver

drivers = [
    make_driver(driver_idx=0, car_number="1", car_class_id=4016, car_class_est_lap_time=40.9251),
    make_driver(driver_idx=1, car_number="2", car_class_id=4016, car_class_est_lap_time=40.9251),
    make_driver(driver_idx=2, car_number="3", car_class_id=3002, car_class_est_lap_time=46.6068),
    make_driver(driver_idx=3, car_number="4", car_class_id=3002, car_class_est_lap_time=46.6068),
    make_driver(driver_idx=4, car_number="0", car_class_id=11, car_class_est_lap_time=39.8243, is_pace_car=True),
]

PACE_CAR_IDX = 4  # index of the pace car in the drivers list


split_class_test_data = [
    {
        # Test case: Cars are already in the right order
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [2.0, 1.9, 1.8, 1.7, 2.1],
            [False, False, False, False, False],
        )],
        "expected": [],
    },
    {
        # Two are swapped
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [2.0, 1.8, 1.9, 1.7, 2.1],
            [False, False, False, False, False],
        )],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
    {
        # Slower class is ahead
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [1.8, 1.7, 2.0, 1.9, 2.1],
            [False, False, False, False, False],
        )],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
    {
        # Faster class is pitting
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [2.0, 1.8, 1.9, 1.7, 2.1],
            [False, True, False, False, False],
        )],
        "expected": [],
    },
    {
        # Slower class is pitting
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [2.0, 1.8, 1.9, 1.7, 2.1],
            [False, False, True, False, False],
        )],
        "expected": [],
    },
    {
        # Car in the back is pitting
        "drivers": [d | {"lap_distance": ld, "on_pit_road": op} for d, ld, op in zip(
            drivers,
            [2.0, 1.8, 1.9, 1.7, 2.1],
            [False, False, False, True, False],
        )],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
]

@pytest.mark.parametrize("test_data", split_class_test_data)
def test_get_split_class_commands(test_data):
    commands = get_split_class_commands(test_data["drivers"], PACE_CAR_IDX)

    assert commands == test_data["expected"]


# Single-class test: only one racing class + pace car → early return []
single_class_drivers = [
    make_driver(driver_idx=0, car_number="1", car_class_id=4016, car_class_est_lap_time=40.9, lap_distance=2.0),
    make_driver(driver_idx=1, car_number="2", car_class_id=4016, car_class_est_lap_time=40.9, lap_distance=1.9),
    make_driver(driver_idx=2, car_number="0", car_class_id=11, car_class_est_lap_time=39.8, is_pace_car=True, lap_distance=2.1),
]

def test_single_class_returns_empty():
    commands = get_split_class_commands(single_class_drivers, 2)
    assert commands == []


# 3-class tests
three_class_drivers = [
    make_driver(driver_idx=0, car_number="10", car_class_id=100, car_class_est_lap_time=38.0),
    make_driver(driver_idx=1, car_number="11", car_class_id=100, car_class_est_lap_time=38.0),
    make_driver(driver_idx=2, car_number="20", car_class_id=200, car_class_est_lap_time=42.0),
    make_driver(driver_idx=3, car_number="21", car_class_id=200, car_class_est_lap_time=42.0),
    make_driver(driver_idx=4, car_number="30", car_class_id=300, car_class_est_lap_time=48.0),
    make_driver(driver_idx=5, car_number="31", car_class_id=300, car_class_est_lap_time=48.0),
    make_driver(driver_idx=6, car_number="0", car_class_id=11, car_class_est_lap_time=36.0, is_pace_car=True),
]

def test_three_classes_in_order():
    """Three classes already sorted correctly → no commands needed."""
    # Order behind SC: fast(10,11) → mid(20,21) → slow(30,31)
    test_drivers = [d | {"lap_distance": ld} for d, ld in zip(
        three_class_drivers,
        [2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 2.1],
    )]
    commands = get_split_class_commands(test_drivers, 6)
    assert commands == []


def test_three_classes_out_of_order():
    """Mid class mixed into fast class → EOL commands for mid and slow classes (cascade)."""
    # Order behind SC: fast(10) → mid(20) → fast(11) → mid(21) → slow(30,31)
    # Mid class (200) appears between fast class cars, so it's out of order.
    # The cascade (add_rest) then also includes the slow class (300).
    test_drivers = [d | {"lap_distance": ld} for d, ld in zip(
        three_class_drivers,
        [2.0, 1.8, 1.9, 1.7, 1.6, 1.5, 2.1],
    )]
    commands = get_split_class_commands(test_drivers, 6)
    # Mid class (200) and slow class (300) should both get EOL commands
    assert "!eol 20 Splitting classes" in commands
    assert "!eol 21 Splitting classes" in commands
    assert "!eol 30 Splitting classes" in commands
    assert "!eol 31 Splitting classes" in commands
    # Fast class should NOT get EOL
    assert "!eol 10 Splitting classes" not in commands
    assert "!eol 11 Splitting classes" not in commands

import pytest

from core.procedures.class_split import get_split_class_commands

drivers = [
    {
        "CarIdx": 0,
        "CarNumber": "1",
        "CarNumberRaw": 1,
        "CarClassID": 4016,
        "CarClassEstLapTime": 40.9251,
        "CarIsPaceCar": 0,
    },
    {
        "CarIdx": 1,
        "CarNumber": "2",
        "CarNumberRaw": 2,
        "CarClassID": 4016,
        "CarClassEstLapTime": 40.9251,
        "CarIsPaceCar": 0,
    },
    {
        "CarIdx": 2,
        "CarNumber": "3",
        "CarNumberRaw": 3,
        "CarClassID": 3002,
        "CarClassEstLapTime": 46.6068,
        "CarIsPaceCar": 0,
    },
    {
        "CarIdx": 3,
        "CarNumber": "4",
        "CarNumberRaw": 4,
        "CarClassID": 3002,
        "CarClassEstLapTime": 46.6068,
        "CarIsPaceCar": 0,
    },
    {
        "CarIdx": 4,
        "CarNumber": "0",
        "CarNumberRaw": 0,
        "CarClassID": 11,
        "CarClassEstLapTime": 39.8243,
        "CarIsPaceCar": 1,
    },
]


split_class_test_data = [
    {
        # Test case: Cars are already in the right order
        "drivers": drivers,
        "car_positions": [2.0, 1.9, 1.8, 1.7, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, False, False, False, False, False, False, False, False],
        "expected": [],
    },
    {
        # Two are swapped
        "drivers": drivers,
        "car_positions": [2.0, 1.8, 1.9, 1.7, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, False, False, False, False, False, False, False, False],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
    {
        # Slower class is ahead
        "drivers": drivers,
        "car_positions": [1.8, 1.7, 2.0, 1.9, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, False, False, False, False, False, False, False, False],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
    {
        # Faster class is pitting
        "drivers": drivers,
        "car_positions": [2.0, 1.8, 1.9, 1.7, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, True, False, False, False, False, False, False, False],
        "expected": [],
    },
    {
        # Slower class is pitting
        "drivers": drivers,
        "car_positions": [2.0, 1.8, 1.9, 1.7, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, False, True, False, False, False, False, False, False],
        "expected": [],
    },
    {
        # Car in the back is pitting
        "drivers": drivers,
        "car_positions": [2.0, 1.8, 1.9, 1.7, 2.1, -1, -1, -1, -1],
        "on_pit_road": [False, False, False, True, False, False, False, False, False],
        "expected": ["!eol 3 Splitting classes", "!eol 4 Splitting classes"],
    },
]

@pytest.mark.parametrize("test_data", split_class_test_data)
def test_get_split_class_commands(test_data):
    commands = get_split_class_commands(test_data["drivers"], test_data["car_positions"], test_data["on_pit_road"], 4) # 4 = the position of the pace car in our test data

    assert commands == test_data["expected"]


# Single-class test: only one racing class + pace car → early return []
single_class_drivers = [
    {"CarIdx": 0, "CarNumber": "1", "CarClassID": 4016, "CarClassEstLapTime": 40.9, "CarIsPaceCar": 0},
    {"CarIdx": 1, "CarNumber": "2", "CarClassID": 4016, "CarClassEstLapTime": 40.9, "CarIsPaceCar": 0},
    {"CarIdx": 2, "CarNumber": "0", "CarClassID": 11, "CarClassEstLapTime": 39.8, "CarIsPaceCar": 1},
]

def test_single_class_returns_empty():
    commands = get_split_class_commands(
        single_class_drivers,
        [2.0, 1.9, 2.1, -1, -1],
        [False, False, False, False, False],
        2,
    )
    assert commands == []


# 3-class tests
three_class_drivers = [
    {"CarIdx": 0, "CarNumber": "10", "CarClassID": 100, "CarClassEstLapTime": 38.0, "CarIsPaceCar": 0},
    {"CarIdx": 1, "CarNumber": "11", "CarClassID": 100, "CarClassEstLapTime": 38.0, "CarIsPaceCar": 0},
    {"CarIdx": 2, "CarNumber": "20", "CarClassID": 200, "CarClassEstLapTime": 42.0, "CarIsPaceCar": 0},
    {"CarIdx": 3, "CarNumber": "21", "CarClassID": 200, "CarClassEstLapTime": 42.0, "CarIsPaceCar": 0},
    {"CarIdx": 4, "CarNumber": "30", "CarClassID": 300, "CarClassEstLapTime": 48.0, "CarIsPaceCar": 0},
    {"CarIdx": 5, "CarNumber": "31", "CarClassID": 300, "CarClassEstLapTime": 48.0, "CarIsPaceCar": 0},
    {"CarIdx": 6, "CarNumber": "0", "CarClassID": 11, "CarClassEstLapTime": 36.0, "CarIsPaceCar": 1},
]

def test_three_classes_in_order():
    """Three classes already sorted correctly → no commands needed."""
    # Order behind SC: fast(10,11) → mid(20,21) → slow(30,31)
    commands = get_split_class_commands(
        three_class_drivers,
        [2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 2.1, -1],
        [False, False, False, False, False, False, False, False],
        6,
    )
    assert commands == []


def test_three_classes_out_of_order():
    """Mid class mixed into fast class → EOL commands for mid and slow classes (cascade)."""
    # Order behind SC: fast(10) → mid(20) → fast(11) → mid(21) → slow(30,31)
    # Mid class (200) appears between fast class cars, so it's out of order.
    # The cascade (add_rest) then also includes the slow class (300).
    commands = get_split_class_commands(
        three_class_drivers,
        [2.0, 1.8, 1.9, 1.7, 1.6, 1.5, 2.1, -1],
        [False, False, False, False, False, False, False, False],
        6,
    )
    # Mid class (200) and slow class (300) should both get EOL commands
    assert "!eol 20 Splitting classes" in commands
    assert "!eol 21 Splitting classes" in commands
    assert "!eol 30 Splitting classes" in commands
    assert "!eol 31 Splitting classes" in commands
    # Fast class should NOT get EOL
    assert "!eol 10 Splitting classes" not in commands
    assert "!eol 11 Splitting classes" not in commands

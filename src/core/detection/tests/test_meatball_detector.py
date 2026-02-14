import irsdk
from irsdk import TrkLoc

from core.detection.detector_common_types import DetectorEventTypes, DetectorState
from core.detection.meatball_detector import MeatballDetector
from core.tests.test_utils import MockDrivers, make_driver

REPAIR_FLAG = irsdk.Flags.repair
SERVICIBLE_FLAG = irsdk.Flags.servicible
MEATBALL_AND_SERVICIBLE = REPAIR_FLAG | SERVICIBLE_FLAG


def test_detect_cars_with_repair_flag():
    drivers = MockDrivers([
        make_driver(driver_idx=0, car_number="10", session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(driver_idx=1, car_number="20", session_flags=SERVICIBLE_FLAG),
        make_driver(driver_idx=2, car_number="30", session_flags=MEATBALL_AND_SERVICIBLE),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert result.event_type == DetectorEventTypes.MEATBALL
    assert result.has_drivers()
    assert len(result.drivers) == 2
    assert result.drivers[0]["driver_idx"] == 0
    assert result.drivers[1]["driver_idx"] == 2


def test_ignores_pace_car():
    drivers = MockDrivers([
        make_driver(driver_idx=0, is_pace_car=True, session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(driver_idx=1, session_flags=MEATBALL_AND_SERVICIBLE),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_ignores_negative_laps_completed():
    drivers = MockDrivers([
        make_driver(driver_idx=0, laps_completed=-1, session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(driver_idx=1, laps_completed=0, session_flags=MEATBALL_AND_SERVICIBLE),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_no_meatball_flags():
    drivers = MockDrivers([
        make_driver(driver_idx=0, session_flags=SERVICIBLE_FLAG),
        make_driver(driver_idx=1, session_flags=0),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert result.has_drivers()
    assert result.drivers == []


def test_ignores_not_in_world():
    """Cars towed out of the world (track_loc=NotInWorld) should be excluded,
    even if they have the meatball flag. This matches the pattern used in
    wave_arounds.py and stopped_detector.py."""
    drivers = MockDrivers([
        make_driver(driver_idx=0, track_loc=TrkLoc.not_in_world, laps_completed=-1,
                    session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(driver_idx=1, track_loc=TrkLoc.on_track, laps_completed=0,
                    session_flags=MEATBALL_AND_SERVICIBLE),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_detects_meatball_in_pit_stall():
    """Cars in pit stall with meatball flag should still be detected,
    since the meatball is a car condition (needs repairs) not a position condition."""
    drivers = MockDrivers([
        make_driver(driver_idx=0, track_loc=TrkLoc.in_pit_stall, laps_completed=0,
                    on_pit_road=True, session_flags=MEATBALL_AND_SERVICIBLE),
    ])
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 0


def test_should_run_always_returns_true():
    """MeatballDetector.should_run() always returns True; enabled/disabled
    is handled by DetectorSettings and build_detector()."""
    drivers = MockDrivers([])
    detector = MeatballDetector(drivers)

    states = [
        DetectorState(0, {}),
        DetectorState(1000, {DetectorEventTypes.MEATBALL: 5}),
    ]
    for state in states:
        assert detector.should_run(state) is True

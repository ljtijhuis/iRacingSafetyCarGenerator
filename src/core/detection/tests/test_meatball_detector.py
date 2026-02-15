import irsdk
from irsdk import TrkLoc

from core.detection.detector_common_types import DetectorEventTypes, DetectorState
from core.detection.meatball_detector import MeatballDetector
from core.tests.test_utils import MockDrivers, make_driver

REPAIR_FLAG = irsdk.Flags.repair
SERVICIBLE_FLAG = irsdk.Flags.servicible
MEATBALL_AND_SERVICIBLE = REPAIR_FLAG | SERVICIBLE_FLAG


def test_detect_transition_to_repair_flag():
    """Detects cars where repair flag just appeared (transition from no-repair to repair)."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, car_number="10", session_flags=MEATBALL_AND_SERVICIBLE),
            make_driver(driver_idx=1, car_number="20", session_flags=SERVICIBLE_FLAG),
            make_driver(driver_idx=2, car_number="30", session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, car_number="10", session_flags=0),
            make_driver(driver_idx=1, car_number="20", session_flags=0),
            make_driver(driver_idx=2, car_number="30", session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert result.event_type == DetectorEventTypes.MEATBALL
    assert result.has_drivers()
    assert len(result.drivers) == 2
    assert result.drivers[0]["driver_idx"] == 0
    assert result.drivers[1]["driver_idx"] == 2


def test_no_transition_when_already_had_repair():
    """No detection when repair flag was already set in previous frame."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, car_number="10", session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, car_number="10", session_flags=MEATBALL_AND_SERVICIBLE),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 0


def test_no_transition_repair_flag_removed():
    """No detection when repair flag is removed (previous had it, current doesn't)."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, car_number="10", session_flags=SERVICIBLE_FLAG),
        ],
        previous=[
            make_driver(driver_idx=0, car_number="10", session_flags=MEATBALL_AND_SERVICIBLE),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 0


def test_ignores_pace_car():
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, is_pace_car=True, session_flags=MEATBALL_AND_SERVICIBLE),
            make_driver(driver_idx=1, session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, is_pace_car=True, session_flags=0),
            make_driver(driver_idx=1, session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_ignores_negative_laps_completed():
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, laps_completed=-1, session_flags=MEATBALL_AND_SERVICIBLE),
            make_driver(driver_idx=1, laps_completed=0, session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, laps_completed=-1, session_flags=0),
            make_driver(driver_idx=1, laps_completed=0, session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_no_meatball_flags():
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, session_flags=SERVICIBLE_FLAG),
            make_driver(driver_idx=1, session_flags=0),
        ],
        previous=[
            make_driver(driver_idx=0, session_flags=0),
            make_driver(driver_idx=1, session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert result.has_drivers()
    assert result.drivers == []


def test_ignores_not_in_world():
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, track_loc=TrkLoc.not_in_world, laps_completed=-1,
                        session_flags=MEATBALL_AND_SERVICIBLE),
            make_driver(driver_idx=1, track_loc=TrkLoc.on_track, laps_completed=0,
                        session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, track_loc=TrkLoc.not_in_world, laps_completed=-1,
                        session_flags=0),
            make_driver(driver_idx=1, track_loc=TrkLoc.on_track, laps_completed=0,
                        session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["driver_idx"] == 1


def test_uses_current_position_when_on_track():
    """Car on track at 0.7 gets meatball → event at 0.7."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.7,
                        session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.69,
                        session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["lap_distance"] == 0.7


def test_uses_last_non_pit_position_when_in_pit():
    """Car was on-track at 0.5, tows to pit (position 0.15), gets meatball in pit → event at 0.5."""
    # First call: car is on track at 0.5, no meatball yet
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.5,
                        session_flags=0),
        ],
        previous=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.49,
                        session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    detector.detect()  # builds up _last_non_pit_position

    # Second call: car is now in pit stall at 0.15 and just got meatball
    drivers.current_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.in_pit_stall, lap_distance=0.15,
                    on_pit_road=True, session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(TrkLoc.not_in_world),  # SC placeholder
    ]
    drivers.previous_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.in_pit_stall, lap_distance=0.15,
                    on_pit_road=True, session_flags=0),
        make_driver(TrkLoc.not_in_world),
    ]
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["lap_distance"] == 0.5


def test_uses_off_track_position():
    """Car goes off-track at 0.4, then gets meatball → event at 0.4."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, track_loc=TrkLoc.off_track, lap_distance=0.4,
                        session_flags=MEATBALL_AND_SERVICIBLE),
        ],
        previous=[
            make_driver(driver_idx=0, track_loc=TrkLoc.off_track, lap_distance=0.4,
                        session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["lap_distance"] == 0.4


def test_position_tracking_persists_across_calls():
    """_last_non_pit_position persists across multiple detect() calls."""
    drivers = MockDrivers(
        current=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.3,
                        session_flags=0),
        ],
        previous=[
            make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.29,
                        session_flags=0),
        ],
    )
    detector = MeatballDetector(drivers)
    detector.detect()

    # Update position
    drivers.current_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.6,
                    session_flags=0),
        make_driver(TrkLoc.not_in_world),
    ]
    drivers.previous_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.on_track, lap_distance=0.3,
                    session_flags=0),
        make_driver(TrkLoc.not_in_world),
    ]
    detector.detect()

    # Now tow to pit and get meatball
    drivers.current_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.in_pit_stall, lap_distance=0.15,
                    on_pit_road=True, session_flags=MEATBALL_AND_SERVICIBLE),
        make_driver(TrkLoc.not_in_world),
    ]
    drivers.previous_drivers = [
        make_driver(driver_idx=0, track_loc=TrkLoc.in_pit_stall, lap_distance=0.15,
                    on_pit_road=True, session_flags=0),
        make_driver(TrkLoc.not_in_world),
    ]
    result = detector.detect()

    assert len(result.drivers) == 1
    assert result.drivers[0]["lap_distance"] == 0.6  # last on-track position


def test_should_run_always_returns_true():
    """MeatballDetector.should_run() always returns True; enabled/disabled
    is handled by DetectorSettings and build_detector()."""
    drivers = MockDrivers([], [])
    detector = MeatballDetector(drivers)

    states = [
        DetectorState(0, {}),
        DetectorState(1000, {DetectorEventTypes.MEATBALL: 5}),
    ]
    for state in states:
        assert detector.should_run(state) is True

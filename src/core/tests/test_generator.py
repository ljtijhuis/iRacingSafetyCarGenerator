import pytest
import irsdk

from unittest.mock import MagicMock, Mock, patch
from core.detection.threshold_checker import ThresholdChecker
from core.detection.detector import Detector, DetectorSettings
from core.generator import Generator, GeneratorState
from core.interactions.command_sender import CommandSender
from core.interactions.mock_sender import MockSender
from core.tests.test_utils import create_mock_drivers

@pytest.fixture
def generator():
    mock_arguments = Mock()
    mock_arguments.disable_window_interactions = True
    mock_master = Mock()

    # Create a mock settings object that behaves like our Settings wrapper
    mock_settings = Mock()
    # Set default values for all properties used in tests
    mock_settings.race_start_threshold_multiplier = 1.5
    mock_settings.race_start_threshold_multiplier_time_seconds = 300.0
    mock_settings.proximity_filter_enabled = False
    mock_settings.proximity_filter_distance_percentage = 0.05
    mock_settings.detection_start_minute = 0.0
    mock_settings.detection_end_minute = 999.0
    mock_settings.max_safety_cars = 999
    mock_settings.min_time_between_safety_cars_minutes = 0.0
    mock_settings.off_track_cars_threshold = 4
    mock_settings.stopped_cars_threshold = 2
    mock_settings.event_time_window_seconds = 5.0
    mock_settings.accumulative_threshold = 7.0
    mock_settings.stopped_weight = 1.0
    mock_settings.off_track_weight = 1.0
    mock_settings.random_detector_enabled = False
    mock_settings.random_probability = 0.5
    mock_settings.random_max_safety_cars = 1
    mock_settings.stopped_detector_enabled = True
    mock_settings.off_track_detector_enabled = True
    mock_master.settings = mock_settings
    gen = Generator(arguments=mock_arguments, master=mock_master)
    gen.start_time = 0  # Simulate the start time as 0 for testing

    # Setup mock drivers
    mock_drivers = create_mock_drivers()
    gen.drivers = mock_drivers

    # Setup detector
    detector_settings = DetectorSettings.from_settings(mock_master.settings)
    gen.detector = Detector.build_detector(detector_settings, mock_drivers)

    return gen

def test_command_sender_init():
    """Test the initialization of the CommandSender."""
    mock_arguments = Mock()
    # This needs to be True to make tests work on MacOS
    mock_arguments.disable_window_interactions = True

    # We need the generator to send actual commands
    mock_arguments.dry_run = False
    generator = Generator(arguments=mock_arguments)
    assert isinstance(generator.command_sender, CommandSender)

    # In this case, we want to avoid sending commands
    mock_arguments.dry_run = True
    generator = Generator(arguments=mock_arguments)
    assert isinstance(generator.command_sender, MockSender)


def test_notify_race_started_calls_both_components(generator):
    """Test that _notify_race_started calls race_started on both detector and threshold_checker"""

    # Create mock detector and threshold_checker
    generator.detector = Mock(spec=Detector)
    generator.threshold_checker = Mock(spec=ThresholdChecker)

    start_time = 1000.0
    generator._notify_race_started(start_time)

    # Verify both components were called
    generator.detector.race_started.assert_called_once_with(start_time)
    generator.threshold_checker.race_started.assert_called_once_with(start_time)

def test_send_wave_arounds_disabled(generator):
    """Test when wave arounds are disabled."""
    generator.master.settings.wave_arounds_enabled = False
    generator.master.settings.laps_before_wave_arounds = 2
    result = generator._send_wave_arounds()
    assert result is True

def test_send_wave_arounds_not_time_yet(generator):
    """Test when it's not time for wave arounds."""
    generator.master.settings.wave_arounds_enabled = True
    generator.master.settings.laps_before_wave_arounds = 2
    generator.lap_at_sc = 5
    generator.current_lap_under_sc = 6  # Not yet at wave lap
    result = generator._send_wave_arounds()
    assert result is False

def test_send_wave_arounds_wave_ahead_of_class_lead(mocker, generator):
    """Test wave arounds for cars ahead of class lead."""
    generator.master.settings.wave_arounds_enabled = True
    generator.master.settings.laps_before_wave_arounds = 1
    generator.master.settings.wave_around_rules_index = 1  # Wave ahead of class lead
    generator.lap_at_sc = 5
    generator.current_lap_under_sc = 7
    generator.ir = MagicMock()

    # Mock drivers with session_info
    generator.drivers.current_drivers = []
    generator.drivers.session_info = {"pace_car_idx": 0}

    mock_wave_around_func = mocker.patch("core.generator.wave_arounds_factory", return_value=lambda *args: ["!w 1", "!w 2"])
    mock_command_sender = mocker.patch.object(generator.command_sender, "send_commands")

    result = generator._send_wave_arounds()

    # Assert waves were actually sent
    mock_wave_around_func.assert_called_once()
    mock_command_sender.assert_called_once_with(["!w 1", "!w 2"])
    assert result is True

def test_send_wave_arounds_no_eligible_cars(generator, mocker):
    """Test wave arounds when no cars are eligible."""
    generator.master.settings.wave_arounds_enabled = True
    generator.master.settings.laps_before_wave_arounds = 1
    generator.master.settings.wave_around_rules_index = 1  # Wave ahead of class lead
    generator.lap_at_sc = 5
    generator.current_lap_under_sc = 7  # At wave lap

    # Mock drivers with session_info
    generator.drivers.current_drivers = []
    generator.drivers.session_info = {"pace_car_idx": 0}

    mock_wave_around_func = mocker.patch("core.generator.wave_arounds_factory", return_value=lambda *args: [])
    mock_command_sender = mocker.patch.object(generator.command_sender, "send_commands")

    generator.ir = MagicMock()

    result = generator._send_wave_arounds()
    mock_command_sender.assert_called_once_with([])
    assert result is True


class TestWaitForGreenFlag:
    """Tests for _wait_for_green_flag() method."""

    @pytest.fixture
    def generator_for_green_flag(self):
        """Create a generator configured for green flag tests."""
        mock_arguments = Mock()
        mock_arguments.disable_window_interactions = True
        mock_master = Mock()
        mock_master.generator_state = GeneratorState.CONNECTED

        mock_settings = Mock()
        mock_master.settings = mock_settings

        gen = Generator(arguments=mock_arguments, master=mock_master)
        gen.start_time = None

        # Mock the iRacing SDK
        gen.ir = MagicMock()
        gen.ir.__getitem__ = MagicMock()

        # Mock detector and threshold_checker for _notify_race_started
        gen.detector = Mock()
        gen.threshold_checker = Mock()

        return gen

    def test_green_flag_detected(self, generator_for_green_flag):
        """Test that green flag detection works (existing behavior)."""
        gen = generator_for_green_flag

        # Setup: Race session, green flag is set
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": irsdk.Flags.green,
            "SessionState": irsdk.SessionState.racing,
        }.get(key)

        gen._wait_for_green_flag(require_race_session=True)

        assert gen.start_time is not None
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_race_already_in_progress_with_require_race_session_true(self, generator_for_green_flag):
        """Test that SessionState==racing is detected when require_race_session=True."""
        gen = generator_for_green_flag

        # Setup: Race session, NO green flag, but SessionState is racing
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": 0,  # No flags set (green flag already cleared)
            "SessionState": irsdk.SessionState.racing,
        }.get(key)

        gen._wait_for_green_flag(require_race_session=True)

        assert gen.start_time is not None
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_race_already_in_progress_ignored_with_require_race_session_false(self, generator_for_green_flag):
        """Test that SessionState==racing is ignored when require_race_session=False (SC restart)."""
        gen = generator_for_green_flag
        call_count = 0

        def mock_getitem(key):
            nonlocal call_count
            call_count += 1
            # First few calls return no green flag, then return green flag
            # This simulates waiting for actual green flag during SC restart
            if key == "SessionFlags":
                if call_count <= 3:
                    return 0  # No flags
                else:
                    return irsdk.Flags.green  # Green flag on 4th+ call
            return {
                "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
                "SessionNum": 0,
                "SessionState": irsdk.SessionState.racing,
            }.get(key)

        gen.ir.__getitem__.side_effect = mock_getitem

        gen._wait_for_green_flag(require_race_session=False)

        # Should have waited for actual green flag, not just SessionState
        assert call_count >= 4
        assert gen.start_time is not None
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_waits_for_race_session_before_checking_green(self, generator_for_green_flag):
        """Test that it waits for race session before checking green flag."""
        gen = generator_for_green_flag
        session_checks = []

        def mock_getitem(key):
            if key == "SessionNum":
                session_checks.append(len(session_checks))
                # Return practice for first call, then race
                if len(session_checks) <= 1:
                    return 0  # Practice session
                return 1  # Race session
            if key == "SessionInfo":
                return {"Sessions": [
                    {"SessionName": "PRACTICE"},
                    {"SessionName": "RACE"}
                ]}
            if key == "SessionFlags":
                return irsdk.Flags.green
            if key == "SessionState":
                return irsdk.SessionState.racing
            return None

        gen.ir.__getitem__.side_effect = mock_getitem

        gen._wait_for_green_flag(require_race_session=True)

        # Should have checked session at least twice (once for practice, once for race)
        assert len(session_checks) >= 2
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_shutdown_event_exits_early(self, generator_for_green_flag):
        """Test that shutdown event causes early exit."""
        gen = generator_for_green_flag

        # Setup: Race session, no green flag, not racing
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": 0,
            "SessionState": irsdk.SessionState.parade_laps,
        }.get(key)

        # Set shutdown event
        gen.shutdown_event.set()

        gen._wait_for_green_flag(require_race_session=True)

        # Should have exited and set start_time
        assert gen.start_time is not None
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_skip_wait_event_exits_early(self, generator_for_green_flag):
        """Test that skip_wait_for_green_event causes early exit."""
        gen = generator_for_green_flag

        # Setup: Race session, no green flag, not racing
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": 0,
            "SessionState": irsdk.SessionState.parade_laps,
        }.get(key)

        # Set skip event
        gen.skip_wait_for_green_event.set()

        gen._wait_for_green_flag(require_race_session=True)

        # Should have exited and set start_time
        assert gen.start_time is not None
        assert gen.master.generator_state == GeneratorState.MONITORING_FOR_INCIDENTS

    def test_green_flag_preferred_over_session_state(self, generator_for_green_flag, caplog):
        """Test that green flag is logged when both conditions are true."""
        gen = generator_for_green_flag

        # Setup: Both green flag AND racing state
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": irsdk.Flags.green,
            "SessionState": irsdk.SessionState.racing,
        }.get(key)

        import logging
        with caplog.at_level(logging.INFO):
            gen._wait_for_green_flag(require_race_session=True)

        # Green flag message should appear (checked first)
        assert "Green flag detected" in caplog.text
        assert "Race already in progress" not in caplog.text

    def test_race_in_progress_logging(self, generator_for_green_flag, caplog):
        """Test that race already in progress is logged correctly."""
        gen = generator_for_green_flag

        # Setup: No green flag, but racing state
        gen.ir.__getitem__.side_effect = lambda key: {
            "SessionInfo": {"Sessions": [{"SessionName": "RACE"}]},
            "SessionNum": 0,
            "SessionFlags": 0,
            "SessionState": irsdk.SessionState.racing,
        }.get(key)

        import logging
        with caplog.at_level(logging.INFO):
            gen._wait_for_green_flag(require_race_session=True)

        assert "Race already in progress" in caplog.text

"""
Example test demonstrating iRSDK recording playback functionality.

This test shows how to use recorded iRSDK dumps to simulate a real iRacing session
in tests without requiring a live connection to iRacing.
"""

import pytest
from unittest.mock import Mock
from core.recording.playback import IRSDKPlayback, MockIRSDK
from core.drivers import Drivers


class TestRecordingPlayback:
    """Example tests using recorded iRSDK data playback."""

    def test_playback_iteration(self):
        """
        Test iterating through recorded dumps.

        This example assumes you have a folder 'logs/dump_20240101_120000' with
        numbered dump files created by the recorder.
        """
        # NOTE: This test will be skipped if the dump folder doesn't exist
        # To use this test, record some data using the "Start Recording iRSDK" button
        # in the dev mode UI, then update the path below

        dump_folder = "logs/dump_example"  # Replace with actual dump folder

        # Skip test if folder doesn't exist (for CI/CD)
        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found. Record data first.")

        # Create playback object
        playback = IRSDKPlayback(dump_folder)

        # Verify we have dumps to play
        assert playback.total_dumps > 0, "Should have at least one dump"

        # Iterate through all dumps
        dump_count = 0
        for dump in playback:
            # Each dump should have the standard iRSDK fields
            assert "SessionNum" in dump
            assert "DriverInfo" in dump
            assert "CarIdxLap" in dump
            assert "CarIdxLapDistPct" in dump
            assert "dump_number" in dump
            assert "timestamp" in dump

            dump_count += 1

        # Verify we processed all dumps
        assert dump_count == playback.total_dumps

    def test_playback_with_mock_irsdk(self):
        """
        Test using MockIRSDK to simulate iRacing connection with playback data.

        This shows how to test components that depend on iRSDK without
        requiring a live iRacing connection.
        """
        # NOTE: This test will be skipped if the dump folder doesn't exist
        dump_folder = "logs/dump_example"  # Replace with actual dump folder

        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found. Record data first.")

        # Create playback and mock iRSDK
        playback = IRSDKPlayback(dump_folder)
        mock_ir = MockIRSDK(playback)

        # Simulate startup
        assert mock_ir.startup() is True

        # Access data just like real iRSDK
        session_num = mock_ir["SessionNum"]
        driver_info = mock_ir["DriverInfo"]
        car_laps = mock_ir["CarIdxLap"]

        # Verify we got valid data
        assert session_num is not None
        assert driver_info is not None
        assert car_laps is not None
        assert len(car_laps) > 0

        # Advance to next dump
        assert mock_ir.advance() is True

        # Data should be from the second dump now
        second_dump_session = mock_ir["SessionNum"]
        assert second_dump_session is not None

        # Simulate shutdown
        mock_ir.shutdown()

    def test_playback_with_drivers_object(self):
        """
        Test using recorded dumps with the Drivers class.

        This demonstrates how to test the Drivers class using playback data
        to simulate real driver state changes over time.
        """
        # NOTE: This test will be skipped if the dump folder doesn't exist
        dump_folder = "logs/dump_example"  # Replace with actual dump folder

        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found. Record data first.")

        # Create playback and mock iRSDK
        playback = IRSDKPlayback(dump_folder)
        mock_ir = MockIRSDK(playback)
        mock_ir.startup()

        # Create a mock generator with our mock iRSDK
        mock_generator = Mock()
        mock_generator.ir = mock_ir

        # Create Drivers object using our mock
        drivers = Drivers(mock_generator)

        # Initialize drivers with first dump
        drivers.update()

        # Verify we have drivers
        assert len(drivers.current) > 0, "Should have at least one driver"

        # Save first state
        first_driver = drivers.current[0]
        first_lap = first_driver["laps_completed"]

        # Advance to next dump and update
        if mock_ir.advance():
            drivers.update()

            # Verify drivers updated
            second_driver = drivers.current[0]
            second_lap = second_driver["laps_completed"]

            # Laps should be same or increased (depending on recording)
            assert second_lap >= first_lap

    def test_playback_specific_dump(self):
        """
        Test accessing a specific dump by index.

        This is useful for testing specific scenarios or edge cases
        captured during recording.
        """
        # NOTE: This test will be skipped if the dump folder doesn't exist
        dump_folder = "logs/dump_example"  # Replace with actual dump folder

        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found. Record data first.")

        # Create playback object
        playback = IRSDKPlayback(dump_folder)

        # Get the first dump
        first_dump = playback.get_dump(0)
        assert first_dump["dump_number"] == 0

        # Get the last dump
        if playback.total_dumps > 1:
            last_dump = playback.get_dump(playback.total_dumps - 1)
            assert last_dump["dump_number"] == playback.total_dumps - 1

        # Test invalid index
        with pytest.raises(IndexError):
            playback.get_dump(99999)

    def test_playback_reset(self):
        """
        Test resetting playback to the beginning.

        This allows re-running the same recorded session multiple times
        in different test scenarios.
        """
        # NOTE: This test will be skipped if the dump folder doesn't exist
        dump_folder = "logs/dump_example"  # Replace with actual dump folder

        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found. Record data first.")

        # Create playback object
        playback = IRSDKPlayback(dump_folder)

        # Consume some dumps
        next(playback)
        if playback.total_dumps > 1:
            next(playback)

        # Position should have advanced
        assert playback.current_position > 0

        # Reset playback
        playback.reset()

        # Position should be back at start
        assert playback.current_position == 0

        # Can iterate again
        first_dump = next(playback)
        assert first_dump["dump_number"] == 0


class TestRecordingPlaybackWithDetectors:
    """
    Example of using playback to test detector components.

    These tests demonstrate how to use recorded data to test
    the safety car detection system with real-world scenarios.
    """

    def test_detector_with_playback(self):
        """
        Test running detectors on recorded data.

        This shows how to replay a recorded session and run the
        detection system on it to verify behavior.
        """
        # NOTE: This is a conceptual example
        # In practice, you'd need a recording with specific events
        dump_folder = "logs/dump_with_off_track_incident"  # Example

        import os
        if not os.path.exists(dump_folder):
            pytest.skip(f"Dump folder '{dump_folder}' not found.")

        # Create playback
        playback = IRSDKPlayback(dump_folder)
        mock_ir = MockIRSDK(playback)
        mock_ir.startup()

        # Create mock generator
        mock_generator = Mock()
        mock_generator.ir = mock_ir

        # Create drivers object
        drivers = Drivers(mock_generator)

        # You would then create your detector and run it
        # through the recorded dumps to verify it detects
        # the expected incidents

        # Example:
        # from core.detection.off_track_detector import OffTrackDetector
        # detector = OffTrackDetector(mock_generator)
        #
        # for dump in playback:
        #     drivers.update()
        #     result = detector.detect()
        #     # Assert expected behavior based on this dump

        # This is just a skeleton - actual implementation would
        # depend on the specific scenario being tested
        assert True  # Placeholder

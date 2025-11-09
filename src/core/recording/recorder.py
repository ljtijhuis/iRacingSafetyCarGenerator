"""
iRSDK Data Recorder

Records iRSDK data dumps to disk for later playback in tests.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class IRSDKRecorder:
    """Records iRSDK data dumps to numbered files in a timestamped folder."""

    def __init__(self, ir, logs_dir="logs"):
        """
        Initialize the recorder.

        Args:
            ir: iRSDK instance to record from
            logs_dir: Directory where dump folders will be created
        """
        self.ir = ir
        self.logs_dir = logs_dir
        self.is_recording = False
        self.recording_folder = None
        self.dump_count = 0
        self.start_time = None
        self.duration_seconds = None

    def start_recording(self, duration_seconds):
        """
        Start recording iRSDK data.

        Args:
            duration_seconds: How long to record (in seconds)
        """
        if self.is_recording:
            logger.warning("Already recording, ignoring start request")
            return

        # Create timestamped folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_folder = Path(self.logs_dir) / f"dump_{timestamp}"
        self.recording_folder.mkdir(parents=True, exist_ok=True)

        self.is_recording = True
        self.dump_count = 0
        self.start_time = datetime.now()
        self.duration_seconds = duration_seconds

        logger.info(f"Started recording to {self.recording_folder} for {duration_seconds} seconds")

    def stop_recording(self):
        """Stop recording iRSDK data."""
        if not self.is_recording:
            return

        self.is_recording = False
        logger.info(f"Stopped recording. Captured {self.dump_count} dumps to {self.recording_folder}")

        # Save the last folder for UI display
        self._last_folder = self.recording_folder.name if self.recording_folder else None

        # Reset state
        self.recording_folder = None
        self.dump_count = 0
        self.start_time = None
        self.duration_seconds = None

    def should_stop_recording(self):
        """
        Check if recording should stop based on duration.

        Returns:
            bool: True if recording should stop
        """
        if not self.is_recording or self.start_time is None:
            return False

        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed >= self.duration_seconds

    def record_dump(self):
        """
        Record a single dump of iRSDK data.

        Returns:
            bool: True if dump was recorded, False if not recording or auto-stopped
        """
        if not self.is_recording:
            return False

        # Check if we should auto-stop
        if self.should_stop_recording():
            self.stop_recording()
            return False

        try:
            # Capture all relevant iRSDK data
            lap_list = self.ir["CarIdxLap"]
            lap_distance_list = self.ir["CarIdxLapDistPct"]
            total_distance = [t[0] + t[1] for t in zip(lap_list, lap_distance_list)]

            data = {
                "dump_number": self.dump_count,
                "timestamp": datetime.now().isoformat(),
                "SessionNum": self.ir["SessionNum"],
                "SessionInfo": self.ir["SessionInfo"],
                "SessionFlags": self.ir["SessionFlags"],
                "DriverInfo": self.ir["DriverInfo"],
                "CarIdxLap": self.ir["CarIdxLap"],
                "CarIdxLapCompleted": self.ir["CarIdxLapCompleted"],
                "CarIdxLapDistPct": self.ir["CarIdxLapDistPct"],
                "CarIdxClass": self.ir["CarIdxClass"],
                "CarIdxOnPitRoad": self.ir["CarIdxOnPitRoad"],
                "CarIdxTrackSurface": self.ir["CarIdxTrackSurface"],
                "total_distance_computed": total_distance,
            }

            # Write to numbered file
            dump_file = self.recording_folder / f"{self.dump_count:05d}.json"
            with open(dump_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.dump_count += 1
            logger.debug(f"Recorded dump {self.dump_count} to {dump_file}")
            return True

        except Exception as e:
            logger.error(f"Error recording dump: {e}")
            return False

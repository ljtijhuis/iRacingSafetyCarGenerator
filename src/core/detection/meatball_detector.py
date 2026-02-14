import logging

import irsdk
from irsdk import TrkLoc

from core.detection.detector_common_types import DetectionResult, DetectorEventTypes, DetectorState
from core.drivers import Drivers

logger = logging.getLogger(__name__)


class MeatballDetector:
    def __init__(self, drivers: Drivers):
        """Initialize the MeatballDetector.

        Args:
            drivers (Drivers): The Drivers object containing the current state of drivers.
        """
        self.drivers = drivers

    def should_run(self, state: DetectorState) -> bool:
        """Check if this detector should run given current state."""
        return True

    def detect(self) -> DetectionResult:
        """Detect cars with the meatball (repairs required) flag.

        Returns:
            DetectionResult with list of drivers that have the repair flag set.
        """
        meatball_drivers = []

        for driver in self.drivers.current_drivers:
            if driver["is_pace_car"]:
                continue

            if driver["laps_completed"] < 0 or driver["track_loc"] == TrkLoc.not_in_world:
                logger.debug(
                    f"Skipping car #{driver['car_number']} (idx {driver['driver_idx']}): "
                    f"laps_completed={driver['laps_completed']}, track_loc={driver['track_loc']}"
                )
                continue

            if driver["session_flags"] & irsdk.Flags.repair:
                meatball_drivers.append(driver)
                logger.debug(
                    f"Car #{driver['car_number']} (idx {driver['driver_idx']}) "
                    f"has meatball flag (session_flags=0x{driver['session_flags']:08x})"
                )

        if meatball_drivers:
            logger.info(f"Found {len(meatball_drivers)} cars with meatball flag")
        else:
            logger.debug("No cars with meatball flag")

        return DetectionResult(DetectorEventTypes.MEATBALL, drivers=meatball_drivers)

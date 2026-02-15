import logging

import irsdk
from irsdk import TrkLoc

from core.detection.detector_common_types import DetectionResult, DetectorEventTypes, DetectorState
from core.drivers import Drivers

logger = logging.getLogger(__name__)


class MeatballDetector:
    def __init__(self, drivers: Drivers):
        self.drivers = drivers
        self._last_non_pit_position = {}  # driver_idx -> lap_distance

    def should_run(self, state: DetectorState) -> bool:
        """Check if this detector should run given current state."""
        return True

    def detect(self) -> DetectionResult:
        """Detect cars that just received the meatball (repairs required) flag.

        Uses transition detection: only fires when the repair flag appears
        (was not set in previous frame, is set in current frame). Tracks
        last known non-pit position so that if a car tows to pit before
        receiving the flag, the event is registered at the incident location.

        Returns:
            DetectionResult with list of drivers that just received the repair flag.
        """
        meatball_drivers = []

        for current, previous in zip(self.drivers.current_drivers, self.drivers.previous_drivers):
            idx = current["driver_idx"]

            if current["is_pace_car"]:
                continue

            if current["laps_completed"] < 0 or current["track_loc"] == TrkLoc.not_in_world:
                logger.debug(
                    f"Skipping car #{current['car_number']} (idx {idx}): "
                    f"laps_completed={current['laps_completed']}, track_loc={current['track_loc']}"
                )
                continue

            # Track last known non-pit position (on_track or off_track)
            if current["track_loc"] in (TrkLoc.on_track, TrkLoc.off_track):
                self._last_non_pit_position[idx] = current["lap_distance"]

            # Detect transition: repair flag just appeared
            has_repair_now = bool(current["session_flags"] & irsdk.Flags.repair)
            had_repair_before = bool(previous["session_flags"] & irsdk.Flags.repair)

            if has_repair_now and not had_repair_before:
                # Build driver with best known incident position
                driver_at_incident = dict(current)
                if idx in self._last_non_pit_position:
                    driver_at_incident["lap_distance"] = self._last_non_pit_position[idx]

                meatball_drivers.append(driver_at_incident)
                logger.debug(
                    f"Car #{current['car_number']} (idx {idx}) "
                    f"just received meatball flag (session_flags=0x{current['session_flags']:08x})"
                )

        if meatball_drivers:
            logger.info(f"Found {len(meatball_drivers)} cars with new meatball flag")
        else:
            logger.debug("No new meatball flag transitions")

        return DetectionResult(DetectorEventTypes.MEATBALL, drivers=meatball_drivers)

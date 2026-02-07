import irsdk
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DUMPS_DIR = "dumps"

SESSION_INFO_KEYS = [
    "WeekendInfo",
    "SessionInfo",
    "DriverInfo",
    "SplitTimeInfo",
    "CameraInfo",
    "RadioInfo",
    "QualifyResultsInfo",
]


def _make_serializable(value):
    """Convert non-serializable SDK values to JSON-compatible types."""
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_make_serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: _make_serializable(v) for k, v in value.items()}
    # irsdk enums and other types
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def dump_sdk_snapshot(ir):
    """Capture a snapshot of all available SDK telemetry and session data.

    Args:
        ir: A connected irsdk.IRSDK instance.

    Returns:
        dict: All telemetry variables and session info sections.
    """
    snapshot = {
        "_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch": time.time(),
        }
    }

    # Telemetry variables
    telemetry = {}
    for var_name in ir.var_headers_names:
        try:
            telemetry[var_name] = _make_serializable(ir[var_name])
        except Exception:
            logger.debug("Could not read telemetry var: %s", var_name)
    snapshot["telemetry"] = telemetry

    # Session info sections
    session_info = {}
    for key in SESSION_INFO_KEYS:
        try:
            value = ir[key]
            if value is not None:
                session_info[key] = _make_serializable(value)
        except Exception:
            logger.debug("Could not read session info: %s", key)
    snapshot["session_info"] = session_info

    return snapshot


def save_snapshot(ir, output_dir=DUMPS_DIR):
    """Capture and save an SDK snapshot to a JSON file.

    Args:
        ir: A connected irsdk.IRSDK instance.
        output_dir: Directory to write the dump file into.

    Returns:
        str: Path to the saved JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    snapshot = dump_sdk_snapshot(ir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{timestamp}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    logger.info("SDK snapshot saved to %s", file_path)
    return file_path


class SdkRecorder:
    """Records SDK snapshots continuously to an NDJSON file."""

    def __init__(self):
        self._shutdown_event = threading.Event()
        self._thread = None
        self._output_file = None

    def start(self, ir, output_dir=DUMPS_DIR):
        """Start recording SDK snapshots every second.

        Args:
            ir: A connected irsdk.IRSDK instance.
            output_dir: Directory to write the recording file into.
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_file = os.path.join(output_dir, f"{timestamp}_recording.ndjson")
        self._shutdown_event.clear()
        self._ir = ir
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        logger.info("SDK recording started: %s", self._output_file)

    def _record_loop(self):
        with open(self._output_file, "a", encoding="utf-8") as f:
            while not self._shutdown_event.is_set():
                try:
                    snapshot = dump_sdk_snapshot(self._ir)
                    f.write(json.dumps(snapshot) + "\n")
                    f.flush()
                except Exception:
                    logger.exception("Error capturing SDK snapshot during recording")
                self._shutdown_event.wait(timeout=1.0)

    def stop(self):
        """Stop the recording and return the output file path.

        Returns:
            str: Path to the NDJSON recording file.
        """
        self._shutdown_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("SDK recording stopped: %s", self._output_file)
        return self._output_file

    @property
    def is_recording(self):
        return self._thread is not None and self._thread.is_alive()

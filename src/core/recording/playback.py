"""
iRSDK Data Playback

Provides playback of recorded iRSDK dumps for testing.
"""

import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any

logger = logging.getLogger(__name__)


class IRSDKPlayback:
    """
    Plays back recorded iRSDK data dumps for testing.

    This class provides an iterator interface to replay recorded dumps
    in sequence, simulating a live iRacing session.
    """

    def __init__(self, dump_folder):
        """
        Initialize playback from a dump folder.

        Args:
            dump_folder: Path to the folder containing numbered dump files
        """
        self.dump_folder = Path(dump_folder)
        self.dump_files = sorted(self.dump_folder.glob("*.json"))
        self.current_index = 0

        if not self.dump_files:
            raise ValueError(f"No dump files found in {dump_folder}")

        logger.info(f"Loaded playback with {len(self.dump_files)} dumps from {dump_folder}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Make the playback object iterable."""
        self.current_index = 0
        return self

    def __next__(self) -> Dict[str, Any]:
        """
        Get the next dump in the sequence.

        Returns:
            dict: The next iRSDK data dump

        Raises:
            StopIteration: When all dumps have been played
        """
        if self.current_index >= len(self.dump_files):
            raise StopIteration

        dump_file = self.dump_files[self.current_index]
        self.current_index += 1

        with open(dump_file, 'r') as f:
            data = json.load(f)

        logger.debug(f"Playing dump {self.current_index}/{len(self.dump_files)}: {dump_file.name}")
        return data

    def get_dump(self, index: int) -> Dict[str, Any]:
        """
        Get a specific dump by index.

        Args:
            index: Index of the dump to retrieve (0-based)

        Returns:
            dict: The iRSDK data dump at the specified index

        Raises:
            IndexError: If index is out of range
        """
        if index < 0 or index >= len(self.dump_files):
            raise IndexError(f"Dump index {index} out of range (0-{len(self.dump_files)-1})")

        dump_file = self.dump_files[index]
        with open(dump_file, 'r') as f:
            return json.load(f)

    def reset(self):
        """Reset playback to the beginning."""
        self.current_index = 0
        logger.debug("Playback reset to beginning")

    @property
    def total_dumps(self) -> int:
        """Get the total number of dumps available."""
        return len(self.dump_files)

    @property
    def current_position(self) -> int:
        """Get the current playback position (0-based index)."""
        return self.current_index


class MockIRSDK:
    """
    Mock iRSDK object that uses playback data.

    This class mimics the iRSDK interface but returns data from
    recorded dumps instead of connecting to iRacing.
    """

    def __init__(self, playback: IRSDKPlayback):
        """
        Initialize mock iRSDK with playback data.

        Args:
            playback: IRSDKPlayback instance to use for data
        """
        self.playback = playback
        self.current_data = None
        self._connected = False

    def startup(self, test_file=None):
        """
        Simulate iRSDK startup.

        Args:
            test_file: Ignored (for compatibility with real iRSDK)

        Returns:
            bool: Always True for mock
        """
        self._connected = True
        # Load the first dump
        try:
            self.current_data = next(self.playback)
            return True
        except StopIteration:
            return False

    def shutdown(self):
        """Simulate iRSDK shutdown."""
        self._connected = False
        self.current_data = None

    def __getitem__(self, key):
        """
        Get data from the current dump.

        Args:
            key: The data field to retrieve

        Returns:
            The value for the specified key
        """
        if not self._connected or self.current_data is None:
            raise RuntimeError("Mock iRSDK not connected")

        if key not in self.current_data:
            raise KeyError(f"Key '{key}' not found in dump data")

        return self.current_data[key]

    def advance(self):
        """
        Advance to the next dump in the playback sequence.

        Returns:
            bool: True if advanced, False if no more dumps
        """
        try:
            self.current_data = next(self.playback)
            return True
        except StopIteration:
            return False

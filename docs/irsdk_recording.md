# iRSDK Data Recording and Playback

This feature allows you to record iRSDK data during live iRacing sessions and replay it in tests to simulate real-world scenarios.

## Overview

The recording system captures full iRSDK data dumps on every driver data refresh (approximately once per second). This data can then be replayed in tests without requiring a live iRacing connection.

## Recording Data

### Prerequisites

- Run the application in developer mode: `python src/main.py -dev`
- Be connected to an active iRacing session

### How to Record

1. Start the application with the `-dev` flag
2. In the UI, look for the "DEVELOPER MODE" panel
3. Enter the desired recording duration in seconds (default: 30)
4. Click "Start Recording iRSDK"
5. The button will change to "Stop Recording" and show the recording status
6. Recording will automatically stop after the specified duration, or you can stop it manually

### What Gets Recorded

Each dump includes:
- `SessionNum` - Current session number
- `SessionInfo` - Full session information
- `SessionFlags` - Current session flags
- `DriverInfo` - Complete driver information
- `CarIdxLap` - Current lap for each car
- `CarIdxLapCompleted` - Completed laps for each car
- `CarIdxLapDistPct` - Lap distance percentage for each car
- `CarIdxClass` - Class for each car
- `CarIdxOnPitRoad` - Pit road status for each car
- `CarIdxTrackSurface` - Track surface location for each car
- `total_distance_computed` - Calculated total distance
- `dump_number` - Sequential dump number
- `timestamp` - ISO format timestamp of when the dump was captured

### Output Location

Dumps are saved in the `logs/` directory with the following structure:

```
logs/
  └── dump_20240101_120000/
      ├── 00000.json
      ├── 00001.json
      ├── 00002.json
      └── ...
```

Each folder is named `dump_{timestamp}` and contains numbered JSON files (00000.json, 00001.json, etc.).

## Replaying Data in Tests

### Using IRSDKPlayback

The `IRSDKPlayback` class provides an iterator interface for replaying dumps:

```python
from core.recording.playback import IRSDKPlayback

# Load a dump folder
playback = IRSDKPlayback("logs/dump_20240101_120000")

# Iterate through all dumps
for dump in playback:
    session_num = dump["SessionNum"]
    driver_info = dump["DriverInfo"]
    # ... use the data

# Or get a specific dump by index
first_dump = playback.get_dump(0)

# Reset to beginning
playback.reset()
```

### Using MockIRSDK

The `MockIRSDK` class mimics the real iRSDK interface but uses playback data:

```python
from core.recording.playback import IRSDKPlayback, MockIRSDK

# Create playback
playback = IRSDKPlayback("logs/dump_20240101_120000")

# Create mock iRSDK
mock_ir = MockIRSDK(playback)

# Use just like real iRSDK
mock_ir.startup()

# Access data with the same API
session_num = mock_ir["SessionNum"]
driver_info = mock_ir["DriverInfo"]
car_laps = mock_ir["CarIdxLap"]

# Advance to next dump
mock_ir.advance()

# Shutdown when done
mock_ir.shutdown()
```

### Example Test

```python
import pytest
from core.recording.playback import IRSDKPlayback, MockIRSDK
from core.drivers import Drivers
from unittest.mock import Mock

def test_with_recorded_data():
    """Test using recorded iRSDK data."""
    # Load playback
    playback = IRSDKPlayback("logs/dump_20240101_120000")
    mock_ir = MockIRSDK(playback)
    mock_ir.startup()

    # Create mock generator
    mock_generator = Mock()
    mock_generator.ir = mock_ir

    # Use with Drivers class
    drivers = Drivers(mock_generator)
    drivers.update()

    # Verify driver state
    assert len(drivers.current) > 0

    # Advance to next dump
    mock_ir.advance()
    drivers.update()

    # Continue testing with updated state
    # ...
```

## Use Cases

### 1. Testing Detectors with Real Scenarios

Record a session where a specific incident occurs (e.g., multiple cars going off track), then use that recording to verify your detector behaves correctly:

```python
def test_off_track_detector_real_scenario():
    playback = IRSDKPlayback("logs/dump_multi_car_off_track")
    mock_ir = MockIRSDK(playback)
    # ... run detector on each dump and verify it triggers
```

### 2. Debugging Edge Cases

When you encounter unexpected behavior during a live session:
1. Start recording immediately
2. Capture 30-60 seconds of data
3. Use the recording to reproduce and debug the issue

### 3. Performance Testing

Record different race scenarios and use them for consistent performance benchmarking:

```python
def test_performance_with_full_grid():
    playback = IRSDKPlayback("logs/dump_60_car_grid")
    # ... measure detector performance
```

### 4. Integration Testing

Test complete workflows with realistic data without requiring iRacing to be running:

```python
def test_full_safety_car_procedure():
    playback = IRSDKPlayback("logs/dump_incident_to_green")
    # ... test entire SC procedure from detection to green flag
```

## Best Practices

1. **Meaningful Names**: Rename dump folders to describe what they contain:
   ```
   logs/dump_20240101_120000/ → logs/dump_multi_car_pileup_lap1/
   ```

2. **Short Recordings**: Record only what you need (10-60 seconds typically)

3. **Document Scenarios**: Add a README.txt in the dump folder describing what happens

4. **Version Control**: Consider committing key recordings to git for shared test scenarios

5. **Clean Up**: Delete unnecessary recordings to save disk space

## Limitations

- Recordings capture only iRSDK data, not the full simulation state
- Cannot replay user inputs or command sends (those must be mocked separately)
- Large recordings (many dumps) consume significant disk space
- Recorded data is specific to the track, cars, and session type

## Troubleshooting

**Recording doesn't start:**
- Ensure you're in developer mode (`-dev` flag)
- Verify iRacing is running and connected
- Check the logs for error messages

**Playback fails:**
- Verify the dump folder exists and contains .json files
- Check that files are valid JSON (not corrupted)
- Ensure the path is correct (relative to working directory)

**Missing data fields:**
- Older recordings may not have all current fields
- Re-record if the data structure has changed

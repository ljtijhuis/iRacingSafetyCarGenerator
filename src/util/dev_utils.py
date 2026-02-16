import irsdk
import json
import pyperclip
import os
import re
import csv
from datetime import datetime
from collections import defaultdict

from core.interactions.interaction_factories import CommandSenderFactory

def copy_sdk_data_to_clipboard():
    """Takes a snapshot of data provided by the SDK and copies it to your clipboard
    
    Args: 
        None
    """
    ir = irsdk.IRSDK()
    connected = False
    try:
        if not ir.startup():
            pyperclip.copy("Could not connect through the SDK")
            return

        connected = True

        from util.sdk_dump import dump_sdk_snapshot
        data = dump_sdk_snapshot(ir)

        pyperclip.copy(json.dumps(data, indent=4))

    finally:
        if connected:
            ir.shutdown()

def send_test_commands():
    """This util was written to test the limits of iRacing receiving chat commands. We 
    noticed if delays between messages were too short, iRacing would drop some of the 
    messages, which is detrimental to a lot of our procedures.
    Testing showed that with a delay of 0.1 seconds, we would see a drop after every 
    16th message. This was resolved with a 0.2 second delay, so we are using 0.5 seconds 
    in our application to be safe.
    
    Other notes:
        - Performance was worse when sitting in the car than when just in the garage view.
        - We moved the delay until after the chat command was sent, which seemed to help.
    """
    ir = irsdk.IRSDK()
    connected = False
    try:
        if not ir.startup():
            print("Could not connect through the SDK")
            return
        connected = True

        arguments = lambda: None
        arguments.dry_run = False
        arguments.disable_window_interactions = False

        command_sender = CommandSenderFactory(arguments, ir) # type: ignore
        command_sender.connect()
        
        # Uncomment for sending regular chat commands
        # for i in range(1, 100):
        #     command_sender.send_command(f"Test Command {i}", 0.5)
        #     print(f"Sent command: Test Command {i}")
        
        cars_to_wave = []
        for driver in ir["DriverInfo"]["Drivers"]:
            cars_to_wave.append(driver["CarNumber"])
            
        for car in cars_to_wave:
            command_sender.send_command(f"!w {car}")
            print(f"!w {car}")

    finally:
        if connected:
            ir.shutdown()

def parse_log_events_to_csv(log_file_path):
    """Parse a single log file to extract detection events and generate CSV.

    This function searches through a log file to find events related to off track
    incidents, stopped cars, meatball flags, and towing, then generates a CSV file
    with timestamps and event counts for graphing in Google Docs.

    Args:
        log_file_path (str): Path to the log file to parse

    Returns:
        str: Path to the generated CSV file
    """
    if not os.path.exists(log_file_path):
        raise FileNotFoundError(f"Log file '{log_file_path}' not found")
    
    # Generate CSV filename by replacing .log with .csv
    csv_file_path = log_file_path.rsplit('.', 1)[0] + '.csv'
    
    # Dictionary to store events by timestamp
    # Each entry contains counts and car number sets for each event type
    events_by_time = defaultdict(lambda: {
        "off_track": 0, "stopped": 0, "meatball": 0, "towing": 0,
        "off_track_cars": set(), "stopped_cars": set(), "meatball_cars": set(), "towing_cars": set()
    })

    # Track race start time for time_since_start calculation
    race_start_time = None

    # Pattern to match threshold checking log entries with events_dict
    # Captures all 5 event types: OFF_TRACK, MEATBALL, RANDOM, STOPPED, TOWING
    threshold_pattern = re.compile(
        r'Checking threshold, events_dict=\{'
        r'<DetectorEventTypes\.OFF_TRACK.*?>\: (\{[^}]*\}), '
        r'<DetectorEventTypes\.MEATBALL.*?>\: (\{[^}]*\}), '
        r'<DetectorEventTypes\.RANDOM.*?>\: (\{[^}]*\}), '
        r'<DetectorEventTypes\.STOPPED.*?>\: (\{[^}]*\}), '
        r'<DetectorEventTypes\.TOWING.*?>\: (\{[^}]*\})\}'
    )

    # Pattern to match race start log entries
    race_start_pattern = re.compile(r'Race started at')

    # Pattern to extract car numbers from "Sorted events with positions" log lines
    # Matches event type and car_number pairs
    car_number_pattern = re.compile(
        r"<DetectorEventTypes\.(OFF_TRACK|MEATBALL|STOPPED|TOWING): '[^']+'>.*?'car_number': '([^']+)'"
    )

    print(f"Processing {log_file_path}...")
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Extract timestamp from log line
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not timestamp_match:
                    continue

                timestamp_str = timestamp_match.group(1)

                # Check for race start to capture the first start time
                if race_start_time is None and race_start_pattern.search(line):
                    race_start_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    print(f"Race started at: {race_start_time}")

                # Check for threshold checking logs with events_dict
                threshold_match = threshold_pattern.search(line)
                if threshold_match:
                    off_track_dict_str = threshold_match.group(1)
                    meatball_dict_str = threshold_match.group(2)
                    # random_dict_str = threshold_match.group(3)  # Ignored for CSV output
                    stopped_dict_str = threshold_match.group(4)
                    towing_dict_str = threshold_match.group(5)

                    # Count unique drivers for each event type (number of keys in dict)
                    # Empty dict is "{}", non-empty will have driver IDs as keys
                    off_track_count = 0 if off_track_dict_str == '{}' else len([x for x in off_track_dict_str.split(',') if ':' in x])
                    meatball_count = 0 if meatball_dict_str == '{}' else len([x for x in meatball_dict_str.split(',') if ':' in x])
                    stopped_count = 0 if stopped_dict_str == '{}' else len([x for x in stopped_dict_str.split(',') if ':' in x])
                    towing_count = 0 if towing_dict_str == '{}' else len([x for x in towing_dict_str.split(',') if ':' in x])

                    # Note: We ignore random events (group 3) for CSV output as they're not used for threshold calculations

                    # Record all threshold checking events, including when counts are 0
                    events_by_time[timestamp_str]["off_track"] = off_track_count
                    events_by_time[timestamp_str]["stopped"] = stopped_count
                    events_by_time[timestamp_str]["meatball"] = meatball_count
                    events_by_time[timestamp_str]["towing"] = towing_count

                # Check for "Sorted events with positions" to extract car numbers
                if 'Sorted events with positions' in line:
                    # Extract all (event_type, car_number) pairs from the line
                    for match in car_number_pattern.finditer(line):
                        event_type = match.group(1).lower()  # OFF_TRACK -> off_track
                        car_number = match.group(2)
                        car_key = f"{event_type}_cars"
                        if car_key in events_by_time[timestamp_str]:
                            events_by_time[timestamp_str][car_key].add(car_number)
                    
    except Exception as e:
        raise Exception(f"Error reading log file: {e}")
    
    if not events_by_time:
        # Create an empty CSV with headers if no events found
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Date', 'Time', 'Time Since Start', 'Off Track Events', 'Off Track Cars', 'Stopped Car Events', 'Stopped Cars', 'Meatball Events', 'Meatball Cars', 'Towing Events', 'Towing Cars', 'Total Events'])
        print("No events found in log file, created empty CSV with headers")
        return csv_file_path
    
    # Sort events by timestamp
    sorted_events = sorted(events_by_time.items())
    
    # Write to CSV
    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Timestamp', 'Date', 'Time', 'Time Since Start', 'Off Track Events', 'Off Track Cars', 'Stopped Car Events', 'Stopped Cars', 'Meatball Events', 'Meatball Cars', 'Towing Events', 'Towing Cars', 'Total Events'])

            # Write data rows
            for timestamp_str, events in sorted_events:
                try:
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M:%S')

                    # Calculate time since race start
                    if race_start_time is not None:
                        delta = dt - race_start_time
                        total_seconds = int(delta.total_seconds())
                        hours, remainder = divmod(max(0, total_seconds), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_since_start = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        time_since_start = "N/A"

                    off_track_count = events["off_track"]
                    stopped_count = events["stopped"]
                    meatball_count = events["meatball"]
                    towing_count = events["towing"]
                    total_count = off_track_count + stopped_count + meatball_count + towing_count

                    # Format car numbers as comma-separated strings (sorted for consistency)
                    off_track_cars = ', '.join(sorted(events["off_track_cars"])) if events["off_track_cars"] else ''
                    stopped_cars = ', '.join(sorted(events["stopped_cars"])) if events["stopped_cars"] else ''
                    meatball_cars = ', '.join(sorted(events["meatball_cars"])) if events["meatball_cars"] else ''
                    towing_cars = ', '.join(sorted(events["towing_cars"])) if events["towing_cars"] else ''

                    writer.writerow([
                        timestamp_str,
                        date_str,
                        time_str,
                        time_since_start,
                        off_track_count,
                        off_track_cars,
                        stopped_count,
                        stopped_cars,
                        meatball_count,
                        meatball_cars,
                        towing_count,
                        towing_cars,
                        total_count
                    ])
                except ValueError as e:
                    print(f"Error parsing timestamp {timestamp_str}: {e}")
                    continue
        
        # Print summary statistics
        total_off_track = sum(events["off_track"] for events in events_by_time.values())
        total_stopped = sum(events["stopped"] for events in events_by_time.values())
        total_meatball = sum(events["meatball"] for events in events_by_time.values())
        total_towing = sum(events["towing"] for events in events_by_time.values())

        print(f"Successfully created {csv_file_path}")
        print(f"Found {len(sorted_events)} time points with events")
        print(f"Summary:")
        print(f"  Total Off Track Events: {total_off_track}")
        print(f"  Total Stopped Car Events: {total_stopped}")
        print(f"  Total Meatball Events: {total_meatball}")
        print(f"  Total Towing Events: {total_towing}")
        print(f"  Total Events: {total_off_track + total_stopped + total_meatball + total_towing}")
        
        return csv_file_path
        
    except Exception as e:
        raise Exception(f"Error writing CSV file: {e}")
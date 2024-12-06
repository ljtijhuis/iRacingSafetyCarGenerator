import csv
from datetime import datetime

class TelemetryLogger:
    """The TelemetryLogger is responsible for recording time series data during sim racing events. 
    
    This data can be used to understand the behavior of the safetycar generator and finetune your preferred settings.
    """
    def __init__(self, drivers):
        self.drivers = drivers

        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"logs/telemetry_{current_datetime}.csv"
        fieldnames = ['timestamp', 'stopped', 'stopped_details', 'off_track', 'off_track_details', 'total_sc_events', 'last_sc_time', 'total_random_sc_events', 'lap_at_sc', 'current_lap_under_sc']

        # We keep the file open for the lifespan of the object
        self.log_file = open(filename, mode='w', newline='')
        self.writer = csv.DictWriter(self.log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
        self.writer.writeheader()

    def __del__(self):
        # Make sure we close the file handle
        self.log_file.close()
    
    def log(self):
        self.writer.writerow({
            'timestamp': datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f"), 
            'stopped': '0', 
            'stopped_details': '', 
            'off_track': '',
            'off_track_details': '',
            'total_sc_events': '',
            'last_sc_time': '',
            'total_random_sc_events': '',
            'lap_at_sc': '',
            'current_lap_under_sc': ''
        })

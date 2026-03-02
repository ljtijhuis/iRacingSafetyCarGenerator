from datetime import datetime
import logging
import logging.config
import json
import os

from core.app import App
from ui.events_log import EventsLogHandler

# Module-level reference so the App can attach its panel later
events_log_handler = EventsLogHandler(level=logging.INFO)


def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger(__name__)

    # Configure logging
    with open("logging.json") as logging_conf_file:
        logging_conf = json.load(logging_conf_file)

    # Dynamically set log file name to current time
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = logging_conf["handlers"]["file"]["filename"]
    logging_conf["handlers"]["file"]["filename"] = logfile.replace("{current_datetime}", current_datetime)

    logging.config.dictConfig(logging_conf)

    # Add the events log handler to all loggers that have the file handler,
    # so INFO+ messages appear in the UI panel as well as the log file
    events_log_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    )
    for logger_name in logging_conf.get("loggers", {}):
        logging.getLogger(logger_name).addHandler(events_log_handler)

    # Log the start of the program
    logger.info("Program started")

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(
        prog='iRacingSafetyCarGenerator',
        description='Trigger automated safety car events in iRacing')
    parser.add_argument('-dwi', '--disable-window-interactions', action='store_true')
    parser.add_argument('-dev', '--developer-mode', action='store_true')
    parser.add_argument('-dry', '--dry-run', action='store_true')
    args = parser.parse_args()
    
    return args

def main(arguments):
    """Main function for the safety car generator."""
    # Set up logging
    setup_logging()

    # Try to create and run the app, and log exceptions
    try:
        app = App(arguments, events_log_handler=events_log_handler)
        app.mainloop()
    except Exception as e:
        logging.exception("A fatal error has occurred")
        raise e

if __name__ == "__main__":
    arguments = parse_arguments()
    main(arguments)
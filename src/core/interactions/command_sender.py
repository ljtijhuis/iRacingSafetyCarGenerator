import logging
import time

logger = logging.getLogger(__name__)

class CommandSender:
    """ Sends commands to the iRacing application. """

    def __init__(self, iracing_window, irsdk):
        """Initialize the CommandSender object.

        Args:
            iracing_window: The window object used to interact with the iRacing application.
            irsdk: A reference to an irSDK instance.
        """
        logger.info("Initializing CommandSender")
        self.iracing_window = iracing_window
        self.irsdk = irsdk


    def connect(self):
        """ Find the iRacing application window and keep a handle. """
        self.iracing_window.connect()
    

    def send_command(self, command, delay = 0.0):
        """ Sends the provided command to the iRacing application window.

        Args:
            command: The command to send. Should NOT include the {ENTER} character!
        """
        logger.info(f"Sending command: {command}")

        self.iracing_window.focus()
        # Send a quick escape to close a potential chat 
        self.iracing_window.send_message("{ESC}")
        # Now open the chat
        self.irsdk.chat_command(1)
        # And send the command
        self.iracing_window.send_message(command)
        if delay > 0:
            logger.debug(f"Adding delay after send_message of: {delay}")
            time.sleep(delay)

    def send_commands(self, commands, delay = 0.1):
        """ Sends the list of commands in order with the provided delay.
        
        Args:
            commands: List of commands to send. Should NOT include the {ENTER} character!
            delay: How much delay to add (in seconds) between each command
        """
        for command in commands:
            self.send_command(command, delay)


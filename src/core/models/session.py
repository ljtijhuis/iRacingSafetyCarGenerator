import logging
import irsdk

logger = logging.getLogger(__name__)


class Session:
    """The Session class is responsible for tracking session-related state.
    
    This class centralizes access to session information from the iRacing SDK,
    including session type, flags, and session management.
    """
    
    def __init__(self, master=None):
        """Initialize the Session class.
        
        Args:
            master (object): The master object that is responsible for the
                connection to the iRacing API.
        """
        self.master = master
        
        # Session state
        self._session_info = None
        self._current_session_num = None
        self._session_flags = None
        self._sessions = {}
        
        # Do initial update
        self.update()
    
    def update(self):
        """Update session data from the iRacing API.
        
        This method should be called each loop to refresh session information.
        """
        logger.debug("Updating session data")
        
        try:
            # Get session information
            self._session_info = self.master.ir["SessionInfo"]
            self._current_session_num = self.master.ir["SessionNum"]
            self._session_flags = self.master.ir["SessionFlags"]
            
            # Build sessions dictionary for easy lookup
            if self._session_info and "Sessions" in self._session_info:
                self._sessions = {}
                for i, session in enumerate(self._session_info["Sessions"]):
                    self._sessions[i] = session["SessionName"]
        except Exception as e:
            # Handle cases where iRacing SDK data is not available (e.g., in tests)
            logger.debug(f"Failed to update session data: {e}")
            self._session_info = None
            self._current_session_num = 0
            self._session_flags = 0
            self._sessions = {}
    
    def is_green_flag(self) -> bool:
        """Check if the green flag is currently displayed.
        
        Returns:
            True if green flag is active, False otherwise
        """
        if self._session_flags is None:
            return False
        return bool(self._session_flags & irsdk.Flags.green)
    
    def is_race_session(self) -> bool:
        """Check if the current session is a race session.
        
        Returns:
            True if current session is a race (not PRACTICE, QUALIFY, or WARMUP)
        """
        current_session_name = self.get_current_session_name()
        if current_session_name is None:
            return False
        
        non_race_sessions = ["PRACTICE", "QUALIFY", "WARMUP"]
        return current_session_name not in non_race_sessions
    
    def get_current_session_name(self) -> str:
        """Get the name of the current session.
        
        Returns:
            The current session name, or None if not available
        """
        if self._current_session_num is None or self._current_session_num not in self._sessions:
            return None
        
        return self._sessions[self._current_session_num]
    
    def get_current_session_num(self) -> int:
        """Get the current session number.
        
        Returns:
            The current session number
        """
        return self._current_session_num
    
    def get_session_flags(self) -> int:
        """Get the current session flags.
        
        Returns:
            The session flags bitmask
        """
        return self._session_flags
    
    def get_all_sessions(self) -> dict[int, str]:
        """Get all available sessions.
        
        Returns:
            Dictionary mapping session indices to session names
        """
        return self._sessions.copy()
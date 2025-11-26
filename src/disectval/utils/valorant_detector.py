"""
Valorant process detection utility.
Checks if Valorant is running to manage input behavior.
"""

import logging
from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


# Valorant related process names
VALORANT_PROCESSES = {
    'VALORANT-Win64-Shipping.exe',
    'VALORANT.exe',
    'RiotClientServices.exe',
}


class ValorantDetector:
    """Detects if Valorant is currently running."""
    
    def __init__(self):
        """Initialize the Valorant detector."""
        self._valorant_running = False
        self._valorant_pid: Optional[int] = None
    
    def is_valorant_running(self) -> bool:
        """
        Check if Valorant is currently running.
        
        Returns:
            True if Valorant process is detected
        """
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available, cannot detect Valorant")
            return False
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] in VALORANT_PROCESSES:
                        if proc.info['name'] != 'RiotClientServices.exe':
                            self._valorant_running = True
                            self._valorant_pid = proc.info['pid']
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error checking for Valorant: {e}")
        
        self._valorant_running = False
        self._valorant_pid = None
        return False
    
    def get_valorant_pid(self) -> Optional[int]:
        """Get the PID of the Valorant process if running."""
        if self._valorant_running:
            return self._valorant_pid
        return None
    
    def should_block_input(self, user_allowed_input: bool) -> bool:
        """
        Determine if input should be blocked.
        
        Args:
            user_allowed_input: Whether the user has permission for input during Valorant
            
        Returns:
            True if input should be blocked (Valorant running and user not allowed)
        """
        if not self.is_valorant_running():
            return False  # No blocking needed if Valorant not running
        
        # Block input if Valorant is running and user hasn't been granted permission
        return not user_allowed_input


class InputController:
    """Controls input state based on Valorant detection."""
    
    def __init__(self, valorant_detector: ValorantDetector):
        """
        Initialize the input controller.
        
        Args:
            valorant_detector: ValorantDetector instance
        """
        self.detector = valorant_detector
        self._input_enabled = True
        self._user_override = False  # SGM can override this at session start
    
    def set_user_override(self, allowed: bool) -> None:
        """
        Set whether user has override permission for input during Valorant.
        This should be set at session start for users with BYPASS_VALORANT_CHECK permission.
        
        Args:
            allowed: Whether to allow input during Valorant
        """
        self._user_override = allowed
    
    def check_input_state(self) -> bool:
        """
        Check current input state.
        
        Returns:
            True if input is currently allowed
        """
        if self._user_override:
            return True
        
        if self.detector.is_valorant_running():
            self._input_enabled = False
            return False
        
        self._input_enabled = True
        return True
    
    def is_input_enabled(self) -> bool:
        """Get current input state without rechecking."""
        return self._input_enabled

"""
Tests for the Valorant detector utility.
"""

import pytest

from disectval.utils.valorant_detector import (
    InputController,
    ValorantDetector,
    VALORANT_PROCESSES,
)


class TestValorantDetector:
    """Tests for ValorantDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a ValorantDetector instance."""
        return ValorantDetector()
    
    def test_valorant_processes_defined(self):
        """Test that Valorant process names are defined."""
        assert 'VALORANT-Win64-Shipping.exe' in VALORANT_PROCESSES
        assert 'VALORANT.exe' in VALORANT_PROCESSES
        assert 'RiotClientServices.exe' in VALORANT_PROCESSES
    
    def test_detector_initializes(self, detector):
        """Test that detector initializes correctly."""
        assert detector._valorant_running is False
        assert detector._valorant_pid is None
    
    def test_get_valorant_pid_when_not_running(self, detector):
        """Test get_valorant_pid returns None when not detected."""
        # Assuming Valorant is not running during tests
        assert detector.get_valorant_pid() is None


class TestInputController:
    """Tests for InputController."""
    
    @pytest.fixture
    def detector(self):
        """Create a ValorantDetector instance."""
        return ValorantDetector()
    
    @pytest.fixture
    def controller(self, detector):
        """Create an InputController instance."""
        return InputController(detector)
    
    def test_controller_initializes(self, controller):
        """Test that controller initializes correctly."""
        assert controller._input_enabled is True
        assert controller._user_override is False
    
    def test_set_user_override(self, controller):
        """Test setting user override."""
        controller.set_user_override(True)
        assert controller._user_override is True
        
        controller.set_user_override(False)
        assert controller._user_override is False
    
    def test_check_input_state_no_valorant(self, controller):
        """Test input state when Valorant is not running."""
        # Assuming Valorant is not running during tests
        result = controller.check_input_state()
        assert result is True
        assert controller._input_enabled is True
    
    def test_input_enabled_with_override(self, controller):
        """Test that input is enabled with user override."""
        controller.set_user_override(True)
        
        # Even if Valorant check would fail, override should allow input
        result = controller.check_input_state()
        assert result is True
    
    def test_is_input_enabled(self, controller):
        """Test is_input_enabled method."""
        assert controller.is_input_enabled() is True

"""
Tests for the Windows settings checker.
"""

import pytest

from disectval.utils.windows_checker import (
    CheckStatus,
    SettingCheck,
    WindowsSettingsChecker,
)


class TestWindowsSettingsChecker:
    """Tests for WindowsSettingsChecker."""
    
    @pytest.fixture
    def checker(self):
        """Create a WindowsSettingsChecker instance."""
        return WindowsSettingsChecker()
    
    def test_setting_check_dataclass(self):
        """Test SettingCheck dataclass."""
        check = SettingCheck(
            name="Test Check",
            category="Test Category",
            status=CheckStatus.OPTIMAL,
            current_value="Enabled",
            recommended_value="Enabled",
            description="Test description",
            how_to_fix="No fix needed",
            can_auto_fix=True,
        )
        
        assert check.name == "Test Check"
        assert check.category == "Test Category"
        assert check.status == CheckStatus.OPTIMAL
        assert check.can_auto_fix is True
    
    def test_check_status_enum(self):
        """Test CheckStatus enum values."""
        assert CheckStatus.OPTIMAL.value == "optimal"
        assert CheckStatus.SUBOPTIMAL.value == "suboptimal"
        assert CheckStatus.CRITICAL.value == "critical"
    
    def test_get_checks_by_status(self, checker):
        """Test filtering checks by status."""
        # Manually add some test checks
        checker._checks = [
            SettingCheck(
                name="Optimal Check",
                category="Test",
                status=CheckStatus.OPTIMAL,
                current_value="Good",
                recommended_value="Good",
                description="",
                how_to_fix="",
            ),
            SettingCheck(
                name="Critical Check",
                category="Test",
                status=CheckStatus.CRITICAL,
                current_value="Bad",
                recommended_value="Good",
                description="",
                how_to_fix="",
            ),
        ]
        
        optimal = checker.get_checks_by_status(CheckStatus.OPTIMAL)
        critical = checker.get_checks_by_status(CheckStatus.CRITICAL)
        
        assert len(optimal) == 1
        assert optimal[0].name == "Optimal Check"
        assert len(critical) == 1
        assert critical[0].name == "Critical Check"
    
    def test_get_checks_by_category(self, checker):
        """Test filtering checks by category."""
        checker._checks = [
            SettingCheck(
                name="Mouse Check",
                category="Mouse Settings",
                status=CheckStatus.OPTIMAL,
                current_value="Good",
                recommended_value="Good",
                description="",
                how_to_fix="",
            ),
            SettingCheck(
                name="Power Check",
                category="Power Settings",
                status=CheckStatus.OPTIMAL,
                current_value="Good",
                recommended_value="Good",
                description="",
                how_to_fix="",
            ),
        ]
        
        mouse = checker.get_checks_by_category("Mouse Settings")
        power = checker.get_checks_by_category("Power Settings")
        
        assert len(mouse) == 1
        assert mouse[0].name == "Mouse Check"
        assert len(power) == 1
        assert power[0].name == "Power Check"
    
    def test_get_summary(self, checker):
        """Test summary generation."""
        checker._checks = [
            SettingCheck(
                name="Check 1",
                category="Test",
                status=CheckStatus.OPTIMAL,
                current_value="",
                recommended_value="",
                description="",
                how_to_fix="",
            ),
            SettingCheck(
                name="Check 2",
                category="Test",
                status=CheckStatus.SUBOPTIMAL,
                current_value="",
                recommended_value="",
                description="",
                how_to_fix="",
            ),
            SettingCheck(
                name="Check 3",
                category="Test",
                status=CheckStatus.CRITICAL,
                current_value="",
                recommended_value="",
                description="",
                how_to_fix="",
            ),
            SettingCheck(
                name="Check 4",
                category="Test",
                status=CheckStatus.OPTIMAL,
                current_value="",
                recommended_value="",
                description="",
                how_to_fix="",
            ),
        ]
        
        summary = checker.get_summary()
        
        assert summary["total"] == 4
        assert summary["optimal"] == 2
        assert summary["suboptimal"] == 1
        assert summary["critical"] == 1

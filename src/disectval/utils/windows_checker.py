"""
Windows settings checker for optimal gaming performance.
Checks and suggests changes to Windows settings for best Valorant experience.
"""

import logging
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a settings check."""
    OPTIMAL = "optimal"       # Setting is at optimal value
    SUBOPTIMAL = "suboptimal" # Could be improved
    CRITICAL = "critical"     # Should be changed for best performance


@dataclass
class SettingCheck:
    """Represents a single setting check result."""
    name: str
    category: str
    status: CheckStatus
    current_value: str
    recommended_value: str
    description: str
    how_to_fix: str
    can_auto_fix: bool = False


class WindowsSettingsChecker:
    """
    Checks Windows settings for optimal gaming performance.
    Provides recommendations and can apply changes if permissions granted.
    """
    
    def __init__(self):
        """Initialize the settings checker."""
        self._checks: List[SettingCheck] = []
        self._is_windows = os.name == 'nt'
    
    def run_all_checks(self) -> List[SettingCheck]:
        """
        Run all Windows settings checks.
        
        Returns:
            List of SettingCheck results
        """
        self._checks = []
        
        if not self._is_windows:
            logger.warning("Windows settings checker only works on Windows")
            return self._checks
        
        # Run each check category
        self._check_power_settings()
        self._check_mouse_settings()
        self._check_game_mode()
        self._check_graphics_settings()
        self._check_network_settings()
        self._check_storage_settings()
        
        return self._checks
    
    def _check_power_settings(self) -> None:
        """Check Windows power plan settings."""
        try:
            # Get current power scheme
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.lower()
            
            is_high_performance = 'high performance' in output or 'ultimate' in output
            
            self._checks.append(SettingCheck(
                name="Power Plan",
                category="Power Settings",
                status=CheckStatus.OPTIMAL if is_high_performance else CheckStatus.CRITICAL,
                current_value="High Performance" if is_high_performance else "Balanced/Power Saver",
                recommended_value="High Performance or Ultimate Performance",
                description="Power plan affects CPU and GPU performance. High Performance ensures your "
                           "hardware runs at maximum capability during gaming.",
                how_to_fix="1. Open Control Panel\n"
                          "2. Go to Hardware and Sound > Power Options\n"
                          "3. Select 'High Performance' or 'Ultimate Performance'\n"
                          "4. If Ultimate Performance is not visible, run in CMD (admin):\n"
                          "   powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
                can_auto_fix=True
            ))
        except Exception as e:
            logger.error(f"Error checking power settings: {e}")
    
    def _check_mouse_settings(self) -> None:
        """Check mouse acceleration settings."""
        try:
            # Check Enhanced Pointer Precision (mouse acceleration)
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Control Panel\Mouse") as key:
                mouse_speed = winreg.QueryValueEx(key, "MouseSpeed")[0]
            
            # MouseSpeed of "0" means acceleration is disabled
            is_disabled = mouse_speed == "0"
            
            self._checks.append(SettingCheck(
                name="Enhanced Pointer Precision (Mouse Acceleration)",
                category="Mouse Settings",
                status=CheckStatus.OPTIMAL if is_disabled else CheckStatus.CRITICAL,
                current_value="Disabled" if is_disabled else "Enabled",
                recommended_value="Disabled",
                description="Mouse acceleration changes cursor speed based on how fast you move the mouse. "
                           "For precise aiming in FPS games, this should be DISABLED for consistent aim.",
                how_to_fix="1. Open Settings > Devices > Mouse\n"
                          "2. Click 'Additional mouse options'\n"
                          "3. Go to 'Pointer Options' tab\n"
                          "4. UNCHECK 'Enhance pointer precision'\n"
                          "5. Click Apply and OK",
                can_auto_fix=True
            ))
        except Exception as e:
            logger.debug(f"Could not check mouse settings: {e}")
            # Add a generic check if we couldn't access registry
            self._checks.append(SettingCheck(
                name="Enhanced Pointer Precision (Mouse Acceleration)",
                category="Mouse Settings",
                status=CheckStatus.SUBOPTIMAL,
                current_value="Unable to detect",
                recommended_value="Disabled",
                description="Mouse acceleration changes cursor speed based on how fast you move the mouse. "
                           "For precise aiming in FPS games, this should be DISABLED for consistent aim.",
                how_to_fix="1. Open Settings > Devices > Mouse\n"
                          "2. Click 'Additional mouse options'\n"
                          "3. Go to 'Pointer Options' tab\n"
                          "4. UNCHECK 'Enhance pointer precision'\n"
                          "5. Click Apply and OK",
                can_auto_fix=False
            ))
    
    def _check_game_mode(self) -> None:
        """Check Windows Game Mode settings."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\GameBar") as key:
                game_mode = winreg.QueryValueEx(key, "AllowAutoGameMode")[0]
        except Exception:
            game_mode = -1  # Unknown
        
        is_enabled = game_mode == 1
        
        self._checks.append(SettingCheck(
            name="Windows Game Mode",
            category="Gaming Settings",
            status=CheckStatus.OPTIMAL if is_enabled else CheckStatus.SUBOPTIMAL,
            current_value="Enabled" if is_enabled else "Disabled/Unknown",
            recommended_value="Enabled",
            description="Game Mode prioritizes gaming performance by limiting background processes "
                       "and preventing Windows Update from running during gameplay.",
            how_to_fix="1. Open Settings\n"
                      "2. Go to Gaming > Game Mode\n"
                      "3. Toggle 'Game Mode' to ON",
            can_auto_fix=True
        ))
    
    def _check_graphics_settings(self) -> None:
        """Check graphics and display settings."""
        self._checks.append(SettingCheck(
            name="Hardware-accelerated GPU scheduling",
            category="Graphics Settings",
            status=CheckStatus.SUBOPTIMAL,
            current_value="Check manually",
            recommended_value="Enabled (if supported)",
            description="HAGS can reduce latency and improve performance by letting your GPU "
                       "manage its own memory. Requires Windows 10 2004+ and compatible GPU.",
            how_to_fix="1. Open Settings > System > Display\n"
                      "2. Click 'Graphics settings'\n"
                      "3. Enable 'Hardware-accelerated GPU scheduling'\n"
                      "4. Restart your PC",
            can_auto_fix=False
        ))
        
        self._checks.append(SettingCheck(
            name="Valorant Graphics Preference",
            category="Graphics Settings",
            status=CheckStatus.SUBOPTIMAL,
            current_value="Check manually",
            recommended_value="High Performance (dedicated GPU)",
            description="Ensure Valorant uses your dedicated GPU instead of integrated graphics "
                       "for best performance.",
            how_to_fix="1. Open Settings > System > Display\n"
                      "2. Click 'Graphics settings'\n"
                      "3. Click 'Browse' and find VALORANT.exe\n"
                      "4. Click 'Options' and select 'High performance'\n"
                      "5. Click 'Save'",
            can_auto_fix=False
        ))
    
    def _check_network_settings(self) -> None:
        """Check network optimization settings."""
        self._checks.append(SettingCheck(
            name="Nagle's Algorithm",
            category="Network Settings",
            status=CheckStatus.SUBOPTIMAL,
            current_value="Check manually",
            recommended_value="Disabled for gaming",
            description="Nagle's Algorithm batches small packets together which can add latency. "
                       "Disabling it for gaming connections can reduce ping.",
            how_to_fix="1. Open Registry Editor (regedit)\n"
                      "2. Navigate to:\n"
                      "   HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\n"
                      "3. Find your network adapter's GUID\n"
                      "4. Create DWORD 'TcpAckFrequency' = 1\n"
                      "5. Create DWORD 'TCPNoDelay' = 1\n"
                      "6. Restart your PC",
            can_auto_fix=False
        ))
    
    def _check_storage_settings(self) -> None:
        """Check storage optimization settings."""
        self._checks.append(SettingCheck(
            name="Game installed on SSD",
            category="Storage Settings",
            status=CheckStatus.SUBOPTIMAL,
            current_value="Check manually",
            recommended_value="Install on SSD/NVMe",
            description="Installing Valorant on an SSD significantly reduces load times and "
                       "prevents stuttering during gameplay.",
            how_to_fix="1. Open Riot Client\n"
                      "2. Go to Settings > Valorant\n"
                      "3. Check install location\n"
                      "4. If on HDD, uninstall and reinstall on SSD",
            can_auto_fix=False
        ))
    
    def apply_fix(self, check_name: str) -> bool:
        """
        Attempt to automatically apply a fix for a setting.
        
        Args:
            check_name: Name of the check to fix
            
        Returns:
            True if fix was applied successfully
        """
        if not self._is_windows:
            return False
        
        for check in self._checks:
            if check.name == check_name and check.can_auto_fix:
                try:
                    if "Power Plan" in check_name:
                        return self._apply_power_fix()
                    elif "Enhanced Pointer Precision" in check_name:
                        return self._apply_mouse_fix()
                    elif "Game Mode" in check_name:
                        return self._apply_game_mode_fix()
                except Exception as e:
                    logger.error(f"Error applying fix for {check_name}: {e}")
        
        return False
    
    def _apply_power_fix(self) -> bool:
        """Apply high performance power plan."""
        try:
            # Set to High Performance
            subprocess.run(
                ['powercfg', '/setactive', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'],
                capture_output=True, timeout=10
            )
            return True
        except Exception:
            return False
    
    def _apply_mouse_fix(self) -> bool:
        """Disable mouse acceleration."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Control Panel\Mouse", 
                               0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "MouseSpeed", 0, winreg.REG_SZ, "0")
                winreg.SetValueEx(key, "MouseThreshold1", 0, winreg.REG_SZ, "0")
                winreg.SetValueEx(key, "MouseThreshold2", 0, winreg.REG_SZ, "0")
            return True
        except Exception:
            return False
    
    def _apply_game_mode_fix(self) -> bool:
        """Enable Windows Game Mode."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\GameBar",
                               0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AllowAutoGameMode", 0, winreg.REG_DWORD, 1)
            return True
        except Exception:
            return False
    
    def get_checks_by_status(self, status: CheckStatus) -> List[SettingCheck]:
        """Get all checks with a specific status."""
        return [c for c in self._checks if c.status == status]
    
    def get_checks_by_category(self, category: str) -> List[SettingCheck]:
        """Get all checks in a specific category."""
        return [c for c in self._checks if c.category == category]
    
    def get_summary(self) -> dict:
        """Get a summary of all checks."""
        return {
            "total": len(self._checks),
            "optimal": len(self.get_checks_by_status(CheckStatus.OPTIMAL)),
            "suboptimal": len(self.get_checks_by_status(CheckStatus.SUBOPTIMAL)),
            "critical": len(self.get_checks_by_status(CheckStatus.CRITICAL)),
        }

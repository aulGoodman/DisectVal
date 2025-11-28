"""
Game launcher with Windows optimization for DisectVal.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from .profiles import GameProfile, GameProfileManager, WindowsSettings

logger = logging.getLogger(__name__)


class GameLauncher:
    """Handles launching games with optimized settings."""
    
    def __init__(self, profile_manager: GameProfileManager):
        self.profile_manager = profile_manager
    
    def apply_windows_settings(self, settings: WindowsSettings) -> bool:
        """Apply Windows settings before launching a game."""
        if os.name != 'nt':
            logger.info("Windows settings only apply on Windows")
            return True
        
        try:
            # Power plan GUIDs
            power_plans = {
                "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
                "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                "ultimate": "e9a42b02-d5df-448d-aa00-03f14749eb61",
            }
            
            if settings.power_plan in power_plans:
                result = subprocess.run(
                    ["powercfg", "/setactive", power_plans[settings.power_plan]],
                    capture_output=True,
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to set power plan: {result.stderr.decode()}")
                else:
                    logger.info(f"Applied power plan: {settings.power_plan}")
            
            return True
        except Exception as e:
            logger.error(f"Error applying Windows settings: {e}")
            return False
    
    def launch_game(self, game_id: str, apply_settings: bool = True) -> bool:
        """Launch a game with optimized settings."""
        profile = self.profile_manager.get_user_game(game_id)
        
        if not profile:
            logger.error(f"Game {game_id} not configured")
            return False
        
        if not profile.executable_path:
            logger.error(f"No executable path set for {game_id}")
            return False
        
        exe_path = Path(profile.executable_path)
        if not exe_path.exists():
            logger.error(f"Executable not found: {exe_path}")
            return False
        
        try:
            if apply_settings:
                self.apply_windows_settings(profile.windows_settings)
            
            # Run pre-launch commands
            for cmd in profile.pre_launch_commands:
                subprocess.run(cmd, shell=True, capture_output=True, check=False)
            
            # Launch game
            args = [str(exe_path)] + profile.launch_args
            subprocess.Popen(args, cwd=exe_path.parent)
            
            logger.info(f"Launched {profile.name}")
            return True
        except Exception as e:
            logger.error(f"Error launching game: {e}")
            return False

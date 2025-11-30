"""
Games module for DisectVal.
Manages game profiles, launchers, and optimization settings.
"""

from .profiles import (
    GameProfile,
    GameProfileManager,
    GameStatus,
    AccessTier,
    WindowsSettings,
    DisplaySettings,
    APPROVED_GAMES,
)
from .launcher import GameLauncher

__all__ = [
    'GameProfile',
    'GameProfileManager',
    'GameLauncher',
    'GameStatus',
    'AccessTier',
    'WindowsSettings',
    'DisplaySettings',
    'APPROVED_GAMES',
]

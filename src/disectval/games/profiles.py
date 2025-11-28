"""
Game profiles and settings for DisectVal.
Manages game-specific configurations and user access tiers.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GameStatus(Enum):
    """Status of a game profile."""
    PUBLIC = "public"           # Available to all users
    TESTING = "testing"         # Available to testers only
    BETA = "beta"               # Available to beta/pro users
    PREMIUM = "premium"         # Requires paid access
    PRIVATE = "private"         # Developer only


class AccessTier(Enum):
    """User access tiers for game features."""
    FREE = "free"               # Basic free access
    AD_FREE = "ad_free"         # $3.99 tier - no ads
    PRO = "pro"                 # $9.99 tier - all features
    TESTER = "tester"           # Special testing access
    DEVELOPER = "developer"     # Full developer access


@dataclass
class WindowsSettings:
    """Windows settings to apply before launching a game."""
    power_plan: str = "high_performance"
    disable_mouse_acceleration: bool = True
    game_mode: bool = True
    gpu_scheduling: bool = True
    disable_fullscreen_optimizations: bool = True
    high_dpi_scaling: str = "application"


@dataclass
class DisplaySettings:
    """Display settings for a game."""
    resolution_width: int = 1920
    resolution_height: int = 1080
    refresh_rate: int = 144
    fullscreen: bool = True
    borderless: bool = False
    vsync: bool = False


@dataclass
class GameProfile:
    """Profile for a supported game."""
    game_id: str
    name: str
    executable_path: str = ""
    icon_path: str = ""
    status: str = GameStatus.PUBLIC.value
    
    # Settings
    windows_settings: WindowsSettings = field(default_factory=WindowsSettings)
    display_settings: DisplaySettings = field(default_factory=DisplaySettings)
    
    # Launch options
    launch_args: List[str] = field(default_factory=list)
    pre_launch_commands: List[str] = field(default_factory=list)
    post_launch_commands: List[str] = field(default_factory=list)
    
    # Feature flags
    features_enabled: Dict[str, bool] = field(default_factory=dict)
    
    # Metadata
    description: str = ""
    supported_features: List[str] = field(default_factory=list)
    required_tier: str = AccessTier.FREE.value


# Preset approved games - only these can be added by users
APPROVED_GAMES: Dict[str, GameProfile] = {
    "valorant": GameProfile(
        game_id="valorant",
        name="Valorant",
        description="Tactical 5v5 shooter by Riot Games",
        status=GameStatus.PUBLIC.value,
        required_tier=AccessTier.FREE.value,
        supported_features=[
            "sensitivity_tracking",
            "crosshair_analysis",
            "position_tracking",
            "aim_training",
            "replay_analysis",
            "pc_optimization",
            "settings_sync"
        ],
        windows_settings=WindowsSettings(
            power_plan="high_performance",
            disable_mouse_acceleration=True,
            game_mode=True,
            gpu_scheduling=True,
        ),
        display_settings=DisplaySettings(
            resolution_width=1920,
            resolution_height=1080,
            refresh_rate=144,
            fullscreen=True,
        ),
    ),
    "csgo2": GameProfile(
        game_id="csgo2",
        name="Counter-Strike 2",
        description="Tactical shooter by Valve",
        status=GameStatus.TESTING.value,
        required_tier=AccessTier.FREE.value,
        supported_features=[
            "sensitivity_tracking",
            "crosshair_analysis",
            "position_tracking",
            "aim_training",
        ],
    ),
    "apex": GameProfile(
        game_id="apex",
        name="Apex Legends",
        description="Battle royale by Respawn Entertainment",
        status=GameStatus.BETA.value,
        required_tier=AccessTier.PRO.value,
        supported_features=[
            "sensitivity_tracking",
            "position_tracking",
            "aim_training",
        ],
    ),
    "overwatch2": GameProfile(
        game_id="overwatch2",
        name="Overwatch 2",
        description="Team-based hero shooter by Blizzard",
        status=GameStatus.BETA.value,
        required_tier=AccessTier.PRO.value,
        supported_features=[
            "sensitivity_tracking",
            "aim_training",
        ],
    ),
    "fortnite": GameProfile(
        game_id="fortnite",
        name="Fortnite",
        description="Battle royale by Epic Games",
        status=GameStatus.PRIVATE.value,
        required_tier=AccessTier.DEVELOPER.value,
        supported_features=["sensitivity_tracking"],
    ),
}


class GameProfileManager:
    """Manages game profiles and user configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the game profile manager."""
        if config_dir is None:
            if os.name == 'nt':
                base = Path(os.environ.get('LOCALAPPDATA', ''))
            else:
                base = Path.home() / '.local' / 'share'
            config_dir = base / 'DisectVal' / 'games'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.user_games_file = self.config_dir / 'user_games.json'
        
        self.user_games: Dict[str, GameProfile] = self._load_user_games()
    
    def _load_user_games(self) -> Dict[str, GameProfile]:
        """Load user's game configurations."""
        if self.user_games_file.exists():
            try:
                with open(self.user_games_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                games = {}
                for game_id, game_data in data.items():
                    if 'windows_settings' in game_data:
                        game_data['windows_settings'] = WindowsSettings(**game_data['windows_settings'])
                    if 'display_settings' in game_data:
                        game_data['display_settings'] = DisplaySettings(**game_data['display_settings'])
                    games[game_id] = GameProfile(**game_data)
                return games
            except Exception as e:
                logger.warning(f"Error loading user games: {e}")
        return {}
    
    def _save_user_games(self) -> None:
        """Save user's game configurations."""
        try:
            data = {gid: asdict(p) for gid, p in self.user_games.items()}
            with open(self.user_games_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user games: {e}")
    
    def get_available_games(
        self,
        user_tier: AccessTier,
        is_tester: bool = False,
        is_developer: bool = False
    ) -> List[GameProfile]:
        """Get games available to a user based on access tier."""
        available = []
        tier_order = [AccessTier.FREE, AccessTier.AD_FREE, AccessTier.PRO, AccessTier.TESTER, AccessTier.DEVELOPER]
        
        for game_id, profile in APPROVED_GAMES.items():
            status = GameStatus(profile.status)
            required_tier = AccessTier(profile.required_tier)
            
            if is_developer:
                available.append(profile)
                continue
            
            if status == GameStatus.PRIVATE:
                continue
            if status == GameStatus.TESTING and not is_tester:
                continue
            if status == GameStatus.BETA and user_tier not in [AccessTier.PRO, AccessTier.DEVELOPER] and not is_tester:
                continue
            
            if tier_order.index(user_tier) >= tier_order.index(required_tier):
                available.append(profile)
        
        return available
    
    def add_game(self, game_id: str, executable_path: str = "") -> bool:
        """Add an approved game to user's configuration."""
        if game_id not in APPROVED_GAMES:
            return False
        
        profile = GameProfile(**asdict(APPROVED_GAMES[game_id]))
        profile.executable_path = executable_path
        self.user_games[game_id] = profile
        self._save_user_games()
        return True
    
    def remove_game(self, game_id: str) -> bool:
        """Remove a game from user's configuration."""
        if game_id in self.user_games:
            del self.user_games[game_id]
            self._save_user_games()
            return True
        return False
    
    def get_user_game(self, game_id: str) -> Optional[GameProfile]:
        """Get user's configuration for a game."""
        return self.user_games.get(game_id)
    
    def update_game_settings(
        self,
        game_id: str,
        windows_settings: Optional[WindowsSettings] = None,
        display_settings: Optional[DisplaySettings] = None,
    ) -> bool:
        """Update settings for a configured game."""
        if game_id not in self.user_games:
            return False
        
        profile = self.user_games[game_id]
        if windows_settings:
            profile.windows_settings = windows_settings
        if display_settings:
            profile.display_settings = display_settings
        
        self._save_user_games()
        return True

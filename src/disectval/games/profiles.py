"""
Game profiles and settings for DisectVal.
Manages game-specific configurations and user access tiers.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
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


class GameCategory(Enum):
    """Category of game for different features."""
    FPS_COMPETITIVE = "fps_competitive"     # Valorant, CS2, etc
    FPS_BATTLE_ROYALE = "fps_battle_royale"  # Apex, Fortnite
    AUTOMATION = "automation"               # Roblox, etc
    MOBA = "moba"                           # League, Dota
    OTHER = "other"


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
class GameUsageStats:
    """Track usage statistics for sorting games."""
    total_sessions: int = 0
    total_time_minutes: int = 0
    last_used: str = ""  # ISO format timestamp


@dataclass
class GameProfile:
    """Profile for a supported game."""
    game_id: str
    name: str
    executable_path: str = ""
    icon_path: str = ""
    status: str = GameStatus.PUBLIC.value
    category: str = GameCategory.OTHER.value
    
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
    short_description: str = ""
    supported_features: List[str] = field(default_factory=list)
    required_tier: str = AccessTier.FREE.value
    
    # Usage tracking
    usage_stats: GameUsageStats = field(default_factory=GameUsageStats)


# Preset approved games - only these can be added by users
APPROVED_GAMES: Dict[str, GameProfile] = {
    "valorant": GameProfile(
        game_id="valorant",
        name="Valorant",
        description="AI-powered coaching for Valorant. Get real-time insights, gameplay advice, "
                    "sensitivity optimization, crosshair analysis, and personalized tips to improve your rank.",
        short_description="Tactical 5v5 shooter by Riot Games",
        category=GameCategory.FPS_COMPETITIVE.value,
        status=GameStatus.PUBLIC.value,
        required_tier=AccessTier.FREE.value,
        supported_features=[
            "coaching",              # Real-time coaching and tips
            "sensitivity_tracking",  # Mouse sensitivity analysis
            "crosshair_analysis",    # Crosshair placement feedback
            "position_tracking",     # Movement and positioning advice
            "aim_training",          # Aim improvement exercises
            "replay_analysis",       # Post-game replay analysis
            "pc_optimization",       # Windows settings for Valorant
            "settings_sync",         # Sync in-game settings
            "warmup_routines",       # Pre-game warmup suggestions
            "rank_improvement",      # Tips to climb ranks
        ],
        windows_settings=WindowsSettings(
            power_plan="high_performance",
            disable_mouse_acceleration=True,
            game_mode=True,
            gpu_scheduling=True,
            disable_fullscreen_optimizations=True,
        ),
        display_settings=DisplaySettings(
            resolution_width=1920,
            resolution_height=1080,
            refresh_rate=144,
            fullscreen=True,
        ),
    ),
    "roblox": GameProfile(
        game_id="roblox",
        name="Roblox",
        description="Smart automation and rate verification for Roblox. Automate repetitive tasks, "
                    "calculate real drop rates, verify creator claims, run overnight automation, "
                    "and search the web for solutions to common problems.",
        short_description="Gaming platform by Roblox Corporation",
        category=GameCategory.AUTOMATION.value,
        status=GameStatus.PUBLIC.value,
        required_tier=AccessTier.FREE.value,
        supported_features=[
            "task_automation",       # Automate repetitive tasks
            "rate_calculator",       # Calculate actual drop/spawn rates
            "rate_verification",     # Verify if creator claims are accurate
            "overnight_automation",  # Run automation while you sleep
            "web_search",            # Search for fixes to common problems
            "macro_recorder",        # Record and replay actions
            "script_detection",      # Detect when games have issues
            "afk_prevention",        # Keep account active
            "multi_instance",        # Run multiple accounts
            "smart_decisions",       # AI makes smart choices
        ],
        windows_settings=WindowsSettings(
            power_plan="balanced",  # Save power for overnight
            disable_mouse_acceleration=False,
            game_mode=False,  # Not needed for automation
            gpu_scheduling=False,
        ),
        display_settings=DisplaySettings(
            resolution_width=1280,
            resolution_height=720,
            refresh_rate=60,
            fullscreen=False,
            borderless=True,  # Better for automation
        ),
    ),
    "csgo2": GameProfile(
        game_id="csgo2",
        name="Counter-Strike 2",
        description="Competitive FPS coaching with aim analysis and positioning feedback.",
        short_description="Tactical shooter by Valve",
        category=GameCategory.FPS_COMPETITIVE.value,
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
        description="Battle royale performance tracking and movement analysis.",
        short_description="Battle royale by Respawn Entertainment",
        category=GameCategory.FPS_BATTLE_ROYALE.value,
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
        description="Hero shooter optimization and aim training.",
        short_description="Team-based hero shooter by Blizzard",
        category=GameCategory.FPS_COMPETITIVE.value,
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
        description="Battle royale building and combat analysis.",
        short_description="Battle royale by Epic Games",
        category=GameCategory.FPS_BATTLE_ROYALE.value,
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
                    if 'usage_stats' in game_data:
                        game_data['usage_stats'] = GameUsageStats(**game_data['usage_stats'])
                    else:
                        game_data['usage_stats'] = GameUsageStats()
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
    
    def get_games_sorted_by_usage(
        self,
        user_tier: AccessTier,
        is_tester: bool = False,
        is_developer: bool = False
    ) -> List[GameProfile]:
        """Get games sorted by usage (most used first, then by last used)."""
        available = self.get_available_games(user_tier, is_tester, is_developer)
        
        def sort_key(profile: GameProfile) -> tuple:
            # Get user's stats if configured
            user_profile = self.user_games.get(profile.game_id)
            if user_profile and user_profile.usage_stats:
                stats = user_profile.usage_stats
                # Sort by: total sessions (desc), last used (desc)
                last_used_str = stats.last_used or "1970-01-01T00:00:00"
                try:
                    last_used_ts = datetime.fromisoformat(last_used_str).timestamp()
                except ValueError:
                    last_used_ts = 0
                return (-stats.total_sessions, -stats.total_time_minutes, -last_used_ts)
            return (0, 0, 0)
        
        return sorted(available, key=sort_key)
    
    def record_game_session(self, game_id: str, duration_minutes: int = 0) -> None:
        """Record a game session for usage tracking."""
        if game_id not in self.user_games:
            return
        
        profile = self.user_games[game_id]
        profile.usage_stats.total_sessions += 1
        profile.usage_stats.total_time_minutes += duration_minutes
        profile.usage_stats.last_used = datetime.now().isoformat()
        self._save_user_games()
    
    def add_game(self, game_id: str, executable_path: str = "") -> bool:
        """Add an approved game to user's configuration."""
        if game_id not in APPROVED_GAMES:
            return False
        
        profile = GameProfile(**asdict(APPROVED_GAMES[game_id]))
        profile.executable_path = executable_path
        # Initialize usage stats
        profile.usage_stats = GameUsageStats()
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

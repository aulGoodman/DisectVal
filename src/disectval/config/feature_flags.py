"""
Feature flags system for DisectVal.
Controls which features are visible/enabled for specific users.
Allows developers to hide features and grant access through admin panel.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Feature:
    """Definition of a feature that can be toggled."""
    feature_id: str
    name: str
    description: str
    category: str = "general"
    hidden: bool = False           # If True, only visible to granted users
    enabled_by_default: bool = True
    requires_tier: str = "free"    # Minimum tier required
    granted_users: List[str] = field(default_factory=list)  # Specific users granted access


# All features in the application
FEATURES: Dict[str, Feature] = {
    # Core features - visible to all
    "home_dashboard": Feature(
        feature_id="home_dashboard",
        name="Home Dashboard",
        description="Main dashboard with overview",
        category="core",
        hidden=False,
        enabled_by_default=True,
    ),
    "pc_check": Feature(
        feature_id="pc_check",
        name="PC Optimization Check",
        description="Analyze and optimize Windows settings",
        category="core",
        hidden=False,
        enabled_by_default=True,
    ),
    
    # Game features
    "game_profiles": Feature(
        feature_id="game_profiles",
        name="Game Profiles",
        description="Manage game-specific settings",
        category="games",
        hidden=False,
        enabled_by_default=True,
    ),
    "game_launcher": Feature(
        feature_id="game_launcher",
        name="Game Launcher",
        description="Launch games with optimized settings",
        category="games",
        hidden=False,
        enabled_by_default=True,
    ),
    
    # Analysis features
    "sensitivity_tracking": Feature(
        feature_id="sensitivity_tracking",
        name="Sensitivity Tracking",
        description="Track and analyze mouse sensitivity",
        category="analysis",
        hidden=False,
        enabled_by_default=True,
    ),
    "aim_analysis": Feature(
        feature_id="aim_analysis",
        name="Aim Analysis",
        description="Analyze aim patterns and accuracy",
        category="analysis",
        hidden=False,
        enabled_by_default=True,
        requires_tier="pro",
    ),
    "replay_analysis": Feature(
        feature_id="replay_analysis",
        name="Replay Analysis",
        description="AI-powered replay analysis",
        category="analysis",
        hidden=False,
        enabled_by_default=True,
        requires_tier="pro",
    ),
    
    # Hidden/Developer features - only SGM and granted users
    "ai_training_panel": Feature(
        feature_id="ai_training_panel",
        name="AI Training Panel",
        description="Train the AI with gameplay footage",
        category="developer",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
    "screen_detection": Feature(
        feature_id="screen_detection",
        name="Screen Detection AI",
        description="AI that detects what's on screen",
        category="developer",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
    "website_sync": Feature(
        feature_id="website_sync",
        name="Website Account Sync",
        description="Sync accounts between app and website",
        category="developer",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
    "user_management": Feature(
        feature_id="user_management",
        name="User Management",
        description="Manage users and permissions",
        category="admin",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
    "feature_flags_panel": Feature(
        feature_id="feature_flags_panel",
        name="Feature Flags Panel",
        description="Control feature visibility for users",
        category="admin",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
    "download_manager": Feature(
        feature_id="download_manager",
        name="Download Version Manager",
        description="Manage downloadable versions for website",
        category="admin",
        hidden=True,
        enabled_by_default=False,
        requires_tier="developer",
        granted_users=["SGM"],
    ),
}


class FeatureFlagsManager:
    """Manages feature flags and user access."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the feature flags manager."""
        if config_dir is None:
            if os.name == 'nt':
                base = Path(os.environ.get('LOCALAPPDATA', ''))
            else:
                base = Path.home() / '.local' / 'share'
            config_dir = base / 'DisectVal'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.flags_file = self.config_dir / 'feature_flags.json'
        
        # Load custom flags (overrides defaults)
        self.custom_flags: Dict[str, dict] = self._load_custom_flags()
    
    def _load_custom_flags(self) -> Dict[str, dict]:
        """Load custom feature flag overrides."""
        if self.flags_file.exists():
            try:
                with open(self.flags_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading feature flags: {e}")
        return {}
    
    def _save_custom_flags(self) -> None:
        """Save custom feature flag overrides."""
        try:
            with open(self.flags_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_flags, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feature flags: {e}")
    
    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """Get a feature by ID with any custom overrides applied."""
        if feature_id not in FEATURES:
            return None
        
        feature = Feature(**asdict(FEATURES[feature_id]))
        
        # Apply custom overrides
        if feature_id in self.custom_flags:
            overrides = self.custom_flags[feature_id]
            if 'granted_users' in overrides:
                feature.granted_users = overrides['granted_users']
            if 'hidden' in overrides:
                feature.hidden = overrides['hidden']
            if 'enabled_by_default' in overrides:
                feature.enabled_by_default = overrides['enabled_by_default']
        
        return feature
    
    def is_feature_visible(self, feature_id: str, username: str, user_tier: str) -> bool:
        """
        Check if a feature is visible to a specific user.
        
        Args:
            feature_id: The feature to check
            username: The user's username
            user_tier: The user's access tier
            
        Returns:
            True if the feature should be visible to this user
        """
        feature = self.get_feature(feature_id)
        if not feature:
            return False
        
        # If not hidden, check tier requirement
        if not feature.hidden:
            tier_order = ["free", "ad_free", "pro", "tester", "developer"]
            if user_tier not in tier_order:
                user_tier = "free"
            if tier_order.index(user_tier) >= tier_order.index(feature.requires_tier):
                return True
            return False
        
        # Hidden features - check if user is specifically granted
        if username in feature.granted_users:
            return True
        
        # Developers can see all hidden features
        if user_tier == "developer":
            return True
        
        return False
    
    def get_visible_features(self, username: str, user_tier: str) -> List[Feature]:
        """Get all features visible to a user."""
        visible = []
        for feature_id in FEATURES:
            if self.is_feature_visible(feature_id, username, user_tier):
                feature = self.get_feature(feature_id)
                if feature:
                    visible.append(feature)
        return visible
    
    def grant_feature_access(self, feature_id: str, username: str) -> bool:
        """Grant a user access to a hidden feature."""
        if feature_id not in FEATURES:
            return False
        
        if feature_id not in self.custom_flags:
            self.custom_flags[feature_id] = {'granted_users': []}
        
        if 'granted_users' not in self.custom_flags[feature_id]:
            self.custom_flags[feature_id]['granted_users'] = list(FEATURES[feature_id].granted_users)
        
        if username not in self.custom_flags[feature_id]['granted_users']:
            self.custom_flags[feature_id]['granted_users'].append(username)
            self._save_custom_flags()
        
        return True
    
    def revoke_feature_access(self, feature_id: str, username: str) -> bool:
        """Revoke a user's access to a hidden feature."""
        if feature_id not in self.custom_flags:
            return False
        
        if 'granted_users' in self.custom_flags[feature_id]:
            if username in self.custom_flags[feature_id]['granted_users']:
                self.custom_flags[feature_id]['granted_users'].remove(username)
                self._save_custom_flags()
                return True
        
        return False
    
    def set_feature_hidden(self, feature_id: str, hidden: bool) -> bool:
        """Set whether a feature is hidden."""
        if feature_id not in FEATURES:
            return False
        
        if feature_id not in self.custom_flags:
            self.custom_flags[feature_id] = {}
        
        self.custom_flags[feature_id]['hidden'] = hidden
        self._save_custom_flags()
        return True
    
    def get_all_features_for_admin(self) -> List[Feature]:
        """Get all features for admin panel (including hidden)."""
        return [self.get_feature(fid) for fid in FEATURES if self.get_feature(fid)]


# Global instance
_flags_manager: Optional[FeatureFlagsManager] = None


def get_flags_manager() -> FeatureFlagsManager:
    """Get the global feature flags manager instance."""
    global _flags_manager
    if _flags_manager is None:
        _flags_manager = FeatureFlagsManager()
    return _flags_manager

"""
Subscription plans and pricing for DisectVal.
Manages user subscription tiers and feature access.
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


class PlanType(Enum):
    """Available subscription plans."""
    FREE = "free"           # Free tier - basic features
    BASIC = "basic"         # $3.99/month - no ads, some features
    PRO = "pro"             # $9.99/month - all features, no ads


@dataclass
class PlanFeature:
    """A feature included in a plan."""
    feature_id: str
    name: str
    description: str
    included: bool = True
    limited: bool = False   # If True, feature has usage limits
    limit_value: int = 0    # Usage limit if limited


@dataclass
class SubscriptionPlan:
    """Definition of a subscription plan."""
    plan_id: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    currency: str = "USD"
    
    # Features included
    features: List[PlanFeature] = field(default_factory=list)
    
    # Limits
    max_games: int = -1         # -1 = unlimited
    has_ads: bool = True
    priority_support: bool = False
    
    # Display
    highlight: bool = False     # Highlight as recommended
    badge: str = ""             # e.g., "POPULAR", "BEST VALUE"


# Define all subscription plans
SUBSCRIPTION_PLANS: Dict[str, SubscriptionPlan] = {
    "free": SubscriptionPlan(
        plan_id="free",
        name="Free",
        description="Get started with basic features",
        price_monthly=0.0,
        price_yearly=0.0,
        has_ads=True,
        max_games=2,
        priority_support=False,
        features=[
            PlanFeature("basic_coaching", "Basic Coaching", "Simple tips and advice", True),
            PlanFeature("pc_optimization", "PC Optimization", "Basic Windows settings check", True),
            PlanFeature("game_profiles", "Game Profiles", "Configure up to 2 games", True, True, 2),
            PlanFeature("sensitivity_tracking", "Sensitivity Tracking", "Track mouse sensitivity", True),
            PlanFeature("ads", "Ads", "Includes advertisements", True),
        ],
    ),
    "basic": SubscriptionPlan(
        plan_id="basic",
        name="Basic",
        description="Remove ads and unlock more features",
        price_monthly=3.99,
        price_yearly=39.99,
        has_ads=False,
        max_games=5,
        priority_support=False,
        highlight=False,
        badge="",
        features=[
            PlanFeature("basic_coaching", "Basic Coaching", "Simple tips and advice", True),
            PlanFeature("advanced_coaching", "Advanced Coaching", "Detailed gameplay insights", True),
            PlanFeature("pc_optimization", "PC Optimization", "Full Windows settings optimization", True),
            PlanFeature("game_profiles", "Game Profiles", "Configure up to 5 games", True, True, 5),
            PlanFeature("sensitivity_tracking", "Sensitivity Tracking", "Track mouse sensitivity", True),
            PlanFeature("crosshair_analysis", "Crosshair Analysis", "Analyze crosshair placement", True),
            PlanFeature("no_ads", "Ad-Free", "No advertisements", True),
        ],
    ),
    "pro": SubscriptionPlan(
        plan_id="pro",
        name="Pro",
        description="Unlock all features with no limits",
        price_monthly=9.99,
        price_yearly=99.99,
        has_ads=False,
        max_games=-1,  # Unlimited
        priority_support=True,
        highlight=True,
        badge="BEST VALUE",
        features=[
            PlanFeature("basic_coaching", "Basic Coaching", "Simple tips and advice", True),
            PlanFeature("advanced_coaching", "Advanced Coaching", "Detailed gameplay insights", True),
            PlanFeature("ai_coaching", "AI Coaching", "Real-time AI-powered coaching", True),
            PlanFeature("pc_optimization", "PC Optimization", "Full Windows settings optimization", True),
            PlanFeature("game_profiles", "Unlimited Games", "Configure unlimited games", True),
            PlanFeature("sensitivity_tracking", "Sensitivity Tracking", "Track mouse sensitivity", True),
            PlanFeature("crosshair_analysis", "Crosshair Analysis", "Analyze crosshair placement", True),
            PlanFeature("aim_training", "Aim Training", "Personalized aim training", True),
            PlanFeature("replay_analysis", "Replay Analysis", "AI-powered replay analysis", True),
            PlanFeature("automation", "Automation Tools", "Task automation for Roblox", True),
            PlanFeature("overnight_automation", "Overnight Mode", "Run automation overnight", True),
            PlanFeature("no_ads", "Ad-Free", "No advertisements", True),
            PlanFeature("priority_support", "Priority Support", "Fast response times", True),
        ],
    ),
}


@dataclass
class UserSubscription:
    """A user's subscription status."""
    user_id: str
    plan_id: str = "free"
    is_active: bool = True
    started_at: str = ""
    expires_at: str = ""
    billing_cycle: str = "monthly"  # monthly or yearly
    auto_renew: bool = False
    payment_method: str = ""


class SubscriptionManager:
    """Manages user subscriptions."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the subscription manager."""
        if config_dir is None:
            if os.name == 'nt':
                base = Path(os.environ.get('LOCALAPPDATA', ''))
            else:
                base = Path.home() / '.local' / 'share'
            config_dir = base / 'DisectVal'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.subscription_file = self.config_dir / 'subscription.json'
        
        self.subscription: Optional[UserSubscription] = self._load_subscription()
    
    def _load_subscription(self) -> Optional[UserSubscription]:
        """Load user's subscription from file."""
        if self.subscription_file.exists():
            try:
                with open(self.subscription_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UserSubscription(**data)
            except Exception as e:
                logger.warning(f"Error loading subscription: {e}")
        return None
    
    def _save_subscription(self) -> None:
        """Save user's subscription to file."""
        if self.subscription:
            try:
                with open(self.subscription_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.subscription), f, indent=2)
            except Exception as e:
                logger.error(f"Error saving subscription: {e}")
    
    def get_current_plan(self) -> SubscriptionPlan:
        """Get the user's current subscription plan."""
        if self.subscription and self.subscription.is_active:
            plan_id = self.subscription.plan_id
            if plan_id in SUBSCRIPTION_PLANS:
                return SUBSCRIPTION_PLANS[plan_id]
        return SUBSCRIPTION_PLANS["free"]
    
    def get_plan_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a plan by its ID."""
        return SUBSCRIPTION_PLANS.get(plan_id)
    
    def get_all_plans(self) -> List[SubscriptionPlan]:
        """Get all available subscription plans."""
        return list(SUBSCRIPTION_PLANS.values())
    
    def is_feature_available(self, feature_id: str) -> bool:
        """Check if a feature is available in the user's current plan."""
        plan = self.get_current_plan()
        for feature in plan.features:
            if feature.feature_id == feature_id and feature.included:
                return True
        return False
    
    def get_feature_limit(self, feature_id: str) -> int:
        """Get the limit for a feature (-1 = unlimited)."""
        plan = self.get_current_plan()
        for feature in plan.features:
            if feature.feature_id == feature_id:
                if feature.limited:
                    return feature.limit_value
                return -1  # Unlimited
        return 0  # Feature not available
    
    def has_ads(self) -> bool:
        """Check if the user's plan shows ads."""
        return self.get_current_plan().has_ads
    
    def can_add_more_games(self, current_count: int) -> bool:
        """Check if the user can add more games."""
        plan = self.get_current_plan()
        if plan.max_games == -1:
            return True
        return current_count < plan.max_games
    
    def change_plan(self, plan_id: str, user_id: str) -> bool:
        """
        Change to a different plan.
        
        Note: This is a placeholder for actual payment integration.
        In production, upgrades would require payment processing
        and downgrades would handle proration/refunds.
        """
        if plan_id not in SUBSCRIPTION_PLANS:
            return False
        
        # In real implementation, this would integrate with payment provider
        self.subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            is_active=True,
            started_at=datetime.now().isoformat(),
            expires_at="",  # Would be set based on billing cycle
            billing_cycle="monthly",
            auto_renew=True,
        )
        self._save_subscription()
        return True
    
    def upgrade_plan(self, plan_id: str, user_id: str) -> bool:
        """Upgrade to a higher tier plan."""
        if plan_id not in SUBSCRIPTION_PLANS:
            return False
        
        # Define tier order for validation
        tier_order = ["free", "basic", "pro"]
        current = self.get_current_plan().plan_id
        
        current_idx = tier_order.index(current) if current in tier_order else 0
        new_idx = tier_order.index(plan_id) if plan_id in tier_order else 0
        
        # Only allow actual upgrades
        if new_idx <= current_idx:
            return False
        
        return self.change_plan(plan_id, user_id)
    
    def cancel_subscription(self) -> bool:
        """Cancel the current subscription."""
        if self.subscription:
            self.subscription.auto_renew = False
            self._save_subscription()
            return True
        return False


# Global instance
_subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get the global subscription manager instance."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager

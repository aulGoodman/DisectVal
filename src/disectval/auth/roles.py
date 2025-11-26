"""
User roles and permissions for DisectVal.
Defines access levels and what each role can do.
"""

from enum import Enum
from typing import Set


class UserRole(Enum):
    """User role enumeration."""
    USER = "user"           # Basic user - default perms
    ADMIN = "admin"         # Admin access - can view admin features
    DEVELOPER = "developer" # Full dev access - all perms including training


class Permission(Enum):
    """Available permissions in the application."""
    # Basic permissions
    VIEW_HOME = "view_home"
    VIEW_CAREER = "view_career"
    VIEW_RANKED = "view_ranked"
    VIEW_AI_SUMMARY = "view_ai_summary"
    
    # Analysis permissions
    START_ANALYSIS = "start_analysis"
    VIEW_CLIPS = "view_clips"
    EXPORT_DATA = "export_data"
    
    # Settings permissions
    VIEW_PC_CHECK = "view_pc_check"
    MODIFY_SETTINGS = "modify_settings"
    
    # Admin permissions
    VIEW_ADMIN_TAB = "view_admin_tab"
    MANAGE_USERS = "manage_users"
    VIEW_ALL_VERSIONS = "view_all_versions"
    
    # Developer permissions
    IMPORT_TRAINING_DATA = "import_training_data"
    TRAIN_AI = "train_ai"
    ACCESS_DEBUG = "access_debug"
    BYPASS_VALORANT_CHECK = "bypass_valorant_check"
    SYNC_TRAINING_DATA = "sync_training_data"


# Define permissions for each role
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.USER: {
        Permission.VIEW_HOME,
        Permission.VIEW_CAREER,
        Permission.VIEW_RANKED,
        Permission.VIEW_AI_SUMMARY,
        Permission.START_ANALYSIS,
        Permission.VIEW_CLIPS,
        Permission.VIEW_PC_CHECK,
    },
    UserRole.ADMIN: {
        # All user permissions
        Permission.VIEW_HOME,
        Permission.VIEW_CAREER,
        Permission.VIEW_RANKED,
        Permission.VIEW_AI_SUMMARY,
        Permission.START_ANALYSIS,
        Permission.VIEW_CLIPS,
        Permission.VIEW_PC_CHECK,
        Permission.EXPORT_DATA,
        Permission.MODIFY_SETTINGS,
        # Admin specific
        Permission.VIEW_ADMIN_TAB,
        Permission.MANAGE_USERS,
        Permission.VIEW_ALL_VERSIONS,
    },
    UserRole.DEVELOPER: {
        # All permissions
        Permission.VIEW_HOME,
        Permission.VIEW_CAREER,
        Permission.VIEW_RANKED,
        Permission.VIEW_AI_SUMMARY,
        Permission.START_ANALYSIS,
        Permission.VIEW_CLIPS,
        Permission.VIEW_PC_CHECK,
        Permission.EXPORT_DATA,
        Permission.MODIFY_SETTINGS,
        Permission.VIEW_ADMIN_TAB,
        Permission.MANAGE_USERS,
        Permission.VIEW_ALL_VERSIONS,
        # Developer specific
        Permission.IMPORT_TRAINING_DATA,
        Permission.TRAIN_AI,
        Permission.ACCESS_DEBUG,
        Permission.BYPASS_VALORANT_CHECK,
        Permission.SYNC_TRAINING_DATA,
    },
}


class PermissionManager:
    """Manages user permissions based on roles."""
    
    def __init__(self, role: UserRole):
        """
        Initialize permission manager for a user role.
        
        Args:
            role: The user's role
        """
        self.role = role
        self._permissions = ROLE_PERMISSIONS.get(role, set())
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if the user has a specific permission.
        
        Args:
            permission: The permission to check
            
        Returns:
            True if user has the permission
        """
        return permission in self._permissions
    
    def get_all_permissions(self) -> Set[Permission]:
        """Get all permissions for the current role."""
        return self._permissions.copy()
    
    def is_developer(self) -> bool:
        """Check if user has developer role."""
        return self.role == UserRole.DEVELOPER
    
    def is_admin(self) -> bool:
        """Check if user has admin role or higher."""
        return self.role in (UserRole.ADMIN, UserRole.DEVELOPER)
    
    def can_access_admin_features(self) -> bool:
        """Check if user can access admin tab and features."""
        return self.has_permission(Permission.VIEW_ADMIN_TAB)
    
    def can_train_ai(self) -> bool:
        """Check if user can import training data and train the AI."""
        return self.has_permission(Permission.TRAIN_AI)
    
    def can_bypass_valorant_check(self) -> bool:
        """Check if user can allow input while Valorant is active."""
        return self.has_permission(Permission.BYPASS_VALORANT_CHECK)

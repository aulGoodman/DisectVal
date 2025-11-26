"""
Tests for the authentication module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from disectval.auth.credentials import CredentialManager
from disectval.auth.roles import Permission, PermissionManager, UserRole


class TestCredentialManager:
    """Tests for CredentialManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def cred_manager(self, temp_dir):
        """Create a CredentialManager with temporary storage."""
        return CredentialManager(data_dir=temp_dir)
    
    def test_init_creates_default_users(self, cred_manager):
        """Test that default users are created on initialization."""
        # SGM user should exist
        sgm_role = cred_manager.get_user_role('SGM')
        assert sgm_role == UserRole.DEVELOPER
        
        # RIOT user should exist
        riot_role = cred_manager.get_user_role('RIOT')
        assert riot_role == UserRole.ADMIN
    
    def test_authenticate_valid_sgm(self, cred_manager):
        """Test authentication with valid SGM credentials."""
        result = cred_manager.authenticate('SGM', 'sgmtm123')
        assert result is not None
        assert result['username'] == 'SGM'
        assert result['role'] == UserRole.DEVELOPER
        assert result['valorant_input_allowed'] is True
    
    def test_authenticate_valid_riot(self, cred_manager):
        """Test authentication with valid RIOT credentials."""
        result = cred_manager.authenticate('RIOT', 'RIOTACESS12481924')
        assert result is not None
        assert result['username'] == 'RIOT'
        assert result['role'] == UserRole.ADMIN
        assert result['valorant_input_allowed'] is False
    
    def test_authenticate_invalid_password(self, cred_manager):
        """Test authentication with invalid password."""
        result = cred_manager.authenticate('SGM', 'wrongpassword')
        assert result is None
    
    def test_authenticate_invalid_username(self, cred_manager):
        """Test authentication with non-existent username."""
        result = cred_manager.authenticate('nonexistent', 'password')
        assert result is None
    
    def test_add_user(self, cred_manager):
        """Test adding a new user."""
        success = cred_manager.add_user(
            username='testuser',
            password='testpass123',
            role=UserRole.USER
        )
        assert success is True
        
        # Verify user can authenticate
        result = cred_manager.authenticate('testuser', 'testpass123')
        assert result is not None
        assert result['role'] == UserRole.USER
    
    def test_add_duplicate_user(self, cred_manager):
        """Test that adding a duplicate user fails."""
        # SGM already exists
        success = cred_manager.add_user(
            username='SGM',
            password='newpassword',
            role=UserRole.USER
        )
        assert success is False
    
    def test_change_password(self, cred_manager):
        """Test changing a user's password."""
        # Add a test user first
        cred_manager.add_user('testuser', 'oldpass', UserRole.USER)
        
        # Change password
        success = cred_manager.change_password('testuser', 'oldpass', 'newpass')
        assert success is True
        
        # Old password should no longer work
        assert cred_manager.authenticate('testuser', 'oldpass') is None
        
        # New password should work
        result = cred_manager.authenticate('testuser', 'newpass')
        assert result is not None
    
    def test_change_password_wrong_old(self, cred_manager):
        """Test that changing password with wrong old password fails."""
        cred_manager.add_user('testuser', 'correctpass', UserRole.USER)
        
        success = cred_manager.change_password('testuser', 'wrongpass', 'newpass')
        assert success is False
    
    def test_delete_user(self, cred_manager):
        """Test deleting a user."""
        cred_manager.add_user('deleteme', 'password', UserRole.USER)
        
        success = cred_manager.delete_user('deleteme')
        assert success is True
        
        # User should no longer exist
        assert cred_manager.get_user_role('deleteme') is None
    
    def test_delete_protected_users(self, cred_manager):
        """Test that SGM and RIOT cannot be deleted."""
        assert cred_manager.delete_user('SGM') is False
        assert cred_manager.delete_user('RIOT') is False
        
        # They should still exist
        assert cred_manager.get_user_role('SGM') is not None
        assert cred_manager.get_user_role('RIOT') is not None


class TestPermissionManager:
    """Tests for PermissionManager."""
    
    def test_developer_has_all_permissions(self):
        """Test that developer role has all permissions."""
        pm = PermissionManager(UserRole.DEVELOPER)
        
        # Check some key permissions
        assert pm.has_permission(Permission.VIEW_HOME)
        assert pm.has_permission(Permission.TRAIN_AI)
        assert pm.has_permission(Permission.BYPASS_VALORANT_CHECK)
        assert pm.has_permission(Permission.MANAGE_USERS)
        assert pm.has_permission(Permission.VIEW_ADMIN_TAB)
    
    def test_admin_permissions(self):
        """Test admin role permissions."""
        pm = PermissionManager(UserRole.ADMIN)
        
        # Should have
        assert pm.has_permission(Permission.VIEW_HOME)
        assert pm.has_permission(Permission.VIEW_ADMIN_TAB)
        assert pm.has_permission(Permission.MANAGE_USERS)
        
        # Should not have
        assert not pm.has_permission(Permission.TRAIN_AI)
        assert not pm.has_permission(Permission.BYPASS_VALORANT_CHECK)
    
    def test_user_permissions(self):
        """Test basic user role permissions."""
        pm = PermissionManager(UserRole.USER)
        
        # Should have basic permissions
        assert pm.has_permission(Permission.VIEW_HOME)
        assert pm.has_permission(Permission.VIEW_CAREER)
        assert pm.has_permission(Permission.START_ANALYSIS)
        
        # Should not have admin/dev permissions
        assert not pm.has_permission(Permission.VIEW_ADMIN_TAB)
        assert not pm.has_permission(Permission.TRAIN_AI)
        assert not pm.has_permission(Permission.MANAGE_USERS)
    
    def test_is_developer(self):
        """Test is_developer method."""
        dev_pm = PermissionManager(UserRole.DEVELOPER)
        admin_pm = PermissionManager(UserRole.ADMIN)
        user_pm = PermissionManager(UserRole.USER)
        
        assert dev_pm.is_developer() is True
        assert admin_pm.is_developer() is False
        assert user_pm.is_developer() is False
    
    def test_is_admin(self):
        """Test is_admin method."""
        dev_pm = PermissionManager(UserRole.DEVELOPER)
        admin_pm = PermissionManager(UserRole.ADMIN)
        user_pm = PermissionManager(UserRole.USER)
        
        # Developer counts as admin
        assert dev_pm.is_admin() is True
        assert admin_pm.is_admin() is True
        assert user_pm.is_admin() is False
    
    def test_can_train_ai(self):
        """Test can_train_ai method."""
        dev_pm = PermissionManager(UserRole.DEVELOPER)
        admin_pm = PermissionManager(UserRole.ADMIN)
        user_pm = PermissionManager(UserRole.USER)
        
        assert dev_pm.can_train_ai() is True
        assert admin_pm.can_train_ai() is False
        assert user_pm.can_train_ai() is False
    
    def test_can_bypass_valorant_check(self):
        """Test can_bypass_valorant_check method (SGM special permission)."""
        dev_pm = PermissionManager(UserRole.DEVELOPER)
        admin_pm = PermissionManager(UserRole.ADMIN)
        
        assert dev_pm.can_bypass_valorant_check() is True
        assert admin_pm.can_bypass_valorant_check() is False

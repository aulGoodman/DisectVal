"""
Tests for the configuration module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from disectval.config.settings import (
    AnalysisSettings,
    AppConfig,
    ClipSettings,
    ConfigManager,
    TrainingSettings,
)


class TestDataClasses:
    """Tests for configuration dataclasses."""
    
    def test_clip_settings_defaults(self):
        """Test ClipSettings default values."""
        settings = ClipSettings()
        assert settings.enabled is False
        assert settings.save_directory == ""
        assert settings.max_storage_mb == 5000
        assert settings.auto_delete_days == 7
        assert settings.save_kills is True
        assert settings.save_deaths is False
    
    def test_analysis_settings_defaults(self):
        """Test AnalysisSettings default values."""
        settings = AnalysisSettings()
        assert settings.auto_start is False
        assert settings.track_sensitivity is True
        assert settings.track_crosshair is True
        assert settings.track_positioning is True
    
    def test_training_settings_defaults(self):
        """Test TrainingSettings default values."""
        settings = TrainingSettings()
        assert settings.training_directories == []
        assert settings.sync_enabled is True
        assert settings.batch_size == 4
        assert settings.max_concurrent == 2
    
    def test_app_config_defaults(self):
        """Test AppConfig default values."""
        config = AppConfig()
        assert config.theme == "dark"
        assert config.language == "en"
        assert config.start_minimized is False
        assert config.minimize_to_tray is True
        assert config.window_width == 1280
        assert config.window_height == 800


class TestConfigManager:
    """Tests for ConfigManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create a ConfigManager with temporary storage."""
        return ConfigManager(config_dir=temp_dir)
    
    def test_init_creates_default_config(self, config_manager):
        """Test that default config is created on init."""
        assert config_manager.config is not None
        assert isinstance(config_manager.config, AppConfig)
    
    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        # Create and modify config
        cm1 = ConfigManager(config_dir=temp_dir)
        cm1.config.theme = "custom"
        cm1.config.riot_username = "TestPlayer"
        cm1.config.clips.enabled = True
        cm1.save()
        
        # Create new manager to load saved config
        cm2 = ConfigManager(config_dir=temp_dir)
        
        assert cm2.config.theme == "custom"
        assert cm2.config.riot_username == "TestPlayer"
        assert cm2.config.clips.enabled is True
    
    def test_reset_to_defaults(self, config_manager):
        """Test resetting config to defaults."""
        # Modify config
        config_manager.config.theme = "custom"
        config_manager.config.language = "es"
        
        # Reset
        config_manager.reset_to_defaults()
        
        assert config_manager.config.theme == "dark"
        assert config_manager.config.language == "en"
    
    def test_add_training_directory(self, config_manager, temp_dir):
        """Test adding a training directory."""
        # Create a test directory
        test_dir = temp_dir / "training_data"
        test_dir.mkdir()
        
        success = config_manager.add_training_directory(str(test_dir))
        
        assert success is True
        assert str(test_dir.absolute()) in config_manager.config.training.training_directories
    
    def test_add_nonexistent_training_directory(self, config_manager):
        """Test adding a non-existent directory fails."""
        success = config_manager.add_training_directory("/nonexistent/path")
        assert success is False
    
    def test_add_duplicate_training_directory(self, config_manager, temp_dir):
        """Test adding same directory twice doesn't duplicate."""
        test_dir = temp_dir / "training_data"
        test_dir.mkdir()
        
        config_manager.add_training_directory(str(test_dir))
        config_manager.add_training_directory(str(test_dir))
        
        # Should only appear once
        dirs = config_manager.config.training.training_directories
        assert len([d for d in dirs if str(test_dir.absolute()) in d]) == 1
    
    def test_remove_training_directory(self, config_manager, temp_dir):
        """Test removing a training directory."""
        test_dir = temp_dir / "training_data"
        test_dir.mkdir()
        
        config_manager.add_training_directory(str(test_dir))
        
        success = config_manager.remove_training_directory(str(test_dir.absolute()))
        
        assert success is True
        assert str(test_dir.absolute()) not in config_manager.config.training.training_directories
    
    def test_get_clip_save_path(self, config_manager):
        """Test getting clip save path."""
        path = config_manager.get_clip_save_path()
        
        assert path is not None
        assert path.exists()
        assert path.is_dir()
    
    def test_get_clip_save_path_custom(self, config_manager, temp_dir):
        """Test getting custom clip save path."""
        custom_path = temp_dir / "my_clips"
        config_manager.config.clips.save_directory = str(custom_path)
        
        path = config_manager.get_clip_save_path()
        
        assert path == custom_path
        assert path.exists()

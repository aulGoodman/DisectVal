"""
Application configuration management for DisectVal.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ClipSettings:
    """Settings for automatic clip recording."""
    enabled: bool = False
    save_directory: str = ""
    max_storage_mb: int = 5000  # 5GB default
    auto_delete_days: int = 7
    save_kills: bool = True
    save_deaths: bool = False
    save_aces: bool = True
    save_clutches: bool = True


@dataclass
class AnalysisSettings:
    """Settings for gameplay analysis."""
    auto_start: bool = False
    track_sensitivity: bool = True
    track_crosshair: bool = True
    track_positioning: bool = True
    notification_sound: bool = True


@dataclass
class TrainingSettings:
    """Settings for AI training (developer only)."""
    training_directories: List[str] = field(default_factory=list)
    sync_enabled: bool = True
    sync_url: str = ""
    batch_size: int = 4
    max_concurrent: int = 2


@dataclass
class AppConfig:
    """Main application configuration."""
    # User preferences
    theme: str = "dark"
    language: str = "en"
    start_minimized: bool = False
    minimize_to_tray: bool = True
    start_with_windows: bool = False
    
    # Riot integration
    riot_username: str = ""
    riot_tagline: str = ""
    
    # Feature settings
    clips: ClipSettings = field(default_factory=ClipSettings)
    analysis: AnalysisSettings = field(default_factory=AnalysisSettings)
    training: TrainingSettings = field(default_factory=TrainingSettings)
    
    # Window state
    window_width: int = 1280
    window_height: int = 800
    window_maximized: bool = False


class ConfigManager:
    """Manages application configuration with persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration. Uses app data directory by default.
        """
        if config_dir is None:
            if os.name == 'nt':
                base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
            else:
                base = Path.home() / '.config'
            config_dir = base / 'DisectVal'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        
        # Load or create default config
        self.config = self._load_config()
    
    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert nested dicts to dataclass instances
                if 'clips' in data:
                    data['clips'] = ClipSettings(**data['clips'])
                if 'analysis' in data:
                    data['analysis'] = AnalysisSettings(**data['analysis'])
                if 'training' in data:
                    data['training'] = TrainingSettings(**data['training'])
                
                return AppConfig(**data)
            except Exception as e:
                logger.warning(f"Error loading config, using defaults: {e}")
        
        return AppConfig()
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            # Convert to dict, handling nested dataclasses
            data = asdict(self.config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = AppConfig()
        self.save()
    
    def get_clip_save_path(self) -> Path:
        """Get the path for saving clips, creating if needed."""
        if self.config.clips.save_directory:
            path = Path(self.config.clips.save_directory)
        else:
            # Default to user's Videos folder
            if os.name == 'nt':
                videos = Path.home() / 'Videos'
            else:
                videos = Path.home() / 'Videos'
            path = videos / 'DisectVal' / 'Clips'
        
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def add_training_directory(self, directory: str) -> bool:
        """Add a training data directory."""
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return False
        
        abs_path = str(path.absolute())
        if abs_path not in self.config.training.training_directories:
            self.config.training.training_directories.append(abs_path)
            self.save()
        
        return True
    
    def remove_training_directory(self, directory: str) -> bool:
        """Remove a training data directory."""
        if directory in self.config.training.training_directories:
            self.config.training.training_directories.remove(directory)
            self.save()
            return True
        return False

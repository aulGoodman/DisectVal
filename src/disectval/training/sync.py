"""
Shared training data synchronization for DisectVal.
Ensures training data is shared across all instances to prevent
duplicate errors and synchronized training.
"""

import hashlib
import json
import logging
import os
import shutil
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class TrainingRecord:
    """Record of a training data sample."""
    file_hash: str
    source_path: str
    processed_at: str
    instance_id: str
    training_status: str = "pending"  # pending, processing, complete, error
    metadata: dict = field(default_factory=dict)


@dataclass
class SyncConfig:
    """Configuration for the sync system."""
    instance_id_bytes: int = 16  # 128-bit for better collision resistance
    stale_lock_timeout_seconds: int = 3600  # 1 hour default
    active_instance_timeout_seconds: int = 600  # 10 minutes default
    sync_interval_seconds: int = 60


@dataclass
class SyncState:
    """State of the sync system."""
    instance_id: str
    last_sync: str = ""
    processed_files: Set[str] = field(default_factory=set)
    active_instances: Dict[str, str] = field(default_factory=dict)


class SharedDataSync:
    """
    Manages shared training data across multiple DisectVal instances.
    
    Features:
    - Prevents duplicate training on same data
    - Coordinates training across instances
    - Syncs training results
    """
    
    def __init__(self, sync_dir: Optional[Path] = None, config: Optional[SyncConfig] = None):
        """
        Initialize the shared data sync system.
        
        Args:
            sync_dir: Directory for sync data. Defaults to app data location.
            config: Optional sync configuration. Uses defaults if not provided.
        """
        self.config = config or SyncConfig()
        
        if sync_dir is None:
            if os.name == 'nt':
                base = Path(os.environ.get('LOCALAPPDATA', '')) / 'DisectVal'
            else:
                base = Path.home() / '.local' / 'share' / 'DisectVal'
            sync_dir = base / 'sync'
        
        self.sync_dir = Path(sync_dir)
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize paths
        self.config_path = self.sync_dir / 'sync_config.json'
        self.state_path = self.sync_dir / 'sync_state.json'
        self.registry_path = self.sync_dir / 'training_registry.json'
        self.lock_dir = self.sync_dir / 'locks'
        self.lock_dir.mkdir(exist_ok=True)
        
        # Track last modified time for incremental sync
        self._last_registry_mtime: float = 0
        
        # Load or create instance ID
        self.instance_id = self._get_or_create_instance_id()
        
        # Load state
        self.state = self._load_state()
        self.training_registry: Dict[str, TrainingRecord] = self._load_registry()
        
        # Sync thread
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_sync = threading.Event()
        
        logger.info(f"SharedDataSync initialized for instance: {self.instance_id}")
    
    def _get_or_create_instance_id(self) -> str:
        """Get or create a unique instance identifier (128-bit for collision resistance)."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('instance_id', os.urandom(self.config.instance_id_bytes).hex())
            except Exception:
                pass
        
        instance_id = os.urandom(self.config.instance_id_bytes).hex()
        self._save_config({'instance_id': instance_id})
        return instance_id
    
    def _save_config(self, config: dict) -> None:
        """Save sync configuration."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _load_state(self) -> SyncState:
        """Load sync state from file."""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                    data['processed_files'] = set(data.get('processed_files', []))
                    return SyncState(**data)
            except Exception as e:
                logger.warning(f"Error loading sync state: {e}")
        
        return SyncState(instance_id=self.instance_id)
    
    def _save_state(self) -> None:
        """Save sync state to file."""
        data = asdict(self.state)
        data['processed_files'] = list(self.state.processed_files)
        with open(self.state_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_registry(self) -> Dict[str, TrainingRecord]:
        """Load training registry from file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    return {
                        k: TrainingRecord(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.warning(f"Error loading registry: {e}")
        return {}
    
    def _save_registry(self) -> None:
        """Save training registry to file."""
        data = {k: asdict(v) for k, v in self.training_registry.items()}
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            Hexadecimal hash string
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            IOError: If there's an error reading the file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except PermissionError:
            raise PermissionError(f"Cannot read file (permission denied): {file_path}")
        except IOError as e:
            raise IOError(f"Error reading file {file_path}: {e}")
    
    def is_file_processed(self, file_path: Path) -> bool:
        """Check if a file has already been processed for training."""
        try:
            file_hash = self.compute_file_hash(file_path)
            return file_hash in self.training_registry
        except (FileNotFoundError, PermissionError, IOError, ValueError) as e:
            logger.warning(f"Could not check if file is processed: {e}")
            return False
    
    def acquire_file_lock(self, file_hash: str) -> bool:
        """
        Acquire a lock for processing a specific file.
        Returns True if lock acquired, False if another instance holds it.
        """
        lock_file = self.lock_dir / f"{file_hash}.lock"
        
        try:
            # Check for existing lock
            if lock_file.exists():
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                # Check if lock is stale (using configurable timeout)
                lock_time = datetime.fromisoformat(lock_data['timestamp'])
                if (datetime.now() - lock_time).total_seconds() > self.config.stale_lock_timeout_seconds:
                    # Stale lock, can override
                    pass
                elif lock_data['instance_id'] != self.instance_id:
                    # Another instance has the lock
                    return False
            
            # Create/update lock
            with open(lock_file, 'w') as f:
                json.dump({
                    'instance_id': self.instance_id,
                    'timestamp': datetime.now().isoformat()
                }, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    def release_file_lock(self, file_hash: str) -> None:
        """Release a file processing lock."""
        lock_file = self.lock_dir / f"{file_hash}.lock"
        try:
            if lock_file.exists():
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                if lock_data.get('instance_id') == self.instance_id:
                    lock_file.unlink()
        except Exception as e:
            logger.warning(f"Error releasing lock: {e}")
    
    def register_training_file(
        self,
        file_path: Path,
        status: str = "pending",
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Register a file for training to prevent duplicate processing.
        
        Args:
            file_path: Path to the training file
            status: Initial training status
            metadata: Additional metadata about the file
            
        Returns:
            File hash if registered, None if already exists
        """
        try:
            file_hash = self.compute_file_hash(file_path)
            
            if file_hash in self.training_registry:
                logger.debug(f"File already registered: {file_path}")
                return None
            
            record = TrainingRecord(
                file_hash=file_hash,
                source_path=str(file_path),
                processed_at=datetime.now().isoformat(),
                instance_id=self.instance_id,
                training_status=status,
                metadata=metadata or {}
            )
            
            self.training_registry[file_hash] = record
            self._save_registry()
            
            logger.info(f"Registered training file: {file_path.name}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Error registering file: {e}")
            return None
    
    def update_training_status(self, file_hash: str, status: str) -> bool:
        """Update the training status of a registered file."""
        if file_hash in self.training_registry:
            self.training_registry[file_hash].training_status = status
            self._save_registry()
            return True
        return False
    
    def get_pending_files(self) -> List[TrainingRecord]:
        """Get all files pending training."""
        return [
            r for r in self.training_registry.values()
            if r.training_status == "pending"
        ]
    
    def announce_presence(self) -> None:
        """Announce this instance's presence for coordination."""
        self.state.active_instances[self.instance_id] = datetime.now().isoformat()
        self._save_state()
    
    def get_active_instances(self) -> List[str]:
        """Get list of recently active instances (using configurable timeout)."""
        active = []
        cutoff = datetime.now().timestamp() - self.config.active_instance_timeout_seconds
        
        for inst_id, timestamp in self.state.active_instances.items():
            try:
                inst_time = datetime.fromisoformat(timestamp).timestamp()
                if inst_time > cutoff:
                    active.append(inst_id)
            except Exception:
                pass
        
        return active
    
    def _should_reload_registry(self) -> bool:
        """Check if registry file has been modified and needs reloading."""
        try:
            if self.registry_path.exists():
                mtime = self.registry_path.stat().st_mtime
                if mtime > self._last_registry_mtime:
                    return True
        except Exception:
            pass
        return False
    
    def start_sync_thread(self, interval: Optional[int] = None) -> None:
        """Start background sync thread."""
        if self._sync_thread and self._sync_thread.is_alive():
            return
        
        sync_interval = interval or self.config.sync_interval_seconds
        
        self._stop_sync.clear()
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            args=(sync_interval,),
            daemon=True
        )
        self._sync_thread.start()
        logger.info("Sync thread started")
    
    def stop_sync_thread(self) -> None:
        """Stop background sync thread."""
        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("Sync thread stopped")
    
    def _sync_loop(self, interval: int) -> None:
        """Background sync loop with incremental registry loading."""
        while not self._stop_sync.is_set():
            try:
                self.announce_presence()
                
                # Only reload registry if file has changed (incremental sync)
                if self._should_reload_registry():
                    self.training_registry = self._load_registry()
                    logger.debug("Registry reloaded due to changes")
                
                self.state.last_sync = datetime.now().isoformat()
                self._save_state()
            except Exception as e:
                logger.error(f"Sync error: {e}")
            
            self._stop_sync.wait(interval)


# Global instance
_sync_instance: Optional[SharedDataSync] = None


def get_sync_instance(config: Optional[SyncConfig] = None) -> SharedDataSync:
    """Get the global SharedDataSync instance."""
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = SharedDataSync(config=config)
    return _sync_instance

"""Training module for DisectVal

This module provides:
- Shared training data synchronization across multiple instances
- Training data registry to prevent duplicate processing
- File locking for coordinated training across instances
"""

from .sync import SharedDataSync, SyncConfig, get_sync_instance

__all__ = ['SharedDataSync', 'SyncConfig', 'get_sync_instance']

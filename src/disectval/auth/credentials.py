"""
Secure credential management with encryption for DisectVal.
Handles user authentication with encrypted storage.
"""

import base64
import hashlib
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .roles import UserRole


class CredentialManager:
    """
    Manages encrypted user credentials with secure storage.
    Uses Fernet symmetric encryption with PBKDF2 key derivation.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the credential manager.
        
        Args:
            data_dir: Directory for storing encrypted credentials. Defaults to user's app data.
        """
        if data_dir is None:
            # Use a secure location in user's app data
            if os.name == 'nt':  # Windows
                base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
            else:  # Linux/Mac
                base = Path.home() / '.local' / 'share'
            data_dir = base / 'DisectVal'
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._credentials_file = self.data_dir / '.credentials.enc'
        self._key_file = self.data_dir / '.keydata'
        
        # Initialize encryption
        self._fernet = self._init_encryption()
        
        # Initialize with default users if fresh install
        if not self._credentials_file.exists():
            self._init_default_users()

    def _init_encryption(self) -> Fernet:
        """Initialize or load encryption key using PBKDF2 derivation."""
        # Use a machine-specific salt combined with a stored random component
        machine_id = self._get_machine_id()
        
        if self._key_file.exists():
            stored_salt = self._key_file.read_bytes()
        else:
            # Generate a random salt for this installation
            stored_salt = secrets.token_bytes(32)
            self._key_file.write_bytes(stored_salt)
            # Restrict file permissions (on Unix-like systems)
            if os.name != 'nt':
                os.chmod(self._key_file, 0o600)
        
        # Derive key using PBKDF2
        combined_salt = hashlib.sha256(machine_id + stored_salt).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=combined_salt,
            iterations=480000,  # High iteration count for security
        )
        
        # Use a constant derived from the application
        app_secret = b'DisectVal_Secure_Key_v1_SGM'
        key = base64.urlsafe_b64encode(kdf.derive(app_secret))
        
        return Fernet(key)

    def _get_machine_id(self) -> bytes:
        """Get a unique machine identifier for key derivation."""
        try:
            if os.name == 'nt':
                # Windows: Use machine GUID
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography"
                ) as key:
                    machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                    return machine_guid.encode()
            else:
                # Linux: Use machine-id
                machine_id_path = Path('/etc/machine-id')
                if machine_id_path.exists():
                    return machine_id_path.read_text().strip().encode()
        except Exception:
            pass
        
        # Fallback: Use hostname and username combination
        fallback = f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
        return fallback.encode()

    def _init_default_users(self) -> None:
        """Initialize default user credentials (encrypted)."""
        # Default users with their roles
        # Passwords are hashed before storage
        default_users = {
            'SGM': {
                'password_hash': self._hash_password('sgmtm123'),
                'role': UserRole.DEVELOPER.value,
                'valorant_input_allowed': True  # Special flag for SGM
            },
            'RIOT': {
                'password_hash': self._hash_password('RIOTACESS12481924'),
                'role': UserRole.ADMIN.value,
                'valorant_input_allowed': False
            }
        }
        self._save_credentials(default_users)

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256 with salt.
        Returns a combined salt:hash string.
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against its stored hash."""
        try:
            salt, hash_value = stored_hash.split(':')
            computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            return secrets.compare_digest(computed_hash, hash_value)
        except (ValueError, AttributeError):
            return False

    def _save_credentials(self, credentials: dict) -> None:
        """Save credentials to encrypted file."""
        import json
        data = json.dumps(credentials).encode()
        encrypted = self._fernet.encrypt(data)
        self._credentials_file.write_bytes(encrypted)
        # Restrict file permissions (on Unix-like systems)
        if os.name != 'nt':
            os.chmod(self._credentials_file, 0o600)

    def _load_credentials(self) -> dict:
        """Load credentials from encrypted file."""
        import json
        if not self._credentials_file.exists():
            return {}
        encrypted = self._credentials_file.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            User data dict if successful, None if authentication fails
        """
        credentials = self._load_credentials()
        
        if username not in credentials:
            return None
        
        user_data = credentials[username]
        if self._verify_password(password, user_data['password_hash']):
            return {
                'username': username,
                'role': UserRole(user_data['role']),
                'valorant_input_allowed': user_data.get('valorant_input_allowed', False)
            }
        
        return None

    def add_user(
        self,
        username: str,
        password: str,
        role: UserRole,
        valorant_input_allowed: bool = False
    ) -> bool:
        """
        Add a new user (requires admin/developer access).
        
        Args:
            username: New username
            password: New password
            role: User role
            valorant_input_allowed: Whether input is allowed when Valorant is active
            
        Returns:
            True if user was added successfully
        """
        credentials = self._load_credentials()
        
        if username in credentials:
            return False
        
        credentials[username] = {
            'password_hash': self._hash_password(password),
            'role': role.value,
            'valorant_input_allowed': valorant_input_allowed
        }
        
        self._save_credentials(credentials)
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password was changed successfully
        """
        credentials = self._load_credentials()
        
        if username not in credentials:
            return False
        
        if not self._verify_password(old_password, credentials[username]['password_hash']):
            return False
        
        credentials[username]['password_hash'] = self._hash_password(new_password)
        self._save_credentials(credentials)
        return True

    def delete_user(self, username: str) -> bool:
        """
        Delete a user (cannot delete SGM or RIOT default accounts).
        
        Args:
            username: Username to delete
            
        Returns:
            True if user was deleted successfully
        """
        # Protect default accounts
        if username in ('SGM', 'RIOT'):
            return False
        
        credentials = self._load_credentials()
        
        if username not in credentials:
            return False
        
        del credentials[username]
        self._save_credentials(credentials)
        return True

    def get_user_role(self, username: str) -> Optional[UserRole]:
        """Get the role for a user."""
        credentials = self._load_credentials()
        if username in credentials:
            return UserRole(credentials[username]['role'])
        return None

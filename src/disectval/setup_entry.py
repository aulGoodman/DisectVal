"""
Setup entry point for DisectVal.
Handles dependency installation and initial configuration.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def check_python_version():
    """Verify Python version meets requirements."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"Python 3.10+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def get_requirements_path() -> Path:
    """Get the path to requirements.txt."""
    paths = [
        Path(__file__).parent.parent.parent / "requirements.txt",
        Path.cwd() / "requirements.txt",
        Path(__file__).parent / "requirements.txt",
    ]
    for p in paths:
        if p.exists():
            return p
    return paths[0]


def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")
    
    req_path = get_requirements_path()
    if req_path.exists():
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(req_path),
                "--quiet"
            ])
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
    
    # Install core dependencies directly if no requirements.txt
    core_deps = [
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "cryptography>=41.0.0",
        "bcrypt>=4.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ]
    
    for dep in core_deps:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep, "--quiet"
            ])
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {dep}")
            return False
    
    print("✓ Core dependencies installed")
    return True


def setup_data_directories():
    """Create necessary data directories."""
    print("\n📁 Setting up data directories...")
    
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        base = Path.home() / '.local' / 'share'
    
    directories = [
        base / 'DisectVal',
        base / 'DisectVal' / 'training_data',
        base / 'DisectVal' / 'models',
        base / 'DisectVal' / 'logs',
        base / 'DisectVal' / 'sync',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")
    
    return True


def create_sync_config():
    """Create initial sync configuration for shared training data."""
    import json
    
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        base = Path.home() / '.local' / 'share'
    
    sync_config_path = base / 'DisectVal' / 'sync' / 'sync_config.json'
    
    if not sync_config_path.exists():
        sync_config = {
            "instance_id": os.urandom(8).hex(),
            "sync_enabled": True,
            "sync_interval_seconds": 300,
            "shared_data_path": str(base / 'DisectVal' / 'training_data'),
            "prevent_duplicate_training": True,
        }
        
        with open(sync_config_path, 'w') as f:
            json.dump(sync_config, f, indent=2)
        
        print("✓ Sync configuration created")


def main():
    """Main setup entry point."""
    setup_logging()
    
    print("=" * 50)
    print("   DisectVal Setup Wizard")
    print("   Valorant Gameplay Analysis AI")
    print("=" * 50)
    
    # Step 1: Check Python
    print("\n🔍 Checking Python version...")
    if not check_python_version():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Step 3: Setup directories
    if not setup_data_directories():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Step 4: Create sync config
    try:
        create_sync_config()
    except Exception as e:
        print(f"Warning: Could not create sync config: {e}")
    
    # Step 5: Initialize credential storage
    print("\n🔐 Initializing secure credential storage...")
    try:
        from disectval.auth.credentials import CredentialManager
        cred_mgr = CredentialManager()
        print("✓ Credential storage initialized")
    except Exception as e:
        print(f"Note: Credentials will be initialized on first run: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("=" * 50)
    print("\nYou can now run:")
    print("  • UserVersion.exe - For regular users")
    print("  • Dev.exe - For developers (requires dev credentials)")
    print("\nDefault accounts:")
    print("  • SGM (Developer) / RIOT (Admin)")
    print("=" * 50)
    
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

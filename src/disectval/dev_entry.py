"""
Developer entry point for DisectVal.
Grants all permissions with developer-only access.
Multiple developer profiles supported.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Developer profiles - only these users can access Dev mode
# Logic: username must match AND special profile key must be present
DEVELOPER_PROFILES = {
    "SGM": {
        "profile_key": "SGM_DEV_2024",
        "permissions": ["all"],
        "bypass_valorant_check": True,
    },
    "DEV1": {
        "profile_key": "DEV1_ACCESS_KEY",
        "permissions": ["all"],
        "bypass_valorant_check": False,
    },
    "DEV2": {
        "profile_key": "DEV2_ACCESS_KEY",
        "permissions": ["all"],
        "bypass_valorant_check": False,
    },
}


def setup_logging():
    """Configure developer logging with debug level."""
    if os.name == 'nt':
        log_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'DisectVal' / 'logs'
    else:
        log_dir = Path.home() / '.local' / 'share' / 'DisectVal' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'dev.log', encoding='utf-8'),
        ]
    )


def verify_developer_access() -> Optional[dict]:
    """
    Verify developer access through login.
    Returns developer profile if valid, None otherwise.
    """
    try:
        import customtkinter as ctk
    except ImportError:
        print("Error: customtkinter not installed. Run Setup.exe first.")
        return None
    
    result = {"authenticated": False, "profile": None}
    
    def on_verify():
        username = username_entry.get().strip()
        password = password_entry.get()
        profile_key = key_entry.get().strip()
        
        # Check if user is a developer profile
        if username not in DEVELOPER_PROFILES:
            status_label.configure(text="✗ Not a developer account", text_color="red")
            return
        
        # Verify profile key
        expected_key = DEVELOPER_PROFILES[username]["profile_key"]
        if profile_key != expected_key:
            status_label.configure(text="✗ Invalid developer key", text_color="red")
            return
        
        # Verify credentials
        try:
            from disectval.auth.credentials import CredentialManager
            from disectval.auth.roles import UserRole
            
            cred_mgr = CredentialManager()
            user_data = cred_mgr.authenticate(username, password)
            
            if user_data and user_data['role'] == UserRole.DEVELOPER:
                result["authenticated"] = True
                result["profile"] = DEVELOPER_PROFILES[username]
                result["user_data"] = user_data
                verify_window.destroy()
            else:
                status_label.configure(text="✗ Developer credentials required", text_color="red")
        except Exception as e:
            status_label.configure(text=f"✗ Auth error: {str(e)[:30]}", text_color="red")
    
    def on_cancel():
        verify_window.destroy()
    
    # Create verification window
    ctk.set_appearance_mode("dark")
    verify_window = ctk.CTk()
    verify_window.title("Developer Access Verification")
    verify_window.geometry("400x350")
    verify_window.resizable(False, False)
    
    # Center window
    verify_window.update_idletasks()
    x = (verify_window.winfo_screenwidth() - 400) // 2
    y = (verify_window.winfo_screenheight() - 350) // 2
    verify_window.geometry(f"400x350+{x}+{y}")
    
    # Title
    title_label = ctk.CTkLabel(
        verify_window,
        text="🔐 Developer Access",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    title_label.pack(pady=20)
    
    # Username
    ctk.CTkLabel(verify_window, text="Username:").pack(anchor="w", padx=40)
    username_entry = ctk.CTkEntry(verify_window, width=300)
    username_entry.pack(pady=5)
    
    # Password
    ctk.CTkLabel(verify_window, text="Password:").pack(anchor="w", padx=40)
    password_entry = ctk.CTkEntry(verify_window, width=300, show="•")
    password_entry.pack(pady=5)
    
    # Profile Key
    ctk.CTkLabel(verify_window, text="Developer Key:").pack(anchor="w", padx=40)
    key_entry = ctk.CTkEntry(verify_window, width=300, show="•")
    key_entry.pack(pady=5)
    
    # Status
    status_label = ctk.CTkLabel(verify_window, text="", text_color="gray")
    status_label.pack(pady=10)
    
    # Buttons
    button_frame = ctk.CTkFrame(verify_window, fg_color="transparent")
    button_frame.pack(pady=10)
    
    verify_btn = ctk.CTkButton(
        button_frame, text="Verify", width=100, command=on_verify,
        fg_color="#2563eb", hover_color="#1d4ed8"
    )
    verify_btn.pack(side="left", padx=10)
    
    cancel_btn = ctk.CTkButton(
        button_frame, text="Cancel", width=100, command=on_cancel,
        fg_color="#6b7280", hover_color="#4b5563"
    )
    cancel_btn.pack(side="left", padx=10)
    
    verify_window.mainloop()
    
    if result["authenticated"]:
        return result
    return None


def launch_dev_mode(dev_profile: dict):
    """Launch the application in developer mode."""
    logger.info("Launching DisectVal in Developer Mode")
    logger.info(f"Profile: {dev_profile.get('user_data', {}).get('username', 'Unknown')}")
    
    try:
        from disectval.main import DisectValApp
        
        app = DisectValApp()
        # Force developer mode flag
        app._dev_mode = True
        app._dev_profile = dev_profile
        app.run()
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"\nError: {e}")
        print("Please run Setup.exe first to install dependencies.")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


def main():
    """Main developer entry point."""
    setup_logging()
    logger.info("DisectVal Developer Mode starting")
    
    # Verify developer access
    dev_result = verify_developer_access()
    
    if dev_result is None:
        logger.warning("Developer access denied or cancelled")
        sys.exit(0)
    
    # Launch in dev mode
    launch_dev_mode(dev_result)


if __name__ == "__main__":
    main()

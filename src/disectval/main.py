"""
Main application for DisectVal.
Entry point and application controller.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from .auth.credentials import CredentialManager
from .auth.roles import PermissionManager

logger = logging.getLogger(__name__)


class DisectValApp:
    """
    Main DisectVal Application.
    Manages the application lifecycle and window state.
    """
    
    def __init__(self):
        """Initialize the DisectVal application."""
        if not CTK_AVAILABLE:
            raise ImportError(
                "customtkinter is required for the GUI. "
                "Install it with: pip install customtkinter"
            )
        
        # Initialize credential manager
        self.credential_manager = CredentialManager()
        
        # Current user data (set after login)
        self.current_user: Optional[dict] = None
        self.permission_manager: Optional[PermissionManager] = None
        
        # Set up the main window
        self._setup_window()
        
        # Show login page initially
        self._show_login()
    
    def _setup_window(self) -> None:
        """Set up the main application window."""
        # Set appearance mode and theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title("DisectVal - Valorant Gameplay Analysis AI")
        self.window.geometry("1280x800")
        self.window.minsize(1024, 600)
        
        # Center window on screen
        self._center_window()
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Set window icon (if available)
        try:
            # Check for icon in various locations
            icon_paths = [
                Path(__file__).parent / "assets" / "icon.ico",
                Path(__file__).parent.parent.parent / "assets" / "icon.ico",
            ]
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.window.iconbitmap(str(icon_path))
                    break
        except Exception:
            pass  # Icon not critical
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self) -> None:
        """Center the window on the screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _show_login(self) -> None:
        """Show the login page."""
        # Clear any existing content
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Import here to avoid circular imports
        from .gui.login_page import LoginPage
        
        self.login_page = LoginPage(
            self.window,
            credential_manager=self.credential_manager,
            on_login_success=self._on_login_success,
        )
        self.login_page.grid(row=0, column=0, sticky="nsew")
    
    def _on_login_success(self, user_data: dict) -> None:
        """Handle successful login."""
        self.current_user = user_data
        self.permission_manager = PermissionManager(user_data['role'])
        
        logger.info(f"User {user_data['username']} logged in with role {user_data['role'].value}")
        
        # Show main dashboard
        self._show_dashboard()
    
    def _show_dashboard(self) -> None:
        """Show the main dashboard."""
        # Clear any existing content
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Import here to avoid circular imports
        from .gui.dashboard import MainDashboard
        
        self.dashboard = MainDashboard(
            self.window,
            user_data=self.current_user,
            credential_manager=self.credential_manager,
            on_logout=self._on_logout,
        )
        self.dashboard.grid(row=0, column=0, sticky="nsew")
    
    def _on_logout(self) -> None:
        """Handle user logout."""
        logger.info(f"User {self.current_user['username']} logged out")
        
        self.current_user = None
        self.permission_manager = None
        
        # Return to login page
        self._show_login()
    
    def _on_close(self) -> None:
        """Handle window close event."""
        logger.info("Application closing")
        self.window.destroy()
    
    def run(self) -> None:
        """Run the application main loop."""
        logger.info("Starting DisectVal application")
        self.window.mainloop()


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main() -> None:
    """Main entry point for the application."""
    setup_logging()
    
    try:
        app = DisectValApp()
        app.run()
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"\nError: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

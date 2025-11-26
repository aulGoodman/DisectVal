"""
Login page for DisectVal application.
Modern UI with encrypted authentication.
"""

import logging
from typing import Callable, Optional

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from ..auth.credentials import CredentialManager
from ..auth.roles import PermissionManager, UserRole
from .theme import theme

logger = logging.getLogger(__name__)


class LoginPage(ctk.CTkFrame if CTK_AVAILABLE else object):
    """
    Modern login page with encrypted authentication.
    Features:
    - Clean dark theme with shadows
    - Bold white text with subtle shadows
    - Smooth animations
    - Secure password handling
    """
    
    def __init__(
        self, 
        parent,
        credential_manager: CredentialManager,
        on_login_success: Callable[[dict], None],
        **kwargs
    ):
        """
        Initialize the login page.
        
        Args:
            parent: Parent widget
            credential_manager: CredentialManager instance for authentication
            on_login_success: Callback when login succeeds, receives user data dict
        """
        if not CTK_AVAILABLE:
            raise ImportError("customtkinter is required for GUI features")
        
        super().__init__(parent, fg_color=theme.colors.bg_primary, **kwargs)
        
        self.credential_manager = credential_manager
        self.on_login_success = on_login_success
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the login page UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container (centered card)
        self.login_card = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
            border_width=1,
            border_color=theme.colors.border_primary,
        )
        self.login_card.grid(row=0, column=0, padx=40, pady=40)
        
        # Card content padding
        card_padding = 40
        
        # Logo/Title section
        self.title_frame = ctk.CTkFrame(
            self.login_card,
            fg_color="transparent",
        )
        self.title_frame.pack(pady=(card_padding, 20), padx=card_padding)
        
        # App logo text with shadow effect
        self.logo_shadow = ctk.CTkLabel(
            self.title_frame,
            text="DisectVal",
            font=(theme.fonts.family_heading, 36, "bold"),
            text_color=theme.colors.text_shadow,
        )
        self.logo_shadow.place(x=2, y=2)
        
        self.logo_label = ctk.CTkLabel(
            self.title_frame,
            text="DisectVal",
            font=(theme.fonts.family_heading, 36, "bold"),
            text_color=theme.colors.accent_primary,
        )
        self.logo_label.pack()
        
        # Subtitle
        self.subtitle = ctk.CTkLabel(
            self.title_frame,
            text="Valorant Gameplay Analysis AI",
            font=(theme.fonts.family_primary, 14),
            text_color=theme.colors.text_muted,
        )
        self.subtitle.pack(pady=(5, 0))
        
        # Separator line
        self.separator = ctk.CTkFrame(
            self.login_card,
            fg_color=theme.colors.border_primary,
            height=1,
        )
        self.separator.pack(fill="x", padx=card_padding, pady=20)
        
        # Login form
        self.form_frame = ctk.CTkFrame(
            self.login_card,
            fg_color="transparent",
        )
        self.form_frame.pack(pady=10, padx=card_padding, fill="x")
        
        # Username field
        self.username_label = ctk.CTkLabel(
            self.form_frame,
            text="Username",
            font=(theme.fonts.family_primary, 13, "bold"),
            text_color=theme.colors.text_secondary,
            anchor="w",
        )
        self.username_label.pack(fill="x", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Enter your username",
            width=300,
            height=44,
            font=(theme.fonts.family_primary, 14),
            fg_color=theme.colors.bg_tertiary,
            border_color=theme.colors.border_primary,
            border_width=1,
            corner_radius=8,
            text_color=theme.colors.text_primary,
            placeholder_text_color=theme.colors.text_muted,
        )
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        # Password field
        self.password_label = ctk.CTkLabel(
            self.form_frame,
            text="Password",
            font=(theme.fonts.family_primary, 13, "bold"),
            text_color=theme.colors.text_secondary,
            anchor="w",
        )
        self.password_label.pack(fill="x", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Enter your password",
            width=300,
            height=44,
            font=(theme.fonts.family_primary, 14),
            fg_color=theme.colors.bg_tertiary,
            border_color=theme.colors.border_primary,
            border_width=1,
            corner_radius=8,
            text_color=theme.colors.text_primary,
            placeholder_text_color=theme.colors.text_muted,
            show="•",
        )
        self.password_entry.pack(fill="x", pady=(0, 20))
        
        # Error message label (hidden by default)
        self.error_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.accent_error,
        )
        self.error_label.pack(fill="x", pady=(0, 10))
        
        # Login button
        self.login_button = ctk.CTkButton(
            self.form_frame,
            text="Sign In",
            font=(theme.fonts.family_primary, 15, "bold"),
            fg_color=theme.colors.accent_primary,
            hover_color="#FF5F6D",
            height=48,
            corner_radius=8,
            command=self._handle_login,
        )
        self.login_button.pack(fill="x", pady=(10, 0))
        
        # Footer info
        self.footer_frame = ctk.CTkFrame(
            self.login_card,
            fg_color="transparent",
        )
        self.footer_frame.pack(pady=(20, card_padding), padx=card_padding)
        
        self.security_label = ctk.CTkLabel(
            self.footer_frame,
            text="🔒 Secured with end-to-end encryption",
            font=(theme.fonts.family_primary, 11),
            text_color=theme.colors.text_muted,
        )
        self.security_label.pack()
        
        # Bind Enter key to login
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
        
        # Focus username field on start
        self.after(100, lambda: self.username_entry.focus())
    
    def _handle_login(self) -> None:
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Clear previous error
        self.error_label.configure(text="")
        
        # Validate input
        if not username:
            self._show_error("Please enter your username")
            self.username_entry.focus()
            return
        
        if not password:
            self._show_error("Please enter your password")
            self.password_entry.focus()
            return
        
        # Disable button during auth
        self.login_button.configure(state="disabled", text="Signing in...")
        
        # Attempt authentication
        self.after(100, lambda: self._authenticate(username, password))
    
    def _authenticate(self, username: str, password: str) -> None:
        """Perform authentication."""
        try:
            user_data = self.credential_manager.authenticate(username, password)
            
            if user_data:
                logger.info(f"User '{username}' logged in successfully")
                # Clear sensitive data
                self.password_entry.delete(0, "end")
                # Trigger success callback
                self.on_login_success(user_data)
            else:
                self._show_error("Invalid username or password")
                self.login_button.configure(state="normal", text="Sign In")
                self.password_entry.delete(0, "end")
                self.password_entry.focus()
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self._show_error("An error occurred. Please try again.")
            self.login_button.configure(state="normal", text="Sign In")
    
    def _show_error(self, message: str) -> None:
        """Display an error message."""
        self.error_label.configure(text=f"⚠ {message}")
        
        # Shake animation for error feedback
        self._shake_widget(self.login_card)
    
    def _shake_widget(self, widget, amplitude: int = 5, duration: int = 300) -> None:
        """Apply a shake animation to a widget."""
        original_x = widget.winfo_x()
        steps = 6
        delay = duration // steps
        
        def shake(step):
            if step >= steps:
                widget.place(x=original_x)
                return
            
            offset = amplitude if step % 2 == 0 else -amplitude
            widget.place(x=original_x + offset)
            self.after(delay, lambda: shake(step + 1))
        
        # Only shake if widget is placed (not grid/pack)
        # For grid/pack, just visual feedback through color
        self.username_entry.configure(border_color=theme.colors.accent_error)
        self.password_entry.configure(border_color=theme.colors.accent_error)
        
        # Reset border color after delay
        self.after(2000, self._reset_entry_borders)
    
    def _reset_entry_borders(self) -> None:
        """Reset entry field borders to default."""
        self.username_entry.configure(border_color=theme.colors.border_primary)
        self.password_entry.configure(border_color=theme.colors.border_primary)

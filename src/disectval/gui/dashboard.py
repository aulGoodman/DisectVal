"""
Main application window for DisectVal.
Contains the dashboard with all main features.
Modern UI with game profiles, optimization, and admin controls.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable, Optional, List

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None  # type: ignore

from ..auth.credentials import CredentialManager
from ..auth.roles import Permission, PermissionManager, UserRole
from ..utils.valorant_detector import InputController, ValorantDetector
from ..utils.windows_checker import CheckStatus, WindowsSettingsChecker
from ..config.feature_flags import get_flags_manager, FEATURES
from ..config.subscription import get_subscription_manager, SUBSCRIPTION_PLANS
from .theme import theme

logger = logging.getLogger(__name__)


class SidebarButton(ctk.CTkButton if CTK_AVAILABLE else object):
    """Custom sidebar navigation button."""
    
    def __init__(self, parent, text: str, icon: str = "", **kwargs):
        if not CTK_AVAILABLE:
            return
        
        super().__init__(
            parent,
            text=f"  {icon}  {text}" if icon else text,
            font=(theme.fonts.family_primary, 14),
            fg_color="transparent",
            hover_color=theme.colors.bg_hover,
            text_color=theme.colors.text_secondary,
            anchor="w",
            height=44,
            corner_radius=8,
            **kwargs
        )
    
    def set_active(self, active: bool) -> None:
        """Set the button as active/inactive."""
        if active:
            self.configure(
                fg_color=theme.colors.bg_tertiary,
                text_color=theme.colors.text_primary,
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=theme.colors.text_secondary,
            )


class MainDashboard(ctk.CTkFrame if CTK_AVAILABLE else object):
    """
    Main dashboard view after login.
    Contains sidebar navigation and content panels.
    """
    
    def __init__(
        self,
        parent,
        user_data: dict,
        credential_manager: CredentialManager,
        on_logout: Callable[[], None],
        **kwargs
    ):
        """
        Initialize the main dashboard.
        
        Args:
            parent: Parent widget
            user_data: Authenticated user data
            credential_manager: CredentialManager instance
            on_logout: Callback when user logs out
        """
        if not CTK_AVAILABLE:
            raise ImportError("customtkinter is required for GUI features")
        
        super().__init__(parent, fg_color=theme.colors.bg_primary, **kwargs)
        
        self.user_data = user_data
        self.credential_manager = credential_manager
        self.on_logout = on_logout
        self.permission_manager = PermissionManager(user_data['role'])
        self.flags_manager = get_flags_manager()
        self.subscription_manager = get_subscription_manager()
        
        # Initialize utilities
        self.valorant_detector = ValorantDetector()
        self.input_controller = InputController(self.valorant_detector)
        self.windows_checker = WindowsSettingsChecker()
        
        # Initialize game profile manager
        try:
            from ..games.profiles import GameProfileManager
            self.game_manager = GameProfileManager()
        except ImportError:
            self.game_manager = None
        
        # Set input override based on user permission
        if user_data.get('valorant_input_allowed', False):
            self.input_controller.set_user_override(True)
        
        # Navigation buttons storage
        self.nav_buttons: dict = {}
        self.current_page: str = "games"  # Default to games page
        
        self._setup_ui()
        self._show_page("games")  # Show games page by default after login
    
    def _setup_ui(self) -> None:
        """Set up the dashboard UI."""
        # Configure grid - header at top, sidebar + content below
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Content
        self.grid_rowconfigure(0, weight=0)     # Header
        self.grid_rowconfigure(1, weight=1)     # Main content
        
        # Top header with settings and profile
        self._setup_header()
        
        # Sidebar
        self._setup_sidebar()
        
        # Content area
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_primary,
            corner_radius=0,
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _setup_header(self) -> None:
        """Set up the top header with settings and profile icons."""
        self.header = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_secondary,
            height=60,
            corner_radius=0,
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        
        # Header content container
        header_inner = ctk.CTkFrame(self.header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left side - Logo
        logo_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        logo_frame.pack(side="left")
        
        ctk.CTkLabel(
            logo_frame,
            text="DisectVal",
            font=(theme.fonts.family_heading, 20, "bold"),
            text_color=theme.colors.accent_primary,
        ).pack(side="left")
        
        # Current plan badge
        current_plan = self.subscription_manager.get_current_plan()
        plan_color = theme.colors.accent_secondary if current_plan.plan_id != "free" else theme.colors.text_muted
        
        ctk.CTkLabel(
            logo_frame,
            text=f"  •  {current_plan.name.upper()}",
            font=(theme.fonts.family_primary, 11, "bold"),
            text_color=plan_color,
        ).pack(side="left", padx=(10, 0))
        
        # Right side - Settings and Profile icons
        right_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        right_frame.pack(side="right")
        
        # Settings button
        settings_btn = ctk.CTkButton(
            right_frame,
            text="⚙️",
            font=(theme.fonts.family_primary, 18),
            fg_color="transparent",
            hover_color=theme.colors.bg_hover,
            width=40,
            height=40,
            corner_radius=8,
            command=lambda: self._show_page("settings"),
        )
        settings_btn.pack(side="left", padx=(0, 8))
        
        # Profile dropdown button
        self.profile_btn = ctk.CTkButton(
            right_frame,
            text=f"👤 {self.user_data['username'][:10]}",
            font=(theme.fonts.family_primary, 13),
            fg_color=theme.colors.bg_tertiary,
            hover_color=theme.colors.bg_hover,
            height=40,
            corner_radius=8,
            command=self._toggle_profile_dropdown,
        )
        self.profile_btn.pack(side="left")
        
        # Profile dropdown (hidden by default)
        self.profile_dropdown = None
    
    def _toggle_profile_dropdown(self) -> None:
        """Toggle the profile dropdown menu."""
        if self.profile_dropdown and self.profile_dropdown.winfo_exists():
            self.profile_dropdown.destroy()
            self.profile_dropdown = None
            return
        
        # Create dropdown
        self.profile_dropdown = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_secondary,
            corner_radius=8,
            border_width=1,
            border_color=theme.colors.border_primary,
        )
        
        # Position dropdown below profile button
        btn_x = self.profile_btn.winfo_x() + self.header.winfo_x()
        btn_y = self.header.winfo_height()
        self.profile_dropdown.place(x=btn_x - 100, y=btn_y + 5)
        
        # Dropdown items
        items = [
            ("👤 Profile", self._show_profile),
            ("📊 My Plan", lambda: self._show_page("subscription")),
            ("⚙️ Settings", lambda: self._show_page("settings")),
            ("---", None),  # Separator
            ("🚪 Sign Out", self.on_logout),
        ]
        
        inner = ctk.CTkFrame(self.profile_dropdown, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        
        for label, command in items:
            if label == "---":
                sep = ctk.CTkFrame(inner, fg_color=theme.colors.border_primary, height=1)
                sep.pack(fill="x", pady=8)
            else:
                btn = ctk.CTkButton(
                    inner,
                    text=label,
                    font=(theme.fonts.family_primary, 12),
                    fg_color="transparent",
                    hover_color=theme.colors.bg_hover,
                    text_color=theme.colors.text_primary if "Sign Out" not in label else theme.colors.accent_error,
                    anchor="w",
                    height=36,
                    corner_radius=6,
                    command=lambda c=command: self._close_dropdown_and_run(c),
                )
                btn.pack(fill="x", pady=1)
    
    def _close_dropdown_and_run(self, command) -> None:
        """Close dropdown and run command."""
        if self.profile_dropdown:
            self.profile_dropdown.destroy()
            self.profile_dropdown = None
        if command:
            command()
    
    def _show_profile(self) -> None:
        """Show user profile page."""
        self._show_page("settings")
    
    def _setup_sidebar(self) -> None:
        """Set up the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_secondary,
            corner_radius=0,
            width=200,
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Navigation section
        nav_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=(theme.fonts.family_primary, 10, "bold"),
            text_color=theme.colors.text_muted,
        )
        nav_label.pack(fill="x", padx=16, pady=(16, 8), anchor="w")
        
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)
        
        # Navigation buttons - check feature visibility
        username = self.user_data['username']
        user_tier = self.permission_manager.get_user_tier()
        
        nav_items = [
            ("games", "🎮", "My Games", "game_profiles"),
            ("pc_check", "⚙️", "PC Check", "pc_check"),
            ("subscription", "💎", "Plans", "home_dashboard"),
        ]
        
        # Add admin tab if user has permission
        if self.permission_manager.can_access_admin_features():
            nav_items.append(("admin", "🔧", "Admin", "user_management"))
        
        # Add hidden feature flags panel for developers
        if self.flags_manager.is_feature_visible("feature_flags_panel", username, user_tier):
            nav_items.append(("features", "🚩", "Features", "feature_flags_panel"))
        
        for page_id, icon, label, feature_id in nav_items:
            # Check if feature is visible to this user
            if not self.flags_manager.is_feature_visible(feature_id, username, user_tier):
                continue
            
            btn = SidebarButton(
                nav_frame,
                text=label,
                icon=icon,
                command=lambda p=page_id: self._show_page(p),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[page_id] = btn
        
        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # Version label at bottom
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v0.1.0 Alpha",
            font=(theme.fonts.family_primary, 10),
            text_color=theme.colors.text_muted,
        )
        version_label.pack(pady=(0, 16))
    
    def _show_page(self, page_id: str) -> None:
        """Show a specific page/tab."""
        # Close any open dropdowns
        if self.profile_dropdown and self.profile_dropdown.winfo_exists():
            self.profile_dropdown.destroy()
            self.profile_dropdown = None
        
        # Update button states
        for pid, btn in self.nav_buttons.items():
            btn.set_active(pid == page_id)
        
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_page = page_id
        
        # Show the appropriate page
        if page_id == "home":
            self._show_home_page()
        elif page_id == "games":
            self._show_games_page()
        elif page_id == "ai_summary":
            self._show_ai_summary_page()
        elif page_id == "pc_check":
            self._show_pc_check_page()
        elif page_id == "settings":
            self._show_settings_page()
        elif page_id == "subscription":
            self._show_subscription_page()
        elif page_id == "admin":
            self._show_admin_page()
        elif page_id == "features":
            self._show_features_page()
    
    def _show_home_page(self) -> None:
        """Display the home page with quick actions."""
        # Page header
        header = self._create_page_header("Dashboard", "Game performance optimizer")
        header.pack(fill="x", pady=(0, 20))
        
        # Welcome card with gradient-like effect
        welcome_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
            border_width=1,
            border_color=theme.colors.border_primary,
        )
        welcome_card.pack(fill="x", pady=(0, 20))
        
        welcome_inner = ctk.CTkFrame(welcome_card, fg_color="transparent")
        welcome_inner.pack(fill="x", padx=28, pady=28)
        
        welcome_title = ctk.CTkLabel(
            welcome_inner,
            text=f"Welcome back, {self.user_data['username']}!",
            font=(theme.fonts.family_heading, 22, "bold"),
            text_color=theme.colors.text_primary,
        )
        welcome_title.pack(anchor="w")
        
        role_text = self.user_data['role'].value.capitalize()
        welcome_text = ctk.CTkLabel(
            welcome_inner,
            text=f"Role: {role_text} • Optimize your gaming performance",
            font=(theme.fonts.family_primary, 14),
            text_color=theme.colors.text_secondary,
        )
        welcome_text.pack(anchor="w", pady=(5, 0))
        
        # Quick Actions Grid
        actions_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 20))
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        quick_actions = [
            ("🎮", "Launch Game", "Open game with optimized settings", self._quick_launch_game),
            ("⚙️", "PC Check", "Optimize Windows settings", lambda: self._show_page("pc_check")),
            ("🤖", "AI Analysis", "Analyze your gameplay", lambda: self._show_page("ai_summary")),
        ]
        
        for i, (icon, title, desc, command) in enumerate(quick_actions):
            card = self._create_action_card(icon, title, desc, command)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
        
        # System Status Card
        status_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
        )
        status_card.pack(fill="both", expand=True)
        
        status_header = ctk.CTkFrame(status_card, fg_color="transparent")
        status_header.pack(fill="x", padx=24, pady=(24, 16))
        
        status_title = ctk.CTkLabel(
            status_header,
            text="📊 System Status",
            font=(theme.fonts.family_heading, 18, "bold"),
            text_color=theme.colors.text_primary,
        )
        status_title.pack(side="left")
        
        # Status indicators
        status_content = ctk.CTkFrame(status_card, fg_color="transparent")
        status_content.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        
        statuses = [
            ("Windows Optimization", "Not checked", theme.colors.text_muted),
            ("Games Configured", f"{len(self.game_manager.user_games) if self.game_manager else 0}", theme.colors.accent_secondary),
            ("AI Training", "Ready", theme.colors.status_optimal),
        ]
        
        for name, value, color in statuses:
            row = ctk.CTkFrame(status_content, fg_color="transparent")
            row.pack(fill="x", pady=8)
            
            ctk.CTkLabel(
                row,
                text=name,
                font=(theme.fonts.family_primary, 14),
                text_color=theme.colors.text_secondary,
            ).pack(side="left")
            
            ctk.CTkLabel(
                row,
                text=value,
                font=(theme.fonts.family_primary, 14, "bold"),
                text_color=color,
            ).pack(side="right")
    
    def _create_action_card(self, icon: str, title: str, desc: str, command) -> ctk.CTkFrame:
        """Create a quick action card."""
        card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=12,
            border_width=1,
            border_color=theme.colors.border_primary,
        )
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        icon_label = ctk.CTkLabel(
            inner,
            text=icon,
            font=(theme.fonts.family_primary, 32),
        )
        icon_label.pack(anchor="w")
        
        title_label = ctk.CTkLabel(
            inner,
            text=title,
            font=(theme.fonts.family_heading, 16, "bold"),
            text_color=theme.colors.text_primary,
        )
        title_label.pack(anchor="w", pady=(10, 0))
        
        desc_label = ctk.CTkLabel(
            inner,
            text=desc,
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_muted,
        )
        desc_label.pack(anchor="w", pady=(2, 10))
        
        btn = ctk.CTkButton(
            inner,
            text="Open →",
            font=(theme.fonts.family_primary, 12, "bold"),
            fg_color=theme.colors.accent_primary,
            hover_color="#FF5F6D",
            height=32,
            corner_radius=6,
            command=command,
        )
        btn.pack(anchor="w")
        
        return card
    
    def _quick_launch_game(self) -> None:
        """Quick launch - go to games page."""
        self._show_page("games")
    
    def _show_games_page(self) -> None:
        """Display the games page with configured games sorted by usage."""
        header = self._create_page_header("My Games", "Games sorted by most used • Click to configure or launch")
        header.pack(fill="x", pady=(0, 20))
        
        # Get available games for this user
        user_tier = self.permission_manager.get_user_tier()
        is_tester = self.permission_manager.is_tester()
        is_developer = self.permission_manager.is_developer()
        
        try:
            from ..games.profiles import APPROVED_GAMES, AccessTier, GameStatus, GameCategory
            
            # Scrollable games container
            games_scroll = ctk.CTkScrollableFrame(
                self.content_frame,
                fg_color="transparent",
            )
            games_scroll.pack(fill="both", expand=True)
            games_scroll.grid_columnconfigure((0, 1), weight=1)
            
            # Sort games by usage (most used first)
            sorted_games = []
            for game_id, profile in APPROVED_GAMES.items():
                status = GameStatus(profile.status)
                
                # Check if user can see this game
                can_see = False
                if is_developer:
                    can_see = True
                elif status == GameStatus.PUBLIC:
                    can_see = True
                elif status == GameStatus.TESTING and is_tester:
                    can_see = True
                elif status == GameStatus.BETA and (is_tester or user_tier in ["pro", "developer"]):
                    can_see = True
                
                if can_see:
                    # Get usage stats
                    user_profile = self.game_manager.user_games.get(game_id) if self.game_manager else None
                    sessions = user_profile.usage_stats.total_sessions if user_profile and user_profile.usage_stats else 0
                    last_used = user_profile.usage_stats.last_used if user_profile and user_profile.usage_stats else ""
                    sorted_games.append((game_id, profile, sessions, last_used))
            
            # Sort by sessions (desc), then last_used (desc)
            sorted_games.sort(key=lambda x: (-x[2], x[3] or ""), reverse=False)
            
            col = 0
            row = 0
            for game_id, profile, sessions, last_used in sorted_games:
                status = GameStatus(profile.status)
                category = GameCategory(profile.category) if hasattr(profile, 'category') and profile.category else GameCategory.OTHER
                
                # Create game card - larger cards for main games
                is_main_game = game_id in ["valorant", "roblox"]
                
                game_card = ctk.CTkFrame(
                    games_scroll,
                    fg_color=theme.colors.bg_secondary,
                    corner_radius=16,
                    border_width=1,
                    border_color=theme.colors.accent_primary if is_main_game else theme.colors.border_primary,
                )
                
                if is_main_game:
                    game_card.grid(row=row, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
                    row += 1
                else:
                    game_card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                    col += 1
                    if col > 1:
                        col = 0
                        row += 1
                
                game_inner = ctk.CTkFrame(game_card, fg_color="transparent")
                game_inner.pack(fill="both", expand=True, padx=20, pady=20)
                
                # Header with name and status
                header_frame = ctk.CTkFrame(game_inner, fg_color="transparent")
                header_frame.pack(fill="x")
                
                # Game icon based on category
                icon_map = {
                    GameCategory.FPS_COMPETITIVE: "🎯",
                    GameCategory.FPS_BATTLE_ROYALE: "🏆",
                    GameCategory.AUTOMATION: "🤖",
                    GameCategory.MOBA: "⚔️",
                    GameCategory.OTHER: "🎮",
                }
                icon = icon_map.get(category, "🎮")
                
                ctk.CTkLabel(
                    header_frame,
                    text=f"{icon} {profile.name}",
                    font=(theme.fonts.family_heading, 18 if is_main_game else 14, "bold"),
                    text_color=theme.colors.text_primary,
                ).pack(side="left")
                
                # Status badge
                badge_color = {
                    GameStatus.PUBLIC: theme.colors.status_optimal,
                    GameStatus.TESTING: theme.colors.accent_warning,
                    GameStatus.BETA: theme.colors.accent_secondary,
                    GameStatus.PRIVATE: theme.colors.accent_error,
                }.get(status, theme.colors.text_muted)
                
                ctk.CTkLabel(
                    header_frame,
                    text=status.value.upper(),
                    font=(theme.fonts.family_primary, 9, "bold"),
                    text_color=badge_color,
                ).pack(side="right")
                
                # Description
                desc_text = profile.description if is_main_game else (profile.short_description if hasattr(profile, 'short_description') and profile.short_description else profile.description[:60])
                ctk.CTkLabel(
                    game_inner,
                    text=desc_text,
                    font=(theme.fonts.family_primary, 12 if is_main_game else 11),
                    text_color=theme.colors.text_secondary,
                    wraplength=600 if is_main_game else 250,
                    justify="left",
                ).pack(anchor="w", pady=(8, 0))
                
                # Features list for main games
                if is_main_game and hasattr(profile, 'supported_features'):
                    features_frame = ctk.CTkFrame(game_inner, fg_color="transparent")
                    features_frame.pack(fill="x", pady=(12, 0))
                    
                    # Show top 4 features
                    feature_names = {
                        "coaching": "🎓 Coaching",
                        "sensitivity_tracking": "🖱️ Sensitivity",
                        "task_automation": "⚙️ Automation",
                        "rate_calculator": "📊 Rate Calc",
                        "overnight_automation": "🌙 Overnight",
                        "aim_training": "🎯 Aim Training",
                        "replay_analysis": "📹 Replays",
                        "crosshair_analysis": "➕ Crosshair",
                    }
                    
                    shown = 0
                    for feat in profile.supported_features[:4]:
                        if feat in feature_names:
                            ctk.CTkLabel(
                                features_frame,
                                text=feature_names[feat],
                                font=(theme.fonts.family_primary, 10),
                                text_color=theme.colors.accent_secondary,
                                fg_color=theme.colors.bg_tertiary,
                                corner_radius=4,
                                padx=8,
                                pady=2,
                            ).pack(side="left", padx=(0, 6))
                            shown += 1
                    
                    if len(profile.supported_features) > 4:
                        ctk.CTkLabel(
                            features_frame,
                            text=f"+{len(profile.supported_features) - 4} more",
                            font=(theme.fonts.family_primary, 10),
                            text_color=theme.colors.text_muted,
                        ).pack(side="left")
                
                # Usage stats
                if sessions > 0:
                    stats_text = f"Used {sessions} time{'s' if sessions != 1 else ''}"
                    ctk.CTkLabel(
                        game_inner,
                        text=stats_text,
                        font=(theme.fonts.family_primary, 10),
                        text_color=theme.colors.text_muted,
                    ).pack(anchor="w", pady=(8, 0))
                
                # Action buttons
                btn_frame = ctk.CTkFrame(game_inner, fg_color="transparent")
                btn_frame.pack(fill="x", pady=(12, 0))
                
                is_configured = self.game_manager and game_id in self.game_manager.user_games
                
                if is_configured:
                    ctk.CTkButton(
                        btn_frame,
                        text="▶ Launch",
                        font=(theme.fonts.family_primary, 12, "bold"),
                        fg_color=theme.colors.accent_secondary,
                        hover_color="#00B894",
                        height=36,
                        corner_radius=8,
                        command=lambda gid=game_id: self._launch_game(gid),
                    ).pack(side="left", padx=(0, 8))
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="⚙️ Settings",
                        font=(theme.fonts.family_primary, 12),
                        fg_color=theme.colors.bg_tertiary,
                        hover_color=theme.colors.bg_hover,
                        height=36,
                        corner_radius=8,
                        command=lambda gid=game_id: self._show_game_settings(gid),
                    ).pack(side="left")
                else:
                    ctk.CTkButton(
                        btn_frame,
                        text="+ Configure Game",
                        font=(theme.fonts.family_primary, 12, "bold"),
                        fg_color=theme.colors.accent_primary,
                        hover_color="#FF5F6D",
                        height=36,
                        corner_radius=8,
                        command=lambda gid=game_id: self._configure_game(gid),
                    ).pack(side="left")
                    
        except ImportError as e:
            logger.warning(f"Games module not available: {e}")
            ctk.CTkLabel(
                self.content_frame,
                text="Games module not available",
                font=(theme.fonts.family_primary, 14),
                text_color=theme.colors.text_muted,
            ).pack(pady=40)
    
    def _show_game_settings(self, game_id: str) -> None:
        """Show settings dialog for a game."""
        # TODO: Implement game-specific settings dialog
        logger.info(f"Opening settings for {game_id}")
    
    def _configure_game(self, game_id: str) -> None:
        """Open game configuration dialog."""
        try:
            from tkinter import filedialog
            
            exe_path = filedialog.askopenfilename(
                title=f"Select {game_id} Executable",
                filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
            )
            
            if exe_path and self.game_manager:
                self.game_manager.add_game(game_id, exe_path)
                self._show_games_page()  # Refresh
        except Exception as e:
            logger.error(f"Error configuring game: {e}")
    
    def _launch_game(self, game_id: str) -> None:
        """Launch a configured game and record usage."""
        try:
            from ..games.launcher import GameLauncher
            
            # Record session start (duration=0 for now, could be updated on game exit)
            # Future: Track game process and update duration when game closes
            if self.game_manager:
                self.game_manager.record_game_session(game_id, 0)
            
            launcher = GameLauncher(self.game_manager)
            launcher.launch_game(game_id)
        except Exception as e:
            logger.error(f"Error launching game: {e}")
    
    def _show_settings_page(self) -> None:
        """Display the settings page with Windows optimization settings."""
        header = self._create_page_header("Settings", "Configure Windows optimizations and application settings")
        header.pack(fill="x", pady=(0, 20))
        
        # Account section
        account_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
        )
        account_card.pack(fill="x", pady=(0, 20))
        
        account_inner = ctk.CTkFrame(account_card, fg_color="transparent")
        account_inner.pack(fill="x", padx=24, pady=24)
        
        ctk.CTkLabel(
            account_inner,
            text="👤 Account",
            font=(theme.fonts.family_heading, 18, "bold"),
            text_color=theme.colors.text_primary,
        ).pack(anchor="w", pady=(0, 16))
        
        # Account info
        info_items = [
            ("Username", self.user_data['username']),
            ("Role", self.user_data['role'].value.capitalize()),
            ("Plan", self.subscription_manager.get_current_plan().name),
        ]
        
        for label, value in info_items:
            row = ctk.CTkFrame(account_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            
            ctk.CTkLabel(
                row,
                text=label,
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_secondary,
            ).pack(side="left")
            
            ctk.CTkLabel(
                row,
                text=value,
                font=(theme.fonts.family_primary, 13, "bold"),
                text_color=theme.colors.text_primary,
            ).pack(side="right")
        
        # Windows settings per game
        windows_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
        )
        windows_card.pack(fill="x", pady=(0, 20))
        
        windows_inner = ctk.CTkFrame(windows_card, fg_color="transparent")
        windows_inner.pack(fill="x", padx=24, pady=24)
        
        ctk.CTkLabel(
            windows_inner,
            text="⚙️ Windows Settings per Game",
            font=(theme.fonts.family_heading, 18, "bold"),
            text_color=theme.colors.text_primary,
        ).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkLabel(
            windows_inner,
            text="These settings will be applied when launching each game",
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_muted,
        ).pack(anchor="w", pady=(0, 16))
        
        # List configured games and their settings
        if self.game_manager and self.game_manager.user_games:
            for game_id, profile in self.game_manager.user_games.items():
                game_frame = ctk.CTkFrame(windows_inner, fg_color=theme.colors.bg_tertiary, corner_radius=8)
                game_frame.pack(fill="x", pady=4)
                
                game_row = ctk.CTkFrame(game_frame, fg_color="transparent")
                game_row.pack(fill="x", padx=16, pady=12)
                
                ctk.CTkLabel(
                    game_row,
                    text=profile.name,
                    font=(theme.fonts.family_primary, 13, "bold"),
                    text_color=theme.colors.text_primary,
                ).pack(side="left")
                
                settings_text = f"Power: {profile.windows_settings.power_plan}"
                if profile.windows_settings.disable_mouse_acceleration:
                    settings_text += " • No mouse accel"
                if profile.windows_settings.game_mode:
                    settings_text += " • Game mode"
                
                ctk.CTkLabel(
                    game_row,
                    text=settings_text,
                    font=(theme.fonts.family_primary, 11),
                    text_color=theme.colors.text_muted,
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                windows_inner,
                text="No games configured yet. Add games from the Games tab.",
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_muted,
            ).pack(anchor="w")
        
        # Sync settings
        sync_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
        )
        sync_card.pack(fill="x")
        
        sync_inner = ctk.CTkFrame(sync_card, fg_color="transparent")
        sync_inner.pack(fill="x", padx=24, pady=24)
        
        ctk.CTkLabel(
            sync_inner,
            text="🔄 Account Sync",
            font=(theme.fonts.family_heading, 18, "bold"),
            text_color=theme.colors.text_primary,
        ).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkLabel(
            sync_inner,
            text="Sync your account with the website version (encrypted)",
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_muted,
        ).pack(anchor="w", pady=(0, 16))
        
        ctk.CTkButton(
            sync_inner,
            text="🔗 Link Website Account",
            font=(theme.fonts.family_primary, 13),
            fg_color=theme.colors.accent_primary,
            hover_color="#FF5F6D",
            height=40,
            corner_radius=8,
            command=self._link_website_account,
        ).pack(anchor="w")
    
    def _link_website_account(self) -> None:
        """Open dialog to link website account."""
        # TODO: Implement website account linking
        logger.info("Website account linking requested")
    
    def _show_subscription_page(self) -> None:
        """Display the subscription plans page."""
        header = self._create_page_header("Subscription Plans", "Choose the plan that's right for you")
        header.pack(fill="x", pady=(0, 20))
        
        # Current plan indicator
        current_plan = self.subscription_manager.get_current_plan()
        
        current_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
            border_width=1,
            border_color=theme.colors.accent_secondary,
        )
        current_card.pack(fill="x", pady=(0, 20))
        
        current_inner = ctk.CTkFrame(current_card, fg_color="transparent")
        current_inner.pack(fill="x", padx=24, pady=16)
        
        ctk.CTkLabel(
            current_inner,
            text=f"Current Plan: {current_plan.name}",
            font=(theme.fonts.family_heading, 16, "bold"),
            text_color=theme.colors.accent_secondary,
        ).pack(side="left")
        
        if current_plan.plan_id != "pro":
            ctk.CTkButton(
                current_inner,
                text="Upgrade →",
                font=(theme.fonts.family_primary, 12, "bold"),
                fg_color=theme.colors.accent_primary,
                hover_color="#FF5F6D",
                height=32,
                corner_radius=6,
            ).pack(side="right")
        
        # Plans grid
        plans_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        plans_frame.pack(fill="both", expand=True)
        plans_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        for i, (plan_id, plan) in enumerate(SUBSCRIPTION_PLANS.items()):
            is_current = plan_id == current_plan.plan_id
            
            plan_card = ctk.CTkFrame(
                plans_frame,
                fg_color=theme.colors.bg_secondary,
                corner_radius=16,
                border_width=2 if plan.highlight else 1,
                border_color=theme.colors.accent_primary if plan.highlight else theme.colors.border_primary,
            )
            plan_card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")
            
            plan_inner = ctk.CTkFrame(plan_card, fg_color="transparent")
            plan_inner.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Badge
            if plan.badge:
                badge = ctk.CTkLabel(
                    plan_inner,
                    text=plan.badge,
                    font=(theme.fonts.family_primary, 10, "bold"),
                    text_color=theme.colors.bg_primary,
                    fg_color=theme.colors.accent_primary,
                    corner_radius=4,
                    padx=8,
                    pady=2,
                )
                badge.pack(anchor="w", pady=(0, 8))
            
            # Plan name
            ctk.CTkLabel(
                plan_inner,
                text=plan.name,
                font=(theme.fonts.family_heading, 20, "bold"),
                text_color=theme.colors.text_primary,
            ).pack(anchor="w")
            
            # Price
            price_text = "Free" if plan.price_monthly == 0 else f"${plan.price_monthly:.2f}/mo"
            ctk.CTkLabel(
                plan_inner,
                text=price_text,
                font=(theme.fonts.family_heading, 28, "bold"),
                text_color=theme.colors.accent_primary if plan.price_monthly > 0 else theme.colors.text_primary,
            ).pack(anchor="w", pady=(8, 4))
            
            if plan.price_yearly > 0:
                yearly_savings = plan.price_monthly * 12 - plan.price_yearly
                if yearly_savings > 0:
                    savings_text = f"or ${plan.price_yearly:.2f}/year (save ${yearly_savings:.2f})"
                else:
                    savings_text = f"or ${plan.price_yearly:.2f}/year"
                ctk.CTkLabel(
                    plan_inner,
                    text=savings_text,
                    font=(theme.fonts.family_primary, 10),
                    text_color=theme.colors.text_muted,
                ).pack(anchor="w")
            
            # Description
            ctk.CTkLabel(
                plan_inner,
                text=plan.description,
                font=(theme.fonts.family_primary, 12),
                text_color=theme.colors.text_secondary,
            ).pack(anchor="w", pady=(12, 16))
            
            # Features list
            for feature in plan.features[:6]:
                feat_row = ctk.CTkFrame(plan_inner, fg_color="transparent")
                feat_row.pack(fill="x", pady=2)
                
                icon = "✓" if feature.included else "✗"
                color = theme.colors.status_optimal if feature.included else theme.colors.text_muted
                
                ctk.CTkLabel(
                    feat_row,
                    text=f"{icon} {feature.name}",
                    font=(theme.fonts.family_primary, 11),
                    text_color=color,
                ).pack(side="left")
            
            # CTA button
            if is_current:
                btn_text = "Current Plan"
                btn_color = theme.colors.bg_tertiary
                btn_state = "disabled"
            elif plan.price_monthly == 0:
                btn_text = "Downgrade"
                btn_color = theme.colors.bg_tertiary
                btn_state = "normal"
            else:
                btn_text = "Upgrade Now"
                btn_color = theme.colors.accent_primary
                btn_state = "normal"
            
            ctk.CTkButton(
                plan_inner,
                text=btn_text,
                font=(theme.fonts.family_primary, 13, "bold"),
                fg_color=btn_color,
                hover_color="#FF5F6D" if btn_color == theme.colors.accent_primary else theme.colors.bg_hover,
                height=44,
                corner_radius=8,
                state=btn_state,
                command=lambda pid=plan_id: self._upgrade_plan(pid),
            ).pack(fill="x", pady=(16, 0))
    
    def _upgrade_plan(self, plan_id: str) -> None:
        """Handle plan upgrade request."""
        # TODO: Implement payment integration
        logger.info(f"Upgrade to {plan_id} requested")
    
    def _show_ai_summary_page(self) -> None:
        """Display the AI summary page."""
        header = self._create_page_header("AI Analysis", "AI-powered gameplay insights and recommendations")
        header.pack(fill="x", pady=(0, 20))
        
        # Timeline card
        timeline_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=12,
        )
        timeline_card.pack(fill="both", expand=True)
        
        timeline_inner = ctk.CTkFrame(timeline_card, fg_color="transparent")
        timeline_inner.pack(fill="both", expand=True, padx=24, pady=24)
        
        timeline_title = ctk.CTkLabel(
            timeline_inner,
            text="🤖 AI Analysis Timeline",
            font=(theme.fonts.family_heading, 18, "bold"),
            text_color=theme.colors.text_primary,
        )
        timeline_title.pack(anchor="w", pady=(0, 10))
        
        timeline_desc = ctk.CTkLabel(
            timeline_inner,
            text="Review events from your recent games with AI-generated insights.\n"
                 "The timeline shows deaths, blunders, and suggestions for improvement.",
            font=(theme.fonts.family_primary, 13),
            text_color=theme.colors.text_secondary,
            justify="left",
        )
        timeline_desc.pack(anchor="w", pady=(0, 20))
        
        # Placeholder timeline
        placeholder_frame = ctk.CTkFrame(
            timeline_inner,
            fg_color=theme.colors.bg_tertiary,
            corner_radius=8,
            height=200,
        )
        placeholder_frame.pack(fill="x")
        placeholder_frame.pack_propagate(False)
        
        placeholder_text = ctk.CTkLabel(
            placeholder_frame,
            text="📝 No timeline data yet.\n\n"
                 "Play games with DisectVal running to generate AI insights.\n"
                 "You can view this mid-game to see your recent deaths and suggestions.",
            font=(theme.fonts.family_primary, 13),
            text_color=theme.colors.text_muted,
            justify="center",
        )
        placeholder_text.place(relx=0.5, rely=0.5, anchor="center")
    
    def _show_pc_check_page(self) -> None:
        """Display the PC settings check page."""
        header = self._create_page_header("PC Check", "Optimize your system for best gaming performance")
        header.pack(fill="x", pady=(0, 20))
        
        # Run checks button
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 20))
        
        run_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 Run System Check",
            font=(theme.fonts.family_primary, 14, "bold"),
            fg_color=theme.colors.accent_primary,
            hover_color="#FF5F6D",
            height=44,
            corner_radius=8,
            command=self._run_pc_check,
        )
        run_btn.pack(side="left")
        
        # Results area
        self.pc_check_results = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=12,
        )
        self.pc_check_results.pack(fill="both", expand=True)
        
        # Initial message
        initial_msg = ctk.CTkLabel(
            self.pc_check_results,
            text="Click 'Run System Check' to analyze your Windows settings.\n\n"
                 "The checker will look at:\n"
                 "• Power plan settings\n"
                 "• Mouse acceleration (Enhance pointer precision)\n"
                 "• Windows Game Mode\n"
                 "• Graphics settings\n"
                 "• Network optimization\n"
                 "• Storage configuration",
            font=(theme.fonts.family_primary, 13),
            text_color=theme.colors.text_secondary,
            justify="left",
        )
        initial_msg.pack(padx=24, pady=24, anchor="w")
    
    def _run_pc_check(self) -> None:
        """Run the PC settings check and display results."""
        # Clear previous results
        for widget in self.pc_check_results.winfo_children():
            widget.destroy()
        
        # Run checks
        checks = self.windows_checker.run_all_checks()
        summary = self.windows_checker.get_summary()
        
        # Summary header
        summary_frame = ctk.CTkFrame(
            self.pc_check_results,
            fg_color=theme.colors.bg_tertiary,
            corner_radius=8,
        )
        summary_frame.pack(fill="x", padx=24, pady=(24, 16))
        
        summary_inner = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_inner.pack(fill="x", padx=16, pady=16)
        
        summary_title = ctk.CTkLabel(
            summary_inner,
            text="📊 Check Summary",
            font=(theme.fonts.family_heading, 16, "bold"),
            text_color=theme.colors.text_primary,
        )
        summary_title.pack(anchor="w")
        
        summary_text = ctk.CTkLabel(
            summary_inner,
            text=f"Optimal: {summary['optimal']} | "
                 f"Needs Attention: {summary['suboptimal']} | "
                 f"Critical: {summary['critical']}",
            font=(theme.fonts.family_primary, 13),
            text_color=theme.colors.text_secondary,
        )
        summary_text.pack(anchor="w", pady=(5, 0))
        
        # Individual check results
        for check in checks:
            self._create_check_card(check)
    
    def _create_check_card(self, check) -> None:
        """Create a card for a single check result."""
        # Determine status color
        status_colors = {
            CheckStatus.OPTIMAL: theme.colors.status_optimal,
            CheckStatus.SUBOPTIMAL: theme.colors.status_suboptimal,
            CheckStatus.CRITICAL: theme.colors.status_critical,
        }
        status_color = status_colors.get(check.status, theme.colors.text_muted)
        
        card = ctk.CTkFrame(
            self.pc_check_results,
            fg_color=theme.colors.bg_tertiary,
            corner_radius=8,
        )
        card.pack(fill="x", padx=24, pady=4)
        
        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=16, pady=12)
        
        # Header row
        header_frame = ctk.CTkFrame(card_inner, fg_color="transparent")
        header_frame.pack(fill="x")
        
        status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",
            font=(theme.fonts.family_primary, 14),
            text_color=status_color,
        )
        status_indicator.pack(side="left", padx=(0, 8))
        
        name_label = ctk.CTkLabel(
            header_frame,
            text=check.name,
            font=(theme.fonts.family_primary, 14, "bold"),
            text_color=theme.colors.text_primary,
        )
        name_label.pack(side="left")
        
        category_label = ctk.CTkLabel(
            header_frame,
            text=check.category,
            font=(theme.fonts.family_primary, 11),
            text_color=theme.colors.text_muted,
        )
        category_label.pack(side="right")
        
        # Current value
        value_text = f"Current: {check.current_value} | Recommended: {check.recommended_value}"
        value_label = ctk.CTkLabel(
            card_inner,
            text=value_text,
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_secondary,
        )
        value_label.pack(anchor="w", pady=(8, 0))
        
        # Expandable description (animated from bottom)
        if check.status != CheckStatus.OPTIMAL:
            desc_frame = ctk.CTkFrame(card_inner, fg_color="transparent")
            desc_frame.pack(fill="x", pady=(8, 0))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=check.description,
                font=(theme.fonts.family_primary, 12),
                text_color=theme.colors.text_muted,
                wraplength=600,
                justify="left",
            )
            desc_label.pack(anchor="w")
            
            # How to fix section
            fix_label = ctk.CTkLabel(
                desc_frame,
                text=f"\n📝 How to fix:\n{check.how_to_fix}",
                font=(theme.fonts.family_mono, 11),
                text_color=theme.colors.text_secondary,
                wraplength=600,
                justify="left",
            )
            fix_label.pack(anchor="w", pady=(8, 0))
            
            # Auto-fix button if available
            if check.can_auto_fix and self.permission_manager.has_permission(Permission.MODIFY_SETTINGS):
                fix_btn = ctk.CTkButton(
                    desc_frame,
                    text="🔧 Apply Fix",
                    font=(theme.fonts.family_primary, 12),
                    fg_color=theme.colors.accent_secondary,
                    hover_color="#00B894",
                    height=32,
                    width=120,
                    corner_radius=6,
                    command=lambda c=check: self._apply_fix(c),
                )
                fix_btn.pack(anchor="w", pady=(10, 0))
    
    def _apply_fix(self, check) -> None:
        """Apply an automatic fix for a setting."""
        success = self.windows_checker.apply_fix(check.name)
        if success:
            # Refresh the page to show updated status
            self._show_pc_check_page()
    
    def _show_admin_page(self) -> None:
        """Display the admin/training page."""
        if not self.permission_manager.can_access_admin_features():
            return
        
        header = self._create_page_header("Admin Panel", "Developer tools and AI training")
        header.pack(fill="x", pady=(0, 20))
        
        # Training section
        if self.permission_manager.can_train_ai():
            training_card = ctk.CTkFrame(
                self.content_frame,
                fg_color=theme.colors.bg_secondary,
                corner_radius=12,
            )
            training_card.pack(fill="x", pady=(0, 20))
            
            training_inner = ctk.CTkFrame(training_card, fg_color="transparent")
            training_inner.pack(fill="x", padx=24, pady=24)
            
            training_title = ctk.CTkLabel(
                training_inner,
                text="🎓 AI Training",
                font=(theme.fonts.family_heading, 18, "bold"),
                text_color=theme.colors.text_primary,
            )
            training_title.pack(anchor="w")
            
            training_desc = ctk.CTkLabel(
                training_inner,
                text="Import gameplay footage for passive AI training.\n"
                     "The AI will analyze videos in the background while you're offline.",
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_secondary,
            )
            training_desc.pack(anchor="w", pady=(5, 15))
            
            # Import data button
            import_btn = ctk.CTkButton(
                training_inner,
                text="📁 Import Training Data",
                font=(theme.fonts.family_primary, 14, "bold"),
                fg_color=theme.colors.accent_secondary,
                hover_color="#00B894",
                height=44,
                width=200,
                corner_radius=8,
                command=self._import_training_data,
            )
            import_btn.pack(anchor="w")
            
            # Training status
            status_frame = ctk.CTkFrame(training_inner, fg_color="transparent")
            status_frame.pack(fill="x", pady=(20, 0))
            
            self.training_status = ctk.CTkLabel(
                status_frame,
                text="Training Status: Idle",
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_muted,
            )
            self.training_status.pack(anchor="w")
        
        # User management section
        if self.permission_manager.has_permission(Permission.MANAGE_USERS):
            users_card = ctk.CTkFrame(
                self.content_frame,
                fg_color=theme.colors.bg_secondary,
                corner_radius=12,
            )
            users_card.pack(fill="x")
            
            users_inner = ctk.CTkFrame(users_card, fg_color="transparent")
            users_inner.pack(fill="x", padx=24, pady=24)
            
            users_title = ctk.CTkLabel(
                users_inner,
                text="👥 User Management",
                font=(theme.fonts.family_heading, 18, "bold"),
                text_color=theme.colors.text_primary,
            )
            users_title.pack(anchor="w")
            
            users_desc = ctk.CTkLabel(
                users_inner,
                text="Manage user accounts and permissions.",
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_secondary,
            )
            users_desc.pack(anchor="w", pady=(5, 0))
    
    def _import_training_data(self) -> None:
        """Open dialog to import training data."""
        try:
            from tkinter import filedialog
            
            directory = filedialog.askdirectory(
                title="Select Training Data Directory",
                mustexist=True,
            )
            
            if directory:
                # Store the selected directory for training
                logger.info(f"Training data directory selected: {directory}")
                self.training_status.configure(
                    text=f"Training Status: Processing {Path(directory).name}..."
                )
        except Exception as e:
            logger.error(f"Error selecting training directory: {e}")
    
    def _create_page_header(self, title: str, subtitle: str) -> ctk.CTkFrame:
        """Create a page header with title and subtitle."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=(theme.fonts.family_heading, 28, "bold"),
            text_color=theme.colors.text_primary,
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            frame,
            text=subtitle,
            font=(theme.fonts.family_primary, 14),
            text_color=theme.colors.text_muted,
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
        return frame
    
    def _create_stat_card(self, label: str, value: str, icon: str) -> ctk.CTkFrame:
        """Create a statistics card."""
        card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=12,
        )
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)
        
        icon_label = ctk.CTkLabel(
            inner,
            text=icon,
            font=(theme.fonts.family_primary, 24),
        )
        icon_label.pack(anchor="w")
        
        value_label = ctk.CTkLabel(
            inner,
            text=value,
            font=(theme.fonts.family_heading, 24, "bold"),
            text_color=theme.colors.text_primary,
        )
        value_label.pack(anchor="w", pady=(8, 0))
        
        label_text = ctk.CTkLabel(
            inner,
            text=label,
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_muted,
        )
        label_text.pack(anchor="w")
        
        return card
    
    def _show_features_page(self) -> None:
        """Display the feature flags management page (developer only)."""
        if not self.permission_manager.can_manage_feature_flags():
            return
        
        header = self._create_page_header("Feature Flags", "Control feature visibility for users")
        header.pack(fill="x", pady=(0, 20))
        
        # Info card
        info_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
            border_width=1,
            border_color=theme.colors.accent_warning,
        )
        info_card.pack(fill="x", pady=(0, 20))
        
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=24, pady=16)
        
        ctk.CTkLabel(
            info_inner,
            text="⚠️ Developer Only",
            font=(theme.fonts.family_heading, 14, "bold"),
            text_color=theme.colors.accent_warning,
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_inner,
            text="Control which features are visible to users. Hidden features are only visible to granted users.",
            font=(theme.fonts.family_primary, 12),
            text_color=theme.colors.text_secondary,
        ).pack(anchor="w", pady=(4, 0))
        
        # Features list
        features_card = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=16,
        )
        features_card.pack(fill="both", expand=True)
        
        all_features = self.flags_manager.get_all_features_for_admin()
        
        # Group by category
        categories = {}
        for feature in all_features:
            cat = feature.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(feature)
        
        for category, features in categories.items():
            # Category header
            cat_frame = ctk.CTkFrame(features_card, fg_color="transparent")
            cat_frame.pack(fill="x", padx=24, pady=(16, 8))
            
            ctk.CTkLabel(
                cat_frame,
                text=category.upper(),
                font=(theme.fonts.family_primary, 11, "bold"),
                text_color=theme.colors.text_muted,
            ).pack(anchor="w")
            
            # Features in category
            for feature in features:
                self._create_feature_flag_row(features_card, feature)
    
    def _create_feature_flag_row(self, parent, feature) -> None:
        """Create a row for a feature flag."""
        row = ctk.CTkFrame(
            parent,
            fg_color=theme.colors.bg_tertiary,
            corner_radius=8,
        )
        row.pack(fill="x", padx=24, pady=4)
        
        row_inner = ctk.CTkFrame(row, fg_color="transparent")
        row_inner.pack(fill="x", padx=16, pady=12)
        
        # Left side - info
        info_frame = ctk.CTkFrame(row_inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill="x")
        
        ctk.CTkLabel(
            name_frame,
            text=feature.name,
            font=(theme.fonts.family_primary, 13, "bold"),
            text_color=theme.colors.text_primary,
        ).pack(side="left")
        
        # Hidden badge
        if feature.hidden:
            ctk.CTkLabel(
                name_frame,
                text="HIDDEN",
                font=(theme.fonts.family_primary, 9, "bold"),
                text_color=theme.colors.accent_error,
            ).pack(side="left", padx=(8, 0))
        
        ctk.CTkLabel(
            info_frame,
            text=feature.description,
            font=(theme.fonts.family_primary, 11),
            text_color=theme.colors.text_muted,
        ).pack(anchor="w", pady=(2, 0))
        
        # Granted users
        if feature.granted_users:
            ctk.CTkLabel(
                info_frame,
                text=f"Granted: {', '.join(feature.granted_users)}",
                font=(theme.fonts.family_primary, 10),
                text_color=theme.colors.accent_secondary,
            ).pack(anchor="w", pady=(2, 0))
        
        # Right side - actions
        actions_frame = ctk.CTkFrame(row_inner, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Grant access button
        grant_btn = ctk.CTkButton(
            actions_frame,
            text="Grant Access",
            font=(theme.fonts.family_primary, 11),
            fg_color=theme.colors.bg_hover,
            hover_color=theme.colors.accent_secondary,
            height=28,
            width=100,
            corner_radius=4,
            command=lambda f=feature: self._show_grant_dialog(f),
        )
        grant_btn.pack(side="left", padx=4)
        
        # Toggle hidden
        hidden_var = ctk.BooleanVar(value=feature.hidden)
        hidden_switch = ctk.CTkSwitch(
            actions_frame,
            text="Hidden",
            font=(theme.fonts.family_primary, 11),
            variable=hidden_var,
            onvalue=True,
            offvalue=False,
            command=lambda f=feature, v=hidden_var: self._toggle_feature_hidden(f, v),
        )
        hidden_switch.pack(side="left", padx=4)
    
    def _show_grant_dialog(self, feature) -> None:
        """Show dialog to grant feature access to a user."""
        dialog = ctk.CTkInputDialog(
            text=f"Enter username to grant access to '{feature.name}':",
            title="Grant Feature Access",
        )
        username = dialog.get_input()
        
        if username:
            self.flags_manager.grant_feature_access(feature.feature_id, username)
            self._show_features_page()  # Refresh
    
    def _toggle_feature_hidden(self, feature, var) -> None:
        """Toggle whether a feature is hidden."""
        self.flags_manager.set_feature_hidden(feature.feature_id, var.get())

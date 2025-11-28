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
        self.current_page: str = "home"
        
        self._setup_ui()
        self._show_page("home")
    
    def _setup_ui(self) -> None:
        """Set up the dashboard UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Content
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self._setup_sidebar()
        
        # Content area
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_primary,
            corner_radius=0,
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _setup_sidebar(self) -> None:
        """Set up the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=theme.colors.bg_secondary,
            corner_radius=0,
            width=240,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo section
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=20)
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="DisectVal",
            font=(theme.fonts.family_heading, 24, "bold"),
            text_color=theme.colors.accent_primary,
        )
        logo_label.pack(anchor="w")
        
        version_label = ctk.CTkLabel(
            logo_frame,
            text="v0.1.0 Alpha",
            font=(theme.fonts.family_primary, 11),
            text_color=theme.colors.text_muted,
        )
        version_label.pack(anchor="w")
        
        # User info section
        user_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.colors.bg_tertiary,
            corner_radius=8,
        )
        user_frame.pack(fill="x", padx=16, pady=(0, 20))
        
        user_inner = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_inner.pack(fill="x", padx=12, pady=12)
        
        user_name = ctk.CTkLabel(
            user_inner,
            text=self.user_data['username'],
            font=(theme.fonts.family_primary, 14, "bold"),
            text_color=theme.colors.text_primary,
        )
        user_name.pack(anchor="w")
        
        role_text = self.user_data['role'].value.capitalize()
        role_color = theme.colors.accent_primary if self.permission_manager.is_developer() else theme.colors.text_muted
        
        user_role = ctk.CTkLabel(
            user_inner,
            text=f"● {role_text}",
            font=(theme.fonts.family_primary, 11),
            text_color=role_color,
        )
        user_role.pack(anchor="w")
        
        # Navigation section
        nav_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=(theme.fonts.family_primary, 11, "bold"),
            text_color=theme.colors.text_muted,
        )
        nav_label.pack(fill="x", padx=20, pady=(10, 5), anchor="w")
        
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)
        
        # Navigation buttons - check feature visibility
        username = self.user_data['username']
        user_tier = self.permission_manager.get_user_tier()
        
        nav_items = [
            ("home", "🏠", "Home", "home_dashboard"),
            ("games", "🎮", "Games", "game_profiles"),
            ("pc_check", "⚙️", "PC Check", "pc_check"),
            ("ai_summary", "🤖", "AI Analysis", "sensitivity_tracking"),
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
        
        # Logout button at bottom
        logout_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logout_frame.pack(fill="x", padx=16, pady=20)
        
        logout_btn = ctk.CTkButton(
            logout_frame,
            text="Sign Out",
            font=(theme.fonts.family_primary, 13),
            fg_color=theme.colors.bg_tertiary,
            hover_color=theme.colors.accent_error,
            text_color=theme.colors.text_secondary,
            height=40,
            corner_radius=8,
            command=self.on_logout,
        )
        logout_btn.pack(fill="x")
    
    def _show_page(self, page_id: str) -> None:
        """Show a specific page/tab."""
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
        """Display the games page with configured games."""
        header = self._create_page_header("Games", "Configure and launch games with optimized settings")
        header.pack(fill="x", pady=(0, 20))
        
        # Get available games for this user
        user_tier = self.permission_manager.get_user_tier()
        is_tester = self.permission_manager.is_tester()
        is_developer = self.permission_manager.is_developer()
        
        try:
            from ..games.profiles import APPROVED_GAMES, AccessTier, GameStatus
            
            # Available games section
            available_card = ctk.CTkFrame(
                self.content_frame,
                fg_color=theme.colors.bg_secondary,
                corner_radius=16,
            )
            available_card.pack(fill="x", pady=(0, 20))
            
            available_inner = ctk.CTkFrame(available_card, fg_color="transparent")
            available_inner.pack(fill="x", padx=24, pady=24)
            
            ctk.CTkLabel(
                available_inner,
                text="🎮 Available Games",
                font=(theme.fonts.family_heading, 18, "bold"),
                text_color=theme.colors.text_primary,
            ).pack(anchor="w", pady=(0, 16))
            
            # Games grid
            games_frame = ctk.CTkFrame(available_inner, fg_color="transparent")
            games_frame.pack(fill="x")
            games_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            col = 0
            row = 0
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
                
                if not can_see:
                    continue
                
                # Create game card
                game_card = ctk.CTkFrame(
                    games_frame,
                    fg_color=theme.colors.bg_tertiary,
                    corner_radius=12,
                )
                game_card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                
                game_inner = ctk.CTkFrame(game_card, fg_color="transparent")
                game_inner.pack(fill="both", expand=True, padx=16, pady=16)
                
                # Game name with status badge
                name_frame = ctk.CTkFrame(game_inner, fg_color="transparent")
                name_frame.pack(fill="x")
                
                ctk.CTkLabel(
                    name_frame,
                    text=profile.name,
                    font=(theme.fonts.family_heading, 14, "bold"),
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
                    name_frame,
                    text=status.value.upper(),
                    font=(theme.fonts.family_primary, 9, "bold"),
                    text_color=badge_color,
                ).pack(side="right")
                
                ctk.CTkLabel(
                    game_inner,
                    text=profile.description,
                    font=(theme.fonts.family_primary, 11),
                    text_color=theme.colors.text_muted,
                    wraplength=180,
                ).pack(anchor="w", pady=(4, 10))
                
                # Check if game is configured
                is_configured = self.game_manager and game_id in self.game_manager.user_games
                
                if is_configured:
                    ctk.CTkButton(
                        game_inner,
                        text="▶ Launch",
                        font=(theme.fonts.family_primary, 12, "bold"),
                        fg_color=theme.colors.accent_secondary,
                        hover_color="#00B894",
                        height=32,
                        corner_radius=6,
                        command=lambda gid=game_id: self._launch_game(gid),
                    ).pack(fill="x")
                else:
                    ctk.CTkButton(
                        game_inner,
                        text="+ Configure",
                        font=(theme.fonts.family_primary, 12),
                        fg_color=theme.colors.bg_hover,
                        hover_color=theme.colors.accent_primary,
                        height=32,
                        corner_radius=6,
                        command=lambda gid=game_id: self._configure_game(gid),
                    ).pack(fill="x")
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1
                    
        except ImportError as e:
            logger.warning(f"Games module not available: {e}")
            ctk.CTkLabel(
                self.content_frame,
                text="Games module not available",
                font=(theme.fonts.family_primary, 14),
                text_color=theme.colors.text_muted,
            ).pack(pady=40)
    
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
        """Launch a configured game."""
        try:
            from ..games.launcher import GameLauncher
            
            launcher = GameLauncher(self.game_manager)
            launcher.launch_game(game_id)
        except Exception as e:
            logger.error(f"Error launching game: {e}")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        stats = [
            ("Games Analyzed", "0", "📊"),
            ("Total Kills", "0", "🎯"),
            ("Total Deaths", "0", "💀"),
            ("Avg K/D", "0.00", "📈"),
        ]
        
        for i, (label, value, icon) in enumerate(stats):
            card = self._create_stat_card(label, value, icon)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
        
        # Match history
        history_card = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.colors.bg_secondary,
            corner_radius=12,
        )
        history_card.pack(fill="both", expand=True)
        
        history_inner = ctk.CTkFrame(history_card, fg_color="transparent")
        history_inner.pack(fill="both", expand=True, padx=24, pady=24)
        
        history_title = ctk.CTkLabel(
            history_inner,
            text="Match History",
            font=(theme.fonts.family_heading, 16, "bold"),
            text_color=theme.colors.text_primary,
        )
        history_title.pack(anchor="w", pady=(0, 16))
        
        no_matches = ctk.CTkLabel(
            history_inner,
            text="No matches analyzed yet.\n\nStart recording your gameplay to see your match history here.",
            font=(theme.fonts.family_primary, 14),
            text_color=theme.colors.text_muted,
            justify="center",
        )
        no_matches.pack(expand=True)
    
    def _show_ranked_page(self) -> None:
        """Display the ranked analytics page."""
        header = self._create_page_header("Ranked Analytics", "In-depth analysis of your ranked performance")
        header.pack(fill="x", pady=(0, 20))
        
        # Analysis sections
        sections = [
            ("Common Mistakes", "Patterns in your deaths and losses", "⚠️"),
            ("Improvement Areas", "Skills to focus on for ranking up", "📈"),
            ("Strengths", "What you're doing well", "✅"),
        ]
        
        for title, desc, icon in sections:
            section = ctk.CTkFrame(
                self.content_frame,
                fg_color=theme.colors.bg_secondary,
                corner_radius=12,
            )
            section.pack(fill="x", pady=(0, 15))
            
            inner = ctk.CTkFrame(section, fg_color="transparent")
            inner.pack(fill="x", padx=24, pady=20)
            
            section_title = ctk.CTkLabel(
                inner,
                text=f"{icon} {title}",
                font=(theme.fonts.family_heading, 16, "bold"),
                text_color=theme.colors.text_primary,
            )
            section_title.pack(anchor="w")
            
            section_desc = ctk.CTkLabel(
                inner,
                text=desc,
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_muted,
            )
            section_desc.pack(anchor="w", pady=(5, 10))
            
            placeholder = ctk.CTkLabel(
                inner,
                text="Analyze more games to see insights here.",
                font=(theme.fonts.family_primary, 13),
                text_color=theme.colors.text_secondary,
            )
            placeholder.pack(anchor="w")
    
    def _show_ai_summary_page(self) -> None:
        """Display the AI summary page."""
        header = self._create_page_header("AI Summary", "AI-generated insights and recommendations")
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

"""
GUI Theme and styling for DisectVal.
Modern dark theme with shadows, transparency, and bold text.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ThemeColors:
    """Color definitions for the DisectVal theme."""
    # Main backgrounds
    bg_primary: str = "#0D0D0D"      # Main dark background
    bg_secondary: str = "#1A1A1A"    # Secondary background
    bg_tertiary: str = "#252525"     # Card/panel background
    bg_hover: str = "#2D2D2D"        # Hover state
    
    # Accent colors
    accent_primary: str = "#FF4655"   # Valorant red
    accent_secondary: str = "#00D4AA" # Teal/green accent
    accent_warning: str = "#FFB800"   # Warning yellow
    accent_error: str = "#FF4444"     # Error red
    
    # Text colors
    text_primary: str = "#FFFFFF"     # Main text - white
    text_secondary: str = "#B8B8B8"   # Secondary text - light gray
    text_muted: str = "#6B6B6B"       # Muted text - gray
    text_shadow: str = "#404040"      # Text shadow color
    
    # Border colors
    border_primary: str = "#333333"
    border_focus: str = "#FF4655"
    
    # Status colors
    status_online: str = "#00FF88"
    status_offline: str = "#666666"
    status_optimal: str = "#00D4AA"
    status_suboptimal: str = "#FFB800"
    status_critical: str = "#FF4444"


@dataclass
class ThemeFonts:
    """Font definitions for the DisectVal theme."""
    family_primary: str = "Segoe UI"
    family_heading: str = "Segoe UI Semibold"
    family_mono: str = "Consolas"
    
    # Font sizes
    size_h1: int = 28
    size_h2: int = 22
    size_h3: int = 18
    size_body: int = 14
    size_small: int = 12
    size_caption: int = 10


@dataclass
class ThemeShadows:
    """Shadow definitions for UI elements."""
    # Shadow offsets and colors
    text_shadow_offset: Tuple[int, int] = (1, 1)
    text_shadow_color: str = "#000000"
    
    card_shadow_offset: Tuple[int, int] = (0, 4)
    card_shadow_blur: int = 12
    card_shadow_color: str = "#000000"


class DisectValTheme:
    """Main theme class for DisectVal application."""
    
    def __init__(self):
        self.colors = ThemeColors()
        self.fonts = ThemeFonts()
        self.shadows = ThemeShadows()
    
    def get_button_style(self, variant: str = "primary") -> dict:
        """Get button styling based on variant."""
        base_style = {
            "font": (self.fonts.family_primary, self.fonts.size_body, "bold"),
            "corner_radius": 8,
            "border_width": 0,
            "height": 40,
        }
        
        if variant == "primary":
            return {
                **base_style,
                "fg_color": self.colors.accent_primary,
                "hover_color": "#FF5F6D",
                "text_color": self.colors.text_primary,
            }
        elif variant == "secondary":
            return {
                **base_style,
                "fg_color": self.colors.bg_tertiary,
                "hover_color": self.colors.bg_hover,
                "text_color": self.colors.text_primary,
                "border_width": 1,
                "border_color": self.colors.border_primary,
            }
        elif variant == "ghost":
            return {
                **base_style,
                "fg_color": "transparent",
                "hover_color": self.colors.bg_hover,
                "text_color": self.colors.text_secondary,
            }
        
        return base_style
    
    def get_entry_style(self) -> dict:
        """Get input field styling."""
        return {
            "font": (self.fonts.family_primary, self.fonts.size_body),
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": self.colors.bg_secondary,
            "border_color": self.colors.border_primary,
            "text_color": self.colors.text_primary,
            "placeholder_text_color": self.colors.text_muted,
            "height": 44,
        }
    
    def get_label_style(self, variant: str = "body") -> dict:
        """Get label styling based on variant."""
        if variant == "h1":
            return {
                "font": (self.fonts.family_heading, self.fonts.size_h1, "bold"),
                "text_color": self.colors.text_primary,
            }
        elif variant == "h2":
            return {
                "font": (self.fonts.family_heading, self.fonts.size_h2, "bold"),
                "text_color": self.colors.text_primary,
            }
        elif variant == "h3":
            return {
                "font": (self.fonts.family_heading, self.fonts.size_h3),
                "text_color": self.colors.text_primary,
            }
        elif variant == "muted":
            return {
                "font": (self.fonts.family_primary, self.fonts.size_small),
                "text_color": self.colors.text_muted,
            }
        
        return {
            "font": (self.fonts.family_primary, self.fonts.size_body),
            "text_color": self.colors.text_secondary,
        }
    
    def get_card_style(self) -> dict:
        """Get card/panel styling."""
        return {
            "fg_color": self.colors.bg_tertiary,
            "corner_radius": 12,
            "border_width": 1,
            "border_color": self.colors.border_primary,
        }
    
    def get_sidebar_style(self) -> dict:
        """Get sidebar styling."""
        return {
            "fg_color": self.colors.bg_secondary,
            "corner_radius": 0,
        }


# Global theme instance
theme = DisectValTheme()

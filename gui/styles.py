"""Design-Konstanten und Styling-Konfiguration"""

from typing import Dict, Tuple, Any
import customtkinter as ctk

# CustomTkinter Konfiguration
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class Colors:
    """Farbdefinitionen"""
    # Status-Farben
    SUCCESS_GREEN = ("#2CC985", "#2FA572")
    SUCCESS_GREEN_HOVER = ("#26B77C", "#2B9966")
    
    ERROR_RED = ("#FF6B6B", "#E55555")
    ERROR_RED_HOVER = ("#FF5252", "#D64545")
    
    DISABLED_GRAY = ("#404040", "#303030")
    PROCESSING_GRAY = ("#808080", "#606060")
    
    # Listbox-Farben
    LISTBOX_BG = "#212121"
    LISTBOX_FG = "white"
    LISTBOX_SELECT = "#1f538d"

class FontFactory:
    """Font-Factory für Lazy Loading"""
    
    _fonts_cache: Dict[str, ctk.CTkFont] = {}
    
    @classmethod
    def get_font(cls, name: str, size: int, weight: str = "normal") -> ctk.CTkFont:
        """Erstellt oder gibt gecachtes Font zurück"""
        cache_key = f"{name}_{size}_{weight}"
        
        if cache_key not in cls._fonts_cache:
            cls._fonts_cache[cache_key] = ctk.CTkFont(size=size, weight=weight)
        
        return cls._fonts_cache[cache_key]

class Fonts:
    """Schriftarten-Definitionen - Einfache Funktionen statt Properties"""
    
    @staticmethod
    def TITLE() -> ctk.CTkFont:
        return FontFactory.get_font("title", 24, "bold")
    
    @staticmethod
    def SUBTITLE() -> ctk.CTkFont:
        return FontFactory.get_font("subtitle", 13)
    
    @staticmethod
    def SECTION_HEADER() -> ctk.CTkFont:
        return FontFactory.get_font("section_header", 18, "bold")
    
    @staticmethod
    def LABEL_BOLD() -> ctk.CTkFont:
        return FontFactory.get_font("label_bold", 14, "bold")
    
    @staticmethod
    def BUTTON_LARGE() -> ctk.CTkFont:
        return FontFactory.get_font("button_large", 13, "bold")
    
    @staticmethod
    def BUTTON_SMALL() -> ctk.CTkFont:
        return FontFactory.get_font("button_small", 12)
    
    @staticmethod
    def HELP_TEXT() -> ctk.CTkFont:
        return FontFactory.get_font("help_text", 11)
    
    @staticmethod
    def SMALL_HELP() -> ctk.CTkFont:
        return FontFactory.get_font("small_help", 10)
    
    @staticmethod
    def STATUS_GRAY() -> ctk.CTkFont:
        return FontFactory.get_font("status_gray", 11)

class Dimensions:
    """Abmessungen und Größen"""
    # Fenster
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 860
    
    # Buttons
    BUTTON_LARGE_WIDTH = 200
    BUTTON_LARGE_HEIGHT = 45
    BUTTON_SMALL_HEIGHT = 40
    BUTTON_ICON_WIDTH = 50
    
    # Widgets
    SLIDER_WIDTH = 350
    SLIDER_WIDE_WIDTH = 400
    PROGRESS_BAR_WIDTH = 700
    
    # Containers
    TABVIEW_WIDTH = 500
    TABVIEW_HEIGHT = 280
    SCROLLFRAME_WIDTH = 450
    SCROLLFRAME_HEIGHT = 240
    
    # Padding
    MAIN_PADDING = 15
    SECTION_PADDING = 8
    WIDGET_PADDING = 5

class Icons:
    """Icon-Definitionen"""
    # Status-Icons
    PROCESSING = "🔄"
    SUCCESS = "✅"
    ERROR = "❌"
    CANCELLED = "⏹️"
    WARNING = "⚠️"
    
    # UI-Icons
    FOLDER = "📁"
    START = "🚀"
    STOP = "⏹️"
    REMOVE = "❌"
    CLEAR = "🗑️"
    
    # App-Icons
    MUSIC = "🎵"
    AI = "🤖"
    SETTINGS = "⚙️"

def get_default_button_colors() -> Tuple[Any, Any]:
    """Gibt die Standard-Button-Farben zurück"""
    return ctk.ThemeManager.theme["CTkButton"]["fg_color"]

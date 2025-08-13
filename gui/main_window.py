# main_window.py (vollständige Datei mit Änderungen)
"""Hauptfenster der Anwendung"""

from typing import Dict, Any, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import logging

from .anleitung import instructions
from utils import logger
from utils.logger import log_with_prefix, log_exception, set_debug_mode
from .styles import Colors, Fonts, Dimensions, Icons
from .components import ParameterSlider, IntegerSlider, ButtonGrid, StatusListBox, RadioButtonGroup
from core.file_manager import FileManager
from core.workers import ProcessingWorker, ProcessingResult

from utils.validators import (
    check_ffmpeg, is_supported_file, validate_file_path, validate_output_directory,
    validate_processing_params, validate_lufs_value, get_available_methods,
    get_default_method, get_supported_formats
)

from utils.config import Config, APP_NAME, APP_VERSION

# Logger konfigurieren
logger = logging.getLogger(__name__)

class AudioRestorerMainWindow(ctk.CTk):
    """Hauptfenster des Audio-Restaurationstools"""

    def __init__(self):
        super().__init__()
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, f"🎵 {APP_NAME} v{APP_VERSION} wird gestartet...")

        self.title(f"🎵 {APP_NAME} v{APP_VERSION}")

        # Skalierbare Fenstergröße basierend auf der Bildschirmauflösung
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Kleinere Mindestgröße für Laptops
        min_width = 1024
        min_height = 720

        # Fenstergröße auf einen Bruchteil des Bildschirms setzen, aber mit Mindestgröße
        window_width = max(min_width, int(screen_width * 0.7))
        window_height = max(min_height, int(screen_height * 0.75))
        
        # Sicherstellen, dass das Fenster nicht größer als der Bildschirm ist
        window_width = min(window_width, screen_width)
        window_height = min(window_height, screen_height - 40) # 40px Puffer für die Taskleiste

        self.geometry(f"{window_width}x{window_height}")
        self.resizable(True, True) # Fenster ist in beide Richtungen skalierbar

        # Fenster zentrieren
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"+{x}+{y}")

        # Disable dangerous tkinter features
        self.tk.call('encoding', 'system', 'utf-8')  # Force safe encoding

        # Debug-Toggle wird später im Header erstellt
        self.debug_var = tk.BooleanVar(value=Config.get_debug_mode())

        # FFmpeg-Dependency prüfen
        if not check_ffmpeg():
            messagebox.showerror(
                "FFmpeg nicht gefunden",
                "FFmpeg ist nicht installiert oder nicht im PATH.\n\n" +
                "Download: https://ffmpeg.org/download.html"
            )
            self.destroy()
            return

        # Kernkomponenten initialisieren
        self.file_manager = FileManager()
        self.processing_worker = ProcessingWorker(self._on_processing_result)
        self.available_methods = get_available_methods()

        # GUI erstellen
        self._create_gui()

    def _create_gui(self) -> None:
        """Erstellt die komplette GUI"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'GUI wird erstellt')

        self._create_header()
        self._create_main_layout()
        self._create_status_bar()

        # Initial Button-States setzen
        self._update_button_states()
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'GUI erfolgreich erstellt')

    def _create_header(self) -> None:
        """Erstellt den Header-Bereich"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Header-Bereich wird erstellt')

        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=Dimensions.MAIN_PADDING, pady=10)
        
        # Hilfe-Button oben links
        self.help_btn = ctk.CTkButton(
            header,
            text="❓ Anleitung",
            command=self._show_instructions,
            width=90,
            font=ctk.CTkFont(size=11),
            fg_color=Colors.LISTBOX_SELECT,  # Passe Farbe an deinen Stil an
        )
        self.help_btn.place(relx=0.03, rely=0.1, anchor="nw")  # Oben links positioniert

        # Debug-Toggle oben rechts mit kleinerer Schrift
        self.debug_toggle = ctk.CTkSwitch(
            header,
            text="Debug-Modus",
            variable=self.debug_var,
            command=self._toggle_debug_mode,
            width=90,
            font=ctk.CTkFont(size=11)
        )
        self.debug_toggle.place(relx=0.97, rely=0.1, anchor="ne")

        # Container für Icon und Titel (zentriert)
        title_container = ctk.CTkFrame(header, fg_color="transparent")
        title_container.pack(expand=True)

        # ✅ KORREKTUR: Variable vor try-Block initialisieren
        icon_loaded = False
        try:
            # BASE64-eingebettetes Icon laden
            icon_image = self._load_embedded_icon()
            if icon_image:
                # Icon-Label mit eingebettetem Icon
                icon_label = ctk.CTkLabel(
                    title_container,
                    image=icon_image,
                    text=""  # Kein Text, nur Icon
                )
                icon_label.pack(side="left", padx=(10, 8), pady=10)
                icon_loaded = True  # Nur bei erfolgreichem Laden auf True setzen
                log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Eingebettetes Programm-Icon erfolgreich geladen und angezeigt')
        except Exception as e:
            log_with_prefix(logger, 'exception', 'MAIN', herkunft, f"Fehler beim Laden des eingebetteten Icons: {str(e)}")
            # icon_loaded bleibt False

        # Fallback: Emoji-Icon (wenn Icon nicht geladen werden konnte)
        if not icon_loaded:
            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Verwende Fallback Emoji-Icon')
            fallback_icon = ctk.CTkLabel(
                title_container,
                text="🎵",
                font=ctk.CTkFont(size=32)
            )
            fallback_icon.pack(side="left", padx=(10, 8), pady=10)

        # Titel-Label (rechts neben dem Icon)
        title_label = ctk.CTkLabel(
            title_container,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=Fonts.TITLE()
        )
        title_label.pack(side="left", pady=10)

        # Methodenstatus (unter Icon und Titel)
        methods_text = self._get_methods_status_text()
        status_label = ctk.CTkLabel(
            header,
            text=methods_text,
            font=Fonts.STATUS_GRAY(),
            text_color="gray"
        )
        status_label.pack(pady=(0, 10))

        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Header mit Icon erfolgreich erstellt')

    def _load_embedded_icon(self) -> Optional[ctk.CTkImage]:
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Lade eingebettetes Icon aus BASE64')

        try:
            import base64
            from PIL import Image
            import io
            from .icon_data import ICON_BASE64

            # BASE64-String bereinigen (Zeilenumbrüche entfernen)
            clean_base64 = ICON_BASE64.strip().replace('\n', '').replace('\r', '').replace(' ', '')

            # Dekodieren und als PIL Image laden
            icon_bytes = base64.b64decode(clean_base64)
            icon_pil = Image.open(io.BytesIO(icon_bytes))

            # Als CTkImage für CustomTkinter konvertieren
            icon_image = ctk.CTkImage(
                light_image=icon_pil,
                dark_image=icon_pil,
                size=(32, 32)
            )
            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Eingebettetes Icon erfolgreich aus BASE64 geladen: %dx%d', icon_pil.width, icon_pil.height)
            return icon_image
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler beim Laden des eingebetteten Icons: {str(e)}")
            return None
    
    # NEU: Methode zum Anzeigen der Anleitung (importiert aus anleitung.py)
    def _show_instructions(self):
        """Zeigt ein formatiertes Popup mit der Benutzungsanleitung an"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Formatiertes Anleitungs-Fenster wird angezeigt')

        # Neues Toplevel-Fenster (Popup)
        instr_window = ctk.CTkToplevel(self)
        instr_window.title("Benutzungsanleitung")
        instr_window.geometry("600x600")  # Anpassbare Größe (größer für mehr Inhalt)
        instr_window.resizable(True, True)
        instr_window.transient(self)  # Bindet ans Hauptfenster
        instr_window.grab_set()  # Macht es modal (blockiert Hauptfenster)

        # Scrollbarer Frame für den Text
        scroll_frame = ctk.CTkFrame(instr_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tkinter Text-Widget für formatierten Text
        text_widget = tk.Text(scroll_frame, wrap="word", font=("Arial", 12), padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)

        # Definiere Tags für Formatierung (wie HTML-Styles)
        text_widget.tag_configure("heading", font=("Arial", 16, "bold"), foreground="#007BFF", spacing3=10)  # Blaue Überschriften
        text_widget.tag_configure("subheading", font=("Arial", 14, "bold"), foreground="#333", spacing3=8)
        text_widget.tag_configure("bold", font=("Arial", 12, "bold"))
        text_widget.tag_configure("italic", font=("Arial", 12, "italic"), foreground="gray")
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=30)  # Einrückung für Aufzählungspunkte
        text_widget.tag_configure("warning", foreground="red", font=("Arial", 12, "bold"))  # Für Warnungen
        
        # Füge den formatierten Text ein
        for tag, content in instructions:
            text_widget.insert(tk.END, content, tag)

        # Mache das Widget read-only
        text_widget.configure(state="disabled")

        # Schließen-Button
        close_btn = ctk.CTkButton(instr_window, text="Schließen", command=instr_window.destroy)
        close_btn.pack(pady=10)
    
    def _get_methods_status_text(self) -> str:
        """Generiert Status-Text für verfügbare Methoden"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Generiere Methoden-Status-Text')

        status_parts = ["Verfügbare Methoden: "]
        for method_id, method_info in self.available_methods.items():
            if method_info['available']:
                status_parts.append(f"✅ {method_info['name']} • ")
            else:
                status_parts.append(f"❌ {method_info['name']} • ")
        status_parts.append("✅ FFmpeg-Fallback")
        status_text = "".join(status_parts)
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Methoden-Status-Text: %s', status_text)
        return status_text

    def _create_main_layout(self) -> None:
        """Erstellt das Haupt-Layout (zwei Spalten)"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Haupt-Layout wird erstellt')

        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=Dimensions.MAIN_PADDING, pady=(0, 10))

        # Spaltenkonfiguration für das Haupt-Layout (50:50 Aufteilung)
        main_container.grid_columnconfigure(0, weight=1)  # Linke Spalte
        main_container.grid_columnconfigure(1, weight=1)  # Rechte Spalte
        main_container.grid_rowconfigure(0, weight=1)

        # Container für die linke Hälfte
        left_container = ctk.CTkFrame(main_container)
        left_container.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Scrollbarer Container für Einstellungen innerhalb des linken Containers
        left_scroll_container = ctk.CTkScrollableFrame(left_container, orientation="vertical")
        left_scroll_container.pack(fill="both", expand=True)

        # Frame für Einstellungen innerhalb des Scroll-Containers
        self.left_frame = ctk.CTkFrame(left_scroll_container, fg_color="transparent")
        self.left_frame.pack(fill="x", expand=True)

        # Rechte Spalte - Dateien und Buttons
        right_container = ctk.CTkFrame(main_container)
        right_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Scrollbarer Frame für die rechte Seite
        self.right_frame = ctk.CTkScrollableFrame(right_container)
        self.right_frame.pack(fill="both", expand=True)

        self._create_settings_panel()
        self._create_files_panel()

        # Audio-Vorschau-Widget mit Verarbeitungs-Referenz
        from gui.audio_preview import AudioPreviewWidget
        self.preview = AudioPreviewWidget(self.right_frame, width=300)
        self.preview.set_main_window(self)  # NEU: Referenz setzen
        self.preview.pack(fill="x", pady=(5, 15))

        self._create_control_buttons()

    def _create_settings_panel(self) -> None:
        """Erstellt das Einstellungs-Panel (linke Spalte)"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Einstellungs-Panel wird erstellt')

        self._create_lufs_section()
        self._create_method_section()
        self._create_voice_enhancement_section()
        self._create_parameters_section()

    def _create_lufs_section(self) -> None:
        """Erstellt die LUFS-Normalisierungs-Sektion"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'LUFS-Normalisierungs-Sektion wird erstellt')

        # Titel
        lufs_title = ctk.CTkLabel(
            self.left_frame,
            text="Lautstärke-Normalisierung",
            font=Fonts.SECTION_HEADER()
        )
        lufs_title.pack(pady=(15, 8))

        # Container
        lufs_container = ctk.CTkFrame(self.left_frame)
        lufs_container.pack(fill="x", padx=15, pady=(0, 15))

        # LUFS-Slider
        self.lufs_slider = ParameterSlider(
            parent=lufs_container,
            label="Ziel-Lautstärke (LUFS):",
            from_=-30.0,
            to=-10.0,
            initial_value=-20.0,
            unit="LUFS",
            width=Dimensions.SLIDER_WIDE_WIDTH,
            help_text="-30 LUFS = Leise • -20 LUFS = Normal • -10 LUFS = Laut"
        )
        self.lufs_slider.pack(fill="x", padx=8, pady=8)

    def _create_method_section(self) -> None:
        """Erstellt die Methoden-Auswahl-Sektion"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Methoden-Auswahl-Sektion wird erstellt')

        # Titel
        method_title = ctk.CTkLabel(
            self.left_frame,
            text="Rauschreduzierungs-Methode",
            font=Fonts.SECTION_HEADER()
        )
        method_title.pack(pady=(8, 8))

        # Container
        methods_container = ctk.CTkFrame(self.left_frame)
        methods_container.pack(fill="x", padx=15, pady=(0, 15))

        # Radio Button Optionen erstellen
        method_options = []
        for method_id, method_info in self.available_methods.items():
            if method_info['available']:
                method_options.append((
                    method_id,
                    method_info['name'],
                    method_info['description']
                ))

        # Radio Button Group
        self.method_selector = RadioButtonGroup(
            parent=methods_container,
            options=method_options,
            default_value=get_default_method()
        )
        self.method_selector.pack(fill="x", padx=8, pady=8)

    def _create_parameters_section(self) -> None:
        """Erstellt die Parameter-Sektion mit Tabs"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Parameter-Sektion wird erstellt')

        # Titel
        params_title = ctk.CTkLabel(
            self.left_frame,
            text="Parameter",
            font=Fonts.SECTION_HEADER()
        )
        params_title.pack(pady=(8, 8))

        # Tab-View
        self.tabview = ctk.CTkTabview(
            self.left_frame,
            width=Dimensions.TABVIEW_WIDTH,
            height=Dimensions.TABVIEW_HEIGHT
        )
        self.tabview.pack(fill="x", padx=15, pady=(0, 15))

        self._create_deepfilter_tab()
        self._create_audacity_tab()
        self._create_voice_tab()

        # Standard-Tab setzen
        default_method = get_default_method()
        if default_method == "deepfilternet3":
            self.tabview.set("DeepFilterNet3")
        else:
            self.tabview.set("Audacity")

    def _create_deepfilter_tab(self) -> None:
        """Erstellt den DeepFilterNet3 Parameter-Tab mit Scroll-Container"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'DeepFilterNet3 Parameter-Tab wird erstellt')

        tab = self.tabview.add("DeepFilterNet3")

        # Scrollbarer Container
        scroll_frame = ctk.CTkScrollableFrame(
            tab,
            width=Dimensions.SCROLLFRAME_WIDTH,
            height=Dimensions.SCROLLFRAME_HEIGHT
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # DeepFilterNet3 Dämpfungsgrenze-Parameter
        self.deepfilter_attenuation = ParameterSlider(
            parent=scroll_frame,
            label="Dämpfungsgrenze (dB):",
            from_=20.0,
            to=100.0,
            initial_value=80.0,
            unit="dB",
            help_text="Niedriger = Stärker (mehr Verzerrung) • Höher = Sanfter (weniger effektiv) • Empfehlung: 70-85 dB"
        )
        self.deepfilter_attenuation.pack(fill="x", padx=8, pady=(15, 8))

    def _create_audacity_tab(self) -> None:
        """Erstellt den Audacity Parameter-Tab mit Scroll-Container"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Audacity Parameter-Tab wird erstellt')

        tab = self.tabview.add("Audacity")

        # Scrollbarer Container
        scroll_frame = ctk.CTkScrollableFrame(
            tab,
            width=Dimensions.SCROLLFRAME_WIDTH,
            height=Dimensions.SCROLLFRAME_HEIGHT
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Rauschunterdrückung
        self.audacity_noise_gain = ParameterSlider(
            parent=scroll_frame,
            label="Rauschunterdrückung (dB):",
            from_=6.0,
            to=30.0,
            initial_value=12.0,
            unit="dB",
            help_text="Höher = Stärkere Rauschreduzierung • Niedriger = Natürlicherer Klang"
        )
        self.audacity_noise_gain.pack(fill="x", pady=(10, 0))

        # Empfindlichkeit
        self.audacity_sensitivity = ParameterSlider(
            parent=scroll_frame,
            label="Empfindlichkeit:",
            from_=0.0,
            to=20.0,
            initial_value=6.0,
            help_text="Höher = Mehr wird als Rauschen erkannt • Niedriger = Nur offensichtliches Rauschen"
        )
        self.audacity_sensitivity.pack(fill="x", pady=(5, 0))

        # Frequenz-Glättung
        self.audacity_freq_smoothing = IntegerSlider(
            parent=scroll_frame,
            label="Frequenz-Glättung:",
            from_=0,
            to=10,
            initial_value=0,
            help_text="0 = Keine Glättung • Höher = Weniger 'musikartige' Artefakte"
        )
        self.audacity_freq_smoothing.pack(fill="x", pady=(5, 20))

    def _create_voice_tab(self):
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Voice Enhancement Parameter-Tab wird erstellt')

        tab = self.tabview.add("Stimmverbesserung")
        scroll = ctk.CTkScrollableFrame(tab, width=Dimensions.SCROLLFRAME_WIDTH,
                                        height=Dimensions.SCROLLFRAME_HEIGHT)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Info welche Methode aktiv ist
        self.voice_method_info = ctk.CTkLabel(scroll,
                                              text="Parameter für klassische Methode",
                                              font=ctk.CTkFont(size=12, weight="bold"),
                                              text_color="gray")
        self.voice_method_info.pack(pady=(5, 15))

        # Parameter für beide Methoden (vereinfacht)
        from utils.config import Config
        # Klassische Parameter
        classic_ranges = Config.get_voice_ranges()
        classic_desc = Config.get_voice_descriptions()
        classic_defaults = Config.get_voice_defaults()
        self.voice_sliders = {}
        translated_labels = {
            "clarity_boost": "Klarheitsverstärkung:",
            "warmth_boost": "Wärmeverstärkung:",
            "bandwidth_extension": "Bandbreitenerweiterung:",
            "harmonic_restoration": "Harmonische Wiederherstellung:",
            "compression_ratio": "Kompressionsverhältnis:",
            "compression_threshold": "Kompressionsschwelle:"
        }
        for key, (vmin, vmax) in classic_ranges.items():
            slider = ParameterSlider(
                parent=scroll,
                label=translated_labels.get(key, f"{key.replace('_', ' ').title()}:"),
                from_=vmin,
                to=vmax,
                initial_value=classic_defaults[key],
                help_text=classic_desc[key]
            )
            slider.pack(fill="x", pady=6)
            self.voice_sliders[key] = slider

        # Separator
        separator = ctk.CTkLabel(scroll, text="─" * 50, text_color="gray")
        separator.pack(pady=15)

        # SpeechBrain AI Parameter
        speechbrain_ranges = Config.get_speechbrain_ranges()
        speechbrain_desc = Config.get_speechbrain_descriptions()
        speechbrain_defaults = Config.get_speechbrain_defaults()
        speechbrain_title = ctk.CTkLabel(scroll,
                                         text="🤖 SpeechBrain AI Parameter",
                                         font=ctk.CTkFont(size=12, weight="bold"))
        speechbrain_title.pack(pady=(5, 10))

        self.speechbrain_sliders = {}
        translated_sb_labels = {
            "enhancement_strength": "Verbesserungsstärke:"
        }
        for key, (vmin, vmax) in speechbrain_ranges.items():
            slider = ParameterSlider(
                parent=scroll,
                label=translated_sb_labels.get(key, f"{key.replace('_', ' ').title()}:"),
                from_=vmin,
                to=vmax,
                initial_value=speechbrain_defaults[key],
                help_text=speechbrain_desc[key]
            )
            slider.pack(fill="x", pady=6)
            self.speechbrain_sliders[key] = slider

    def _create_voice_enhancement_section(self):
        """Erstellt die Voice Enhancement Sektion"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Voice Enhancement Sektion wird erstellt')

        voice_title = ctk.CTkLabel(self.left_frame,
                                   text="Stimmverbesserung",
                                   font=Fonts.SECTION_HEADER())
        voice_title.pack(pady=(15, 8))

        container = ctk.CTkFrame(self.left_frame)
        container.pack(fill="x", padx=15, pady=(0, 15))

        # Voice Enhancement aktivieren
        self.voice_enable = ctk.BooleanVar(value=False)
        voice_checkbox = ctk.CTkCheckBox(container,
                                         text="Stimmverbesserung aktivieren",
                                         variable=self.voice_enable,
                                         command=self._on_voice_enhancement_toggle,
                                         font=Fonts.BUTTON_SMALL())
        voice_checkbox.pack(pady=10, padx=15, anchor="w")

        # NEU: Methoden-Auswahl für Voice Enhancement
        method_frame = ctk.CTkFrame(container)
        method_frame.pack(fill="x", padx=15, pady=(5, 10))

        method_label = ctk.CTkLabel(method_frame,
                                    text="Methode:",
                                    font=Fonts.BUTTON_SMALL())
        method_label.pack(anchor="w", padx=8, pady=(8, 3))

        self.voice_method_var = ctk.StringVar(value="classic")

        # Klassische Methode
        classic_radio = ctk.CTkRadioButton(method_frame,
                                           text="🎛️ Klassisch (EQ + Kompression)",
                                           variable=self.voice_method_var,
                                           value="classic",
                                           command=self._on_voice_method_change,
                                           font=Fonts.BUTTON_SMALL())
        classic_radio.pack(anchor="w", padx=20, pady=2)

        # SpeechBrain AI Methode
        self.speechbrain_radio = ctk.CTkRadioButton(method_frame,
                                                    text="🤖 SpeechBrain AI (Spektrale Maskierung)",
                                                    variable=self.voice_method_var,
                                                    value="speechbrain",
                                                    command=self._on_voice_method_change,
                                                    font=Fonts.BUTTON_SMALL())
        self.speechbrain_radio.pack(anchor="w", padx=20, pady=2)

        # Prüfe SpeechBrain Verfügbarkeit
        self._check_speechbrain_availability()

    def _check_speechbrain_availability(self):
        """Prüft ob SpeechBrain verfügbar ist und passt UI an"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Prüfe SpeechBrain Verfügbarkeit')

        try:
            from audio.speechbrain_voice_enhancer import SpeechBrainVoiceEnhancer
            enhancer = SpeechBrainVoiceEnhancer()
            if not enhancer.is_available():
                self.speechbrain_radio.configure(
                    state="disabled",
                    text="🤖 SpeechBrain AI (nicht verfügbar)"
                )
                # Fallback zu klassisch wenn SpeechBrain gewählt war
                if self.voice_method_var.get() == "speechbrain":
                    self.voice_method_var.set("classic")
                log_with_prefix(logger, 'warning', 'MAIN', herkunft, 'SpeechBrain AI nicht verfügbar, weiche auf klassisch aus')
            else:
                log_with_prefix(logger, 'info', 'MAIN', herkunft, 'SpeechBrain AI verfügbar')
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler bei SpeechBrain-Check: {str(e)}")
            self.speechbrain_radio.configure(state="disabled")

    def _on_voice_enhancement_toggle(self):
        """Wird aufgerufen wenn Voice Enhancement aktiviert/deaktiviert wird"""
        herkunft = 'main_window.py'
        enabled = self.voice_enable.get()
        log_with_prefix(logger, 'info', 'MAIN', herkunft, f"Voice Enhancement {'aktiviert' if enabled else 'deaktiviert'}")
        # Hier könnten weitere Aktionen erfolgen, z. B. UI anpassen

    def _on_voice_method_change(self):
        """Wird aufgerufen wenn Voice Enhancement Methode geändert wird"""
        herkunft = 'main_window.py'
        method = self.voice_method_var.get()
        log_with_prefix(logger, 'info', 'MAIN', herkunft, f"Voice Enhancement Methode geändert: {method}")
        # Hier könnten verschiedene Parameter-Tabs angezeigt werden
        # Momentan verwenden beide die gleichen Parameter-Tabs

    def _create_files_panel(self) -> None:
        """Erstellt das Dateien-Panel (rechte Spalte)"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Dateien-Panel wird erstellt')

        self._create_filename_options()
        self._create_output_options()
        self._create_file_list()

    def _create_filename_options(self) -> None:
        """Erstellt die Dateinamen-Optionen"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Dateinamen-Optionen werden erstellt')

        # Titel
        filename_title = ctk.CTkLabel(
            self.right_frame,
            text="Dateinamen-Optionen",
            font=Fonts.SECTION_HEADER()
        )
        filename_title.pack(pady=(15, 8))

        # Container
        filename_container = ctk.CTkFrame(self.right_frame)
        filename_container.pack(fill="x", padx=15, pady=(0, 15))

        # Suffix-Option
        suffix_frame = ctk.CTkFrame(filename_container)
        suffix_frame.pack(fill="x", padx=8, pady=5)

        self.filename_mode_var = ctk.StringVar(value="suffix")
        self.suffix_radio = ctk.CTkRadioButton(
            suffix_frame,
            text="Suffix verwenden:",
            variable=self.filename_mode_var,
            value="suffix",
            font=Fonts.BUTTON_SMALL()
        )
        self.suffix_radio.pack(side="left", padx=8)

        self.suffix_var = ctk.StringVar(value="restauriert")
        self.suffix_entry = ctk.CTkEntry(
            suffix_frame,
            textvariable=self.suffix_var,
            placeholder_text="z.B. verbessert, KI, bearbeitet...",
            width=220,
            font=Fonts.BUTTON_SMALL()
        )
        self.suffix_entry.pack(side="left", padx=8, expand=True, fill="x")

        # Event-Bindings für automatische Auswahl
        self.suffix_entry.bind('<FocusIn>', lambda e: self.filename_mode_var.set("suffix"))
        self.suffix_entry.bind('<KeyRelease>', lambda e: self.filename_mode_var.set("suffix"))

        # Original-Namen Option
        original_radio = ctk.CTkRadioButton(
            filename_container,
            text="Ursprünglichen Dateinamen verwenden",
            variable=self.filename_mode_var,
            value="original",
            font=Fonts.BUTTON_SMALL()
        )
        original_radio.pack(anchor="w", padx=15, pady=8)

    def _create_output_options(self) -> None:
        """Erstellt die Ausgabeordner-Optionen"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Ausgabeordner-Optionen werden erstellt')

        # Titel
        output_title = ctk.CTkLabel(
            self.right_frame,
            text="Zielspeicherort",
            font=Fonts.SECTION_HEADER()
        )
        output_title.pack(pady=(8, 8))

        # Container
        output_container = ctk.CTkFrame(self.right_frame)
        output_container.pack(fill="x", padx=15, pady=(0, 15))

        self.output_mode_var = ctk.StringVar(value="original_location")

        # Neben Original-Dateien
        original_location_radio = ctk.CTkRadioButton(
            output_container,
            text="Neben Original-Dateien speichern",
            variable=self.output_mode_var,
            value="original_location",
            command=self._on_output_mode_change,
            font=Fonts.BUTTON_SMALL()
        )
        original_location_radio.pack(anchor="w", padx=15, pady=5)

        # Eigener Ordner
        custom_dir_frame = ctk.CTkFrame(output_container)
        custom_dir_frame.pack(fill="x", padx=15, pady=5)

        custom_dir_radio = ctk.CTkRadioButton(
            custom_dir_frame,
            text="Eigenen Ordner verwenden:",
            variable=self.output_mode_var,
            value="custom_dir",
            command=self._on_output_mode_change,
            font=Fonts.BUTTON_SMALL()
        )
        custom_dir_radio.pack(side="left", padx=8)

        self.output_dir_var = ctk.StringVar(value="")
        self.output_entry = ctk.CTkEntry(
            custom_dir_frame,
            textvariable=self.output_dir_var,
            placeholder_text="Ordner auswählen...",
            state="disabled",
            font=Fonts.BUTTON_SMALL()
        )
        self.output_entry.pack(side="left", padx=8, expand=True, fill="x")

        self.browse_btn = ctk.CTkButton(
            custom_dir_frame,
            text=Icons.FOLDER,
            command=self._browse_output_dir,
            width=Dimensions.BUTTON_ICON_WIDTH,
            state="disabled"
        )
        self.browse_btn.pack(side="right", padx=8)

    def _create_file_list(self) -> None:
        """Erstellt die Datei-Liste"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Datei-Liste wird erstellt')

        # Titel
        list_title = ctk.CTkLabel(
            self.right_frame,
            text="Media-Dateien",
            font=Fonts.SECTION_HEADER()
        )
        list_title.pack(pady=(8, 8))

        # Info-Text
        info_label = ctk.CTkLabel(
            self.right_frame,
            text="Über Button Dateien auswählen",
            font=Fonts.HELP_TEXT(),
            text_color="gray"
        )
        info_label.pack(pady=3)

        # Listbox Container
        listbox_container = ctk.CTkFrame(self.right_frame)
        listbox_container.pack(fill="both", expand=True, padx=15, pady=8)

        # Status-Listbox
        self.file_listbox = StatusListBox(listbox_container)
        self.file_listbox.pack(fill="both", expand=True)

        # NEU: Event-Binding für Vorschau
        self.file_listbox.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

    def _create_control_buttons(self) -> None:
        """Erstellt die Steuerungs-Buttons"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Steuerungs-Buttons werden erstellt')

        buttons_container = ctk.CTkFrame(self.right_frame)
        buttons_container.pack(fill="x", padx=15, pady=8)

        # Obere Button-Reihe
        top_grid = ButtonGrid(buttons_container)
        top_grid.pack(fill="x", pady=(8, 5))

        # Dateien auswählen Button
        self.select_btn = ctk.CTkButton(
            top_grid.grid_frame,
            text=f"{Icons.FOLDER} Dateien auswählen",
            command=self._select_files,
            font=Fonts.BUTTON_LARGE(),
            height=Dimensions.BUTTON_LARGE_HEIGHT,
            width=Dimensions.BUTTON_LARGE_WIDTH
        )

        # Start/Abbrechen Button (dynamisch)
        self.start_btn = ctk.CTkButton(
            top_grid.grid_frame,
            text=f"{Icons.START} Verarbeitung starten",
            command=self._start_processing,
            font=Fonts.BUTTON_LARGE(),
            height=Dimensions.BUTTON_LARGE_HEIGHT,
            width=Dimensions.BUTTON_LARGE_WIDTH,
            state="disabled",
            fg_color=Colors.SUCCESS_GREEN,
            hover_color=Colors.SUCCESS_GREEN_HOVER
        )

        self.cancel_btn = ctk.CTkButton(
            top_grid.grid_frame,
            text=f"{Icons.STOP} Abbrechen",
            command=self._cancel_processing,
            font=Fonts.BUTTON_LARGE(),
            height=Dimensions.BUTTON_LARGE_HEIGHT,
            width=Dimensions.BUTTON_LARGE_WIDTH,
            fg_color=Colors.ERROR_RED,
            hover_color=Colors.ERROR_RED_HOVER
        )

        top_grid.add_button_pair(self.select_btn, self.start_btn)

        # Untere Button-Reihe
        bottom_grid = ButtonGrid(buttons_container)
        bottom_grid.pack(fill="x", pady=(5, 8))

        self.remove_btn = ctk.CTkButton(
            bottom_grid.grid_frame,
            text=f"{Icons.REMOVE} Element entfernen",
            command=self._remove_selected,
            font=Fonts.BUTTON_SMALL(),
            height=Dimensions.BUTTON_SMALL_HEIGHT,
            width=Dimensions.BUTTON_LARGE_WIDTH
        )

        self.clear_btn = ctk.CTkButton(
            bottom_grid.grid_frame,
            text=f"{Icons.CLEAR} Liste leeren",
            command=self._clear_list,
            font=Fonts.BUTTON_SMALL(),
            height=Dimensions.BUTTON_SMALL_HEIGHT,
            width=Dimensions.BUTTON_LARGE_WIDTH
        )

        bottom_grid.add_button_pair(self.remove_btn, self.clear_btn)

    def _create_status_bar(self) -> None:
        """Erstellt die Status-Leiste"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Status-Leiste wird erstellt')

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=Dimensions.MAIN_PADDING, pady=(0, 15))

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="✅ Bereit für Verarbeitung",
            font=Fonts.BUTTON_SMALL()
        )
        self.status_label.pack(pady=12)

        self.progress_bar = ctk.CTkProgressBar(
            bottom_frame,
            width=Dimensions.PROGRESS_BAR_WIDTH
        )
        self.progress_bar.pack(pady=(0, 12))
        self.progress_bar.set(0)

    # ========== EVENT HANDLERS ========== #

    def _select_files(self) -> None:
        """Öffnet Datei-Dialog zur Media-Auswahl (Video oder Audio)"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Datei-Auswahl-Dialog wird geöffnet')

        try:
            files = filedialog.askopenfilenames(
                title="Media-Dateien für Audio-Restauration auswählen",
                filetypes=[
                    ("Alle Medien", " ".join(get_supported_formats())),
                    ("MP4-Dateien", "*.mp4"),
                    ("MOV-Dateien", "*.mov"),
                    ("MKV-Dateien", "*.mkv"),
                    ("AVI-Dateien", "*.avi"),
                    ("MP3-Dateien", "*.mp3"),
                    ("WAV-Dateien", "*.wav"),
                    ("Alle Dateien", "*.*")
                ]
            )

            if files:
                added_count = 0
                for file_path in files:
                    if self._add_file(file_path):
                        added_count += 1
                if added_count > 0:
                    self._update_status_display()
                print(f"✅ {added_count} Dateien hinzugefügt")
        except Exception as e:
            if logger:
                log_exception(logger, e, "_select_files")
            messagebox.showerror("Fehler", f"Fehler beim Auswählen der Dateien: {str(e)}")

    def _add_file(self, file_path: str) -> bool:
        """
        Fügt eine Datei zur Liste hinzu
        Returns:
            True wenn Datei hinzugefügt wurde, False wenn bereits vorhanden oder ungültig
        """
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Füge Datei hinzu: %s', os.path.basename(file_path))

        try:
            # Validierung
            is_valid, error_msg = validate_file_path(file_path)
            if not is_valid:
                if "Warnung" not in error_msg:
                    log_with_prefix(logger, 'warning', 'MAIN', herkunft, f"Ungültige Datei: {file_path} - {error_msg}")
                    return False
                else:
                    log_with_prefix(logger, 'warning', 'MAIN', herkunft, f"⚠️ {error_msg}")

            is_valid, msg, media_type = is_supported_file(file_path)
            if not is_valid:
                log_with_prefix(logger, 'warning', 'MAIN', herkunft, f"❌ Kein unterstütztes Format: {os.path.basename(file_path)} - {msg}")
                return False

            # Zur Verwaltung hinzufügen
            display_name = self.file_manager.add_file(file_path)
            if display_name:
                self.file_listbox.add_item(display_name)
                self._update_button_states()
                log_with_prefix(logger, 'info', 'MAIN', herkunft, "Datei erfolgreich zur Liste hinzugefügt: %s (%s)", display_name, media_type)
                return True
            else:
                log_with_prefix(logger, 'debug', 'MAIN', herkunft, "Datei bereits in der Liste vorhanden: %s", os.path.basename(file_path))
                return False
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Unerwarteter Fehler beim Hinzufügen der Datei: {str(e)}")
            return False

    def _remove_selected(self) -> None:
        """Entfernt ausgewählte Dateien aus der Liste"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Entferne ausgewählte Dateien')

        try:
            selected_indices = self.file_listbox.get_selected_indices()
            if not selected_indices:
                messagebox.showinfo("Keine Auswahl", "Bitte wählen Sie Dateien zum Entfernen aus.")
                return

            # Von hinten nach vorne entfernen (um Indizes nicht zu verschieben)
            removed_count = 0
            for index in reversed(selected_indices):
                item_text = self.file_listbox.get_item(index)
                # Bereinige Text von Status-Icons
                cleaned_text = self._clean_display_name(item_text)
                if self.file_manager.remove_file(cleaned_text):
                    self.file_listbox.delete_item(index)
                    removed_count += 1
                    log_with_prefix(logger, 'info', 'MAIN', herkunft, f"Datei entfernt: {cleaned_text}")
                else:
                    log_with_prefix(logger, 'warning', 'MAIN', herkunft, f"Datei nicht gefunden in Manager: {cleaned_text}")

            if removed_count > 0:
                self._update_status_display()
                self._update_button_states()
            print(f"✅ {removed_count} Dateien entfernt")
        except Exception as e:
            if logger:
                log_exception(logger, e, "_remove_selected")
            messagebox.showerror("Fehler", f"Fehler beim Entfernen der Dateien: {str(e)}")

    def _clear_list(self) -> None:
        """Leert die komplette Dateiliste"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Leere die gesamte Dateiliste')

        if self.file_manager.get_file_count() == 0:
            return

        try:
            # Bestätigung bei vielen Dateien
            file_count = self.file_manager.get_file_count()
            if file_count > 5:
                log_with_prefix(logger, 'warning', 'MAIN', herkunft, f"⚠️ {file_count} Dateien werden gelöscht")
                response = messagebox.askyesno(
                    "Liste leeren",
                    f"Möchten Sie wirklich alle {file_count} Dateien aus der Liste entfernen?"
                )
                if not response:
                    log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Leeren der Liste abgebrochen')
                    return

            self.file_manager.clear_files()
            self.file_listbox.clear()
            self._update_status_display()
            self._update_button_states()
            self.status_label.configure(text="✅ Liste geleert")
            log_with_prefix(logger, 'info', 'MAIN', herkunft, '✅ Dateiliste geleert')
        except Exception as e:
            if logger:
                log_exception(logger, e, "_clear_list")
            messagebox.showerror("Fehler", f"Fehler beim Leeren der Liste: {str(e)}")

    def _start_processing(self) -> None:
        """Startet die Batch-Verarbeitung"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Starte Batch-Verarbeitung')

        try:
            # Validierungen
            file_count = self.file_manager.get_file_count()
            if file_count == 0:
                log_with_prefix(logger, 'warning', 'MAIN', herkunft, 'Keine Dateien ausgewählt')
                messagebox.showwarning("Keine Dateien", "Bitte wählen Sie erst Media-Dateien aus.")
                return

            log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Starte Verarbeitung für %d Dateien', file_count)

            # Parameter sammeln und validieren
            processing_config = self._collect_processing_config()
            log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Verarbeitungs-Konfiguration: %s', processing_config)

            is_valid, error_msg = self._validate_processing_config(processing_config)
            if not is_valid:
                log_with_prefix(logger, 'error', 'MAIN', herkunft, f'Ungültige Einstellungen: {error_msg}')
                messagebox.showerror("Ungültige Einstellungen", error_msg)
                return

            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Verarbeitungs-Konfiguration validiert')

            # UI für Verarbeitung vorbereiten
            self._prepare_processing_ui()

            # Verarbeitung starten
            file_paths = self.file_manager.get_all_files()
            self.processing_worker.start_processing(file_paths, processing_config)

            method_name = self.available_methods[processing_config['method']]['name']
            lufs_value = processing_config['target_lufs']
            voice_method = processing_config.get('voice_method')
            voice_enabled = processing_config.get('voice_enhancement', False)

            # Stimmverbesserung-Info ergänzen
            if voice_enabled and voice_method:
                voice_method_text = f", Stimmverbesserung: {voice_method}"
            else:
                voice_method_text = ""

            self.status_label.configure(
                text=f"Verarbeitung gestartet mit {method_name} (LUFS: {lufs_value}{voice_method_text})"
            )

            log_with_prefix(
                logger, 'info', 'MAIN', herkunft,
                'Verarbeitung gestartet: %d Dateien mit Methode "%s" und LUFS-Ziel %.2f%s',
                file_count, method_name, lufs_value, voice_method_text
            )
            print(f"🚀 Verarbeitung gestartet: {len(file_paths)} Dateien")

            # ✅ HIER erst Result-Checks starten:
            self._check_processing_results()
        except Exception as e:
            if logger:
                log_exception(logger, e, "_start_processing")
            messagebox.showerror("Fehler", f"Fehler beim Starten der Verarbeitung: {str(e)}")
            self._reset_processing_ui()

    def _cancel_processing(self) -> None:
        """Bricht die laufende Verarbeitung ab"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Breche laufende Verarbeitung ab...')

        try:
            if not self.processing_worker.is_processing:
                return

            self.processing_worker.cancel_processing()
            self.status_label.configure(text="⏹️ Verarbeitung wird abgebrochen...")
            self.cancel_btn.configure(
                state="disabled",
                text="Bricht ab...",
                fg_color=Colors.PROCESSING_GRAY
            )

            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Verarbeitung wurde abgebrochen')
            print("⏹️ Verarbeitung wird abgebrochen...")
        except Exception as e:
            if logger:
                log_exception(logger, e, "_cancel_processing")
            messagebox.showerror("Fehler", f"Fehler beim Abbrechen: {str(e)}")

    def _browse_output_dir(self) -> None:
        """Öffnet Dialog zur Auswahl des Ausgabeverzeichnisses"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Öffne Dialog für Ausgabeverzeichnis')

        try:
            directory = filedialog.askdirectory(
                title="Zielspeicherort für restaurierte Dateien auswählen"
            )
            if directory:
                # Validierung
                is_valid, error_msg = validate_output_directory(directory)
                if not is_valid:
                    messagebox.showerror("Ungültiges Verzeichnis", error_msg)
                    return
                self.output_dir_var.set(directory)
                print(f"📁 Ausgabeverzeichnis: {directory}")
        except Exception as e:
            if logger:
                log_exception(logger, e, "_browse_output_dir")
            messagebox.showerror("Fehler", f"Fehler beim Auswählen des Verzeichnisses: {str(e)}")

    def _on_output_mode_change(self) -> None:
        """Wird aufgerufen wenn sich der Ausgabemodus ändert"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Ausgabemodus geändert')

        try:
            is_custom_dir = self.output_mode_var.get() == "custom_dir"
            # Entry und Button aktivieren/deaktivieren
            state = "normal" if is_custom_dir else "disabled"
            self.output_entry.configure(state=state)
            self.browse_btn.configure(state=state)
            # Bei Deaktivierung Pfad leeren
            if not is_custom_dir:
                self.output_dir_var.set("")
        except Exception as e:
            if logger:
                log_exception(logger, e, "_on_output_mode_change")
            print(f"Fehler bei Ausgabemodus-Änderung: {e}")

    # ========== PROCESSING LOGIC ========== #

    def _collect_processing_config(self) -> Dict[str, Any]:
        """Sammelt und validiert alle Verarbeitungsparameter"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Sammle Verarbeitungsparameter')

        try:
            method = self.method_selector.get_value()
            voice_enhancement = self.voice_enable.get()
            voice_method = self.voice_method_var.get() if hasattr(self, 'voice_method_var') else "classic"
            voice_settings = self._collect_voice_settings()

            # Basis-Konfiguration
            config = {
                'method': method,
                'target_lufs': self.lufs_slider.get_value(),
                'filename_mode': self.filename_mode_var.get(),
                'custom_suffix': self.suffix_var.get(),
                'output_dir': None,
                # Voice Enhancement erweitert
                'voice_enhancement': voice_enhancement,
                'voice_method': voice_method,  # EXPLIZIT setzen
                'voice_settings': voice_settings,
                'method_params': {}
            }

            # Methodenspezifische Parameter
            if method == "deepfilternet3":
                config['method_params']['attenuation_limit'] = self.deepfilter_attenuation.get_value()
            elif method == "audacity":
                config['method_params']['rauschunterdrückung'] = self.audacity_noise_gain.get_value()
                config['method_params']['empfindlichkeit'] = self.audacity_sensitivity.get_value()
                config['method_params']['frequenzglättung'] = self.audacity_freq_smoothing.get_value()

            # Ausgabeverzeichnis
            if config['filename_mode'] == "original":
                config['output_dir'] = None
            elif self.output_mode_var.get() == "custom_dir":
                config['output_dir'] = self.output_dir_var.get()

            log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Gesammelte Konfiguration: %s', config)
            return config
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler beim Sammeln der Konfiguration: {str(e)}")
            raise

    def _collect_voice_settings(self) -> Dict[str, Any]:
        """Sammelt Voice Enhancement Settings basierend auf gewählter Methode"""
        if not self.voice_enable.get():
            log_with_prefix(logger, 'info', 'MAIN', 'main_window.py', "Voice Enhancement deaktiviert, keine Einstellungen gesammelt")
            return {}

        try:
            method = self.voice_method_var.get() if hasattr(self, 'voice_method_var') else "classic"
            log_with_prefix(logger, 'debug', 'MAIN', 'main_window.py', f"Voice Enhancement aktiviert, Methode: {method}")

            # Debug-Output für Voice-Einstellungen
            log_with_prefix(logger, 'info', 'MAIN', 'main_window.py', f"DEBUG - Voice Settings Collection:")
            log_with_prefix(logger, 'info', 'MAIN', 'main_window.py', f" Voice Enable: {self.voice_enable.get()}")
            log_with_prefix(logger, 'info', 'MAIN', 'main_window.py', f" Voice Method: {method}")
            log_with_prefix(logger, 'info', 'MAIN', 'main_window.py', f" HasAttr speechbrain_sliders: {hasattr(self, 'speechbrain_sliders')}")

            if method == "classic":
                # Klassische Parameter
                settings = {
                    key: slider.get_value()
                    for key, slider in self.voice_sliders.items()
                } if hasattr(self, 'voice_sliders') else {}
                print(f" Classic Settings: {settings}")
                return settings
            elif method == "speechbrain":
                # SpeechBrain Parameter
                settings = {
                    key: slider.get_value()
                    for key, slider in self.speechbrain_sliders.items()
                } if hasattr(self, 'speechbrain_sliders') else {}
                print(f" SpeechBrain Settings: {settings}")
                return settings
            return {}
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', 'main_window.py', "Fehler beim Sammeln der Voice-Einstellungen")
            return {}

    def _validate_processing_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validiert die Verarbeitungskonfiguration"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Validiere Verarbeitungskonfiguration')

        try:
            # LUFS validieren
            is_valid, error_msg = validate_lufs_value(config['target_lufs'])
            if not is_valid:
                log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Ungültiger LUFS-Wert: {error_msg}")
                return False, f"LUFS-Wert ungültig: {error_msg}"

            is_valid, error_msg = validate_processing_params(config['method'],
                                                            config['method_params'])
            if not is_valid:
                log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Validierung fehlgeschlagen: {error_msg}")
            else:
                log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Konfiguration validiert')

            # Ausgabeverzeichnis validieren
            if config['output_dir']:
                is_valid, error_msg = validate_output_directory(config['output_dir'])
                if not is_valid:
                    log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Ungültiges Ausgabeverzeichnis: {error_msg}")
                    return False, f"Ausgabeverzeichnis ungültig: {error_msg}"

            # Suffix validieren (falls verwendet)
            if config['filename_mode'] == 'suffix' and not config['custom_suffix'].strip():
                log_with_prefix(logger, 'error', 'MAIN', herkunft, "Suffix-Validierung fehlgeschlagen: leer")
                return False, "Suffix darf nicht leer sein"

            return is_valid, error_msg
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler bei Validierung: {str(e)}")
            return False, f"Fehler bei Validierung: {str(e)}"

    def _prepare_processing_ui(self) -> None:
        """Bereitet UI für Verarbeitung vor"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Bereite UI für Verarbeitung vor')

        try:
            # Buttons deaktivieren
            self.select_btn.configure(state="disabled")
            self.remove_btn.configure(state="disabled")
            self.clear_btn.configure(state="disabled")
            self.start_btn.pack_forget()
            self.cancel_btn.pack(side="right")

            # Status aktualisieren
            self.status_label.configure(text="🔄 Verarbeite...")
            self.progress_bar.set(0)
            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'UI für Verarbeitung vorbereitet')
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler bei UI-Vorbereitung: {str(e)}")

    def _reset_processing_ui(self) -> None:
        """Setzt UI nach Verarbeitung zurück"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Setze UI nach Verarbeitung zurück')

        try:
            # Buttons zurücksetzen
            self.select_btn.configure(state="normal")
            self.remove_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
            self.cancel_btn.pack_forget()
            self.start_btn.pack(side="right")
            self.start_btn.configure(state="normal")
            self._update_button_states()
            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'UI zurückgesetzt')
        except Exception as e:
            log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Fehler bei UI-Reset: {str(e)}")

    def _check_processing_results(self) -> None:
        """Prüft auf neue Verarbeitungsergebnisse und aktualisiert UI"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Prüfe auf neue Verarbeitungsergebnisse')

        try:
            results = self.processing_worker.get_results()
            for result in results:
                display_name = self.file_manager.find_display_name_by_path(result.file_path)
                if display_name:
                    if result.status == "processing":
                        self.file_listbox.update_item_status(display_name, "processing")
                    elif result.status == "done":
                        self.file_listbox.update_item_status(display_name, "done")
                    elif result.status == "error":
                        self.file_listbox.update_item_status(display_name, "error")
                    elif result.status == "cancelled":
                        self.file_listbox.update_item_status(display_name, "cancelled")
                    else:
                        self.file_listbox.update_item_status(display_name, "warning")

            # Fortschritt aktualisieren
            total_files = self.file_manager.get_file_count()
            if total_files > 0:
                progress = self.processing_worker.processed_files / total_files
                self.progress_bar.set(progress)

            # Fertig-Prüfung
            if self.processing_worker.is_worker_finished():
                self._reset_processing_ui()
                self._update_status_display()
                self._show_processing_summary()
            else:
                # Weiter prüfen
                self.after(500, self._check_processing_results)
        except Exception as e:
            if logger:
                log_exception(logger, e, "_check_processing_results")
            self.after(500, self._check_processing_results)

    def _show_processing_summary(self) -> None:
        """Zeigt Zusammenfassung nach Verarbeitung an"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Zeige Verarbeitungs-Zusammenfassung')

        stats = self.processing_worker.get_statistics()
        message = (
            f"Verarbeitung abgeschlossen:\n"
            f"Verarbeitet: {stats['processed_files']}\n"
            f"Erfolgreich: {stats['successful_files']}\n"
            f"Abgebrochen: {stats['cancelled_files']}\n"
            f"Fehler: {stats['error_files']}\n"
            f"Warnungen: {stats['warning_count']}"
        )
        messagebox.showinfo("Verarbeitung abgeschlossen", message)

    def _update_status_display(self) -> None:
        """Aktualisiert die Status-Anzeige"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Aktualisiere Status-Anzeige')

        file_count = self.file_manager.get_file_count()
        if file_count == 0:
            self.status_label.configure(text="✅ Bereit für Verarbeitung")
        else:
            self.status_label.configure(text=f"📁 {file_count} Dateien ausgewählt")

    def _update_button_states(self) -> None:
        """Aktualisiert Button-States basierend auf Dateianzahl"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Aktualisiere Button-States')

        has_files = self.file_manager.get_file_count() > 0
        self.start_btn.configure(state="normal" if has_files else "disabled")
        self.remove_btn.configure(state="normal" if has_files else "disabled")
        self.clear_btn.configure(state="normal" if has_files else "disabled")

    def _on_listbox_select(self, event):
        """Wird aufgerufen bei Auswahl in der Listbox"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Listbox-Auswahl geändert')

        selected = self.file_listbox.get_selected_indices()
        if selected:
            item_text = self.file_listbox.get_item(selected[0])
            cleaned_name = self._clean_display_name(item_text)
            file_path = self.file_manager.get_file_path(cleaned_name)
            if file_path:
                self.preview.load_media(file_path)
                log_with_prefix(logger, 'info', 'MAIN', herkunft, f'Vorschau für {cleaned_name} geladen')

    def _clean_display_name(self, item_text: str) -> str:
        """Bereinigt den Anzeigenamen von Status-Icons"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Bereinige Anzeigenamen: %s', item_text)

        cleaned = item_text.lstrip("🔄✅❌⏹️ ")
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Bereinigter Name: %s', cleaned)
        return cleaned

    def _on_processing_result(self, result: ProcessingResult) -> None:
        """Callback für Verarbeitungsergebnisse"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'debug', 'MAIN', herkunft, 'Verarbeitungsergebnis erhalten: %s', result)

        display_name = self.file_manager.find_display_name_by_path(result.file_path)
        if display_name:
            if result.status == "processing":
                self.file_listbox.update_item_status(display_name, "processing")
            elif result.status == "done":
                self.file_listbox.update_item_status(display_name, "done")
            elif result.status == "error":
                self.file_listbox.update_item_status(display_name, "error")
            elif result.status == "cancelled":
                self.file_listbox.update_item_status(display_name, "cancelled")
            else:
                self.file_listbox.update_item_status(display_name, "warning")

        self._update_status_display()

    def _toggle_debug_mode(self):
        """Wechselt den Debug-Modus"""
        herkunft = 'main_window.py'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Wechsle Debug-Modus')

        enabled = self.debug_var.get()
        set_debug_mode(enabled)

if __name__ == "__main__":
    from main import main
    main()

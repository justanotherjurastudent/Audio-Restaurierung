"""Hauptfenster der Anwendung"""

from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os

from .styles import Colors, Fonts, Dimensions, Icons
from .components import ParameterSlider, IntegerSlider, ButtonGrid, StatusListBox, RadioButtonGroup
from core.file_manager import FileManager
from core.workers import ProcessingWorker, ProcessingResult
from utils.validators import (
    check_ffmpeg, is_video_file, validate_file_path, validate_output_directory,
    validate_processing_params, validate_lufs_value, get_available_methods, 
    get_default_method, get_supported_video_formats
)

class AudioRestorerMainWindow(ctk.CTk):
    """Hauptfenster des Audio-Restaurationstools"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🎵 Audio-Restaurationstool v0.6.8 - Refaktorierte Version")
        self.geometry(f"{Dimensions.WINDOW_WIDTH}x{Dimensions.WINDOW_HEIGHT}")
        self.resizable(True, False)
        
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
        self._create_header()
        self._create_main_layout()
        self._create_status_bar()
        
        # Initial Button-States setzen
        self._update_button_states()
    
    def _create_header(self) -> None:
        """Erstellt den Header-Bereich"""
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=Dimensions.MAIN_PADDING, pady=10)
        
        # Titel
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎵 Audio-Restaurationstool v0.6.8",
            font=Fonts.TITLE()
        )
        title_label.pack(pady=(10, 5))
        
        # Untertitel
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="🤖 KI-Enhanced • 📊 Refaktorierte Architektur • ⏹️ Robuste Verarbeitung",
            font=Fonts.SUBTITLE()
        )
        subtitle_label.pack(pady=(0, 5))
        
        # Verfügbare Methoden anzeigen
        methods_status = self._get_methods_status_text()
        status_label = ctk.CTkLabel(
            header_frame,
            text=methods_status,
            font=Fonts.STATUS_GRAY(),
            text_color="gray"
        )
        status_label.pack(pady=(0, 10))
    
    def _get_methods_status_text(self) -> str:
        """Generiert Status-Text für verfügbare Methoden"""
        status_parts = ["Verfügbare Methoden: "]
        
        for method_id, method_info in self.available_methods.items():
            if method_info['available']:
                status_parts.append(f"✅ {method_info['name']} • ")
            else:
                status_parts.append(f"❌ {method_info['name']} • ")
        
        status_parts.append("✅ FFmpeg-Fallback")
        return "".join(status_parts)
    
    def _create_main_layout(self) -> None:
        """Erstellt das Haupt-Layout (zwei Spalten)"""
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=Dimensions.MAIN_PADDING, pady=(0, 10))
        
        # Linke Spalte - Einstellungen
        self.left_frame = ctk.CTkFrame(main_container)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        
        # Rechte Spalte - Dateien und Buttons
        self.right_frame = ctk.CTkFrame(main_container)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        self._create_settings_panel()
        self._create_files_panel()
    
    def _create_settings_panel(self) -> None:
        """Erstellt das Einstellungs-Panel (linke Spalte)"""
        self._create_lufs_section()
        self._create_method_section()
        self._create_parameters_section()
    
    def _create_lufs_section(self) -> None:
        """Erstellt die LUFS-Normalisierungs-Sektion"""
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
            from_=-23.0,
            to=-10.0,
            initial_value=-15.0,
            unit="LUFS",
            width=Dimensions.SLIDER_WIDE_WIDTH,
            help_text="-23 LUFS = Leise • -15 LUFS = Normal • -10 LUFS = Laut"
        )
        self.lufs_slider.pack(fill="x", padx=8, pady=8)
    
    def _create_method_section(self) -> None:
        """Erstellt die Methoden-Auswahl-Sektion"""
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
        
        # Standard-Tab setzen
        default_method = get_default_method()
        if default_method == "deepfilternet3":
            self.tabview.set("DeepFilterNet3")
        else:
            self.tabview.set("Audacity")
    
    def _create_deepfilter_tab(self) -> None:
        """Erstellt den DeepFilterNet3 Parameter-Tab"""
        tab = self.tabview.add("DeepFilterNet3")
        
        # DeepFilterNet3 Dämpfungsgrenze-Parameter
        self.deepfilter_attenuation = ParameterSlider(
            parent=tab,
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

    def _create_files_panel(self) -> None:
        """Erstellt das Dateien-Panel (rechte Spalte)"""
        self._create_filename_options()
        self._create_output_options()
        self._create_file_list()
        self._create_control_buttons()
    
    def _create_filename_options(self) -> None:
        """Erstellt die Dateinamen-Optionen"""
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
        self.suffix_entry.bind('<KeyPress>', lambda e: self.filename_mode_var.set("suffix"))
        self.suffix_entry.bind('<Button-1>', lambda e: self.filename_mode_var.set("suffix"))
        
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
        # Titel
        list_title = ctk.CTkLabel(
            self.right_frame,
            text="Video-Dateien",
            font=Fonts.SECTION_HEADER()
        )
        list_title.pack(pady=(8, 8))
        
        # Info-Text
        info_label = ctk.CTkLabel(
            self.right_frame,
            text="Über Button Videos auswählen",
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

    def _create_control_buttons(self) -> None:
        """Erstellt die Steuerungs-Buttons"""
        buttons_container = ctk.CTkFrame(self.right_frame)
        buttons_container.pack(fill="x", padx=15, pady=8)
        
        # Obere Button-Reihe
        top_grid = ButtonGrid(buttons_container)
        top_grid.pack(fill="x", pady=(8, 5))
        
        # Videos auswählen Button
        self.select_btn = ctk.CTkButton(
            top_grid.grid_frame,
            text=f"{Icons.FOLDER} Videos auswählen",
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
        """Öffnet Datei-Dialog zur Video-Auswahl"""
        try:
            files = filedialog.askopenfilenames(
                title="Videodateien für Audio-Restauration auswählen",
                filetypes=[
                    ("Alle Videos", " ".join(get_supported_video_formats())),
                    ("MP4-Dateien", "*.mp4"),
                    ("MOV-Dateien", "*.mov"),
                    ("MKV-Dateien", "*.mkv"),
                    ("AVI-Dateien", "*.avi"),
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
            messagebox.showerror("Fehler", f"Fehler beim Auswählen der Dateien: {str(e)}")
    
    def _add_file(self, file_path: str) -> bool:
        """
        Fügt eine Datei zur Liste hinzu
        
        Returns:
            True wenn Datei hinzugefügt wurde, False wenn bereits vorhanden oder ungültig
        """
        # Validierung
        is_valid, error_msg = validate_file_path(file_path)
        if not is_valid:
            if "Warnung" not in error_msg:
                print(f"❌ Datei übersprungen: {error_msg}")
                return False
            else:
                print(f"⚠️ {error_msg}")
        
        if not is_video_file(file_path):
            print(f"❌ Keine Video-Datei: {os.path.basename(file_path)}")
            return False
        
        # Zur Verwaltung hinzufügen
        display_name = self.file_manager.add_file(file_path)
        if display_name:
            self.file_listbox.add_item(display_name)
            self._update_button_states()
            return True
        
        return False  # Bereits vorhanden
    
    def _remove_selected(self) -> None:
        """Entfernt ausgewählte Dateien aus der Liste"""
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
            
            if removed_count > 0:
                self._update_status_display()
                self._update_button_states()
                print(f"✅ {removed_count} Dateien entfernt")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Entfernen der Dateien: {str(e)}")
    
    def _clear_list(self) -> None:
        """Leert die komplette Dateiliste"""
        if self.file_manager.get_file_count() == 0:
            return
        
        try:
            # Bestätigung bei vielen Dateien
            file_count = self.file_manager.get_file_count()
            if file_count > 5:
                response = messagebox.askyesno(
                    "Liste leeren",
                    f"Möchten Sie wirklich alle {file_count} Dateien aus der Liste entfernen?"
                )
                if not response:
                    return
            
            self.file_manager.clear_files()
            self.file_listbox.clear()
            self._update_status_display()
            self._update_button_states()
            
            print("✅ Dateiliste geleert")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Leeren der Liste: {str(e)}")
    
    def _start_processing(self) -> None:
        """Startet die Batch-Verarbeitung"""
        try:
            # Validierungen
            if self.file_manager.get_file_count() == 0:
                messagebox.showwarning("Keine Dateien", "Bitte wählen Sie erst Videodateien aus.")
                return
            
            # Parameter sammeln und validieren
            processing_config = self._collect_processing_config()
            is_valid, error_msg = self._validate_processing_config(processing_config)
            
            if not is_valid:
                messagebox.showerror("Ungültige Einstellungen", error_msg)
                return
            
            # UI für Verarbeitung vorbereiten
            self._prepare_processing_ui()
            
            # Verarbeitung starten
            file_paths = self.file_manager.get_all_files()
            self.processing_worker.start_processing(file_paths, processing_config)
            
            method_name = self.available_methods[processing_config['method']]['name']
            lufs_value = processing_config['target_lufs']
            
            self.status_label.configure(
                text=f"Verarbeitung gestartet mit {method_name} (LUFS: {lufs_value})"
            )
            
            print(f"🚀 Verarbeitung gestartet: {len(file_paths)} Dateien")
            
            # ✅ HIER erst Result-Checks starten:
            self._check_processing_results()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten der Verarbeitung: {str(e)}")
            self._reset_processing_ui()
    
    def _cancel_processing(self) -> None:
        """Bricht die laufende Verarbeitung ab"""
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
            print("⏹️ Verarbeitung wird abgebrochen...")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abbrechen: {str(e)}")
    
    def _browse_output_dir(self) -> None:
        """Öffnet Dialog zur Auswahl des Ausgabeverzeichnisses"""
        try:
            directory = filedialog.askdirectory(
                title="Zielspeicherort für restaurierte Videos auswählen"
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
            messagebox.showerror("Fehler", f"Fehler beim Auswählen des Verzeichnisses: {str(e)}")
    
    def _on_output_mode_change(self) -> None:
        """Wird aufgerufen wenn sich der Ausgabemodus ändert"""
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
            print(f"Fehler bei Ausgabemodus-Änderung: {e}")

    # ========== PROCESSING LOGIC ========== #
    
    def _collect_processing_config(self) -> Dict[str, Any]:
        """Sammelt und validiert alle Verarbeitungsparameter"""
        method = self.method_selector.get_value()
        
        # Basis-Konfiguration
        config = {
            'method': method,
            'target_lufs': self.lufs_slider.get_value(),
            'filename_mode': self.filename_mode_var.get(),
            'custom_suffix': self.suffix_var.get(),
            'output_dir': None
        }
        
        # Ausgabeverzeichnis
        if self.output_mode_var.get() == "custom_dir":
            output_dir = self.output_dir_var.get().strip()
            if output_dir:
                config['output_dir'] = output_dir
        
        # Methoden-spezifische Parameter
        if method == "deepfilternet3":
            config['method_params'] = {
                'attenuation_limit': self.deepfilter_attenuation.get_value()
            }
        elif method == "audacity":
            config['method_params'] = {
                'rauschunterdrückung': self.audacity_noise_gain.get_value(),
                'empfindlichkeit': self.audacity_sensitivity.get_value(),
                'frequenzglättung': self.audacity_freq_smoothing.get_value(),
                'window_size': 2048,
                'zeitglättung': 20
            }
        else:
            config['method_params'] = {}
        
        return config
    
    def _validate_processing_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """Validiert die Verarbeitungskonfiguration"""
        # LUFS validieren
        is_valid, error_msg = validate_lufs_value(config['target_lufs'])
        if not is_valid:
            return False, f"LUFS-Wert ungültig: {error_msg}"
        
        # Methoden-Parameter validieren
        is_valid, error_msg = validate_processing_params(
            config['method'], 
            config['method_params']
        )
        if not is_valid:
            return False, f"Parameter ungültig: {error_msg}"
        
        # Ausgabeverzeichnis validieren
        if config['output_dir']:
            is_valid, error_msg = validate_output_directory(config['output_dir'])
            if not is_valid:
                return False, f"Ausgabeverzeichnis ungültig: {error_msg}"
        
        # Suffix validieren (falls verwendet)
        if config['filename_mode'] == 'suffix' and not config['custom_suffix'].strip():
            return False, "Suffix darf nicht leer sein"
        
        return True, ""
    
    def _prepare_processing_ui(self) -> None:
        """Bereitet die UI für die Verarbeitung vor"""
        # Start-Button ausblenden, Abbrechen-Button anzeigen
        self.start_btn.pack_forget()
        self.cancel_btn.pack(side="right", padx=(10, 0))
        
        # Andere Buttons deaktivieren
        self.select_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
        self.remove_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
        self.clear_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
        
        # Progress zurücksetzen
        self.progress_bar.set(0)
    
    def _reset_processing_ui(self) -> None:
        """Setzt die UI nach der Verarbeitung zurück"""
        # Abbrechen-Button ausblenden, Start-Button anzeigen
        self.cancel_btn.pack_forget()
        self.start_btn.pack(side="right", padx=(10, 0))
        
        # Abbrechen-Button zurücksetzen
        self.cancel_btn.configure(
            state="normal", 
            text=f"{Icons.STOP} Abbrechen", 
            fg_color=Colors.ERROR_RED
        )
        
        # Button-Status aktualisieren
        self._update_button_states()
    
    def _on_processing_result(self, status: str, file_path: str, message: str) -> None:
        """Callback für Verarbeitungsergebnisse (wird vom Worker aufgerufen)"""
        # Diese Methode wird vom ProcessingWorker als Callback verwendet
        # Aber da wir Threading verwenden, erfolgt die eigentliche Verarbeitung
        # in _check_processing_results()
        pass
    
    def _check_processing_results(self) -> None:
        """Prüft regelmäßig auf neue Verarbeitungsergebnisse"""
        try:
            # Hole alle verfügbaren Ergebnisse
            results = self.processing_worker.get_results()
            
            for result in results:
                self._handle_processing_result(result)
            
            # VERBESSERTE ENDERKENNUNG
            stats = self.processing_worker.get_statistics()
            total_files = self.file_manager.get_file_count()
            worker_finished = self.processing_worker.is_worker_finished()
            
            # Prüfe mehrere Bedingungen für Ende der Verarbeitung
            all_files_processed = stats['processed_files'] >= total_files
            worker_stopped = not self.processing_worker.is_processing
            queue_empty = self.processing_worker.result_queue.empty()
            
            # Debug-Output für Problemdiagnose
            if all_files_processed or worker_finished:
                print(f"🔍 Debug - Ende-Prüfung:")
                print(f"   Verarbeitete Dateien: {stats['processed_files']}/{total_files}")
                print(f"   Worker finished: {worker_finished}")
                print(f"   Worker stopped: {worker_stopped}")
                print(f"   Queue empty: {queue_empty}")
            
            # Verarbeitung ist beendet wenn:
            # 1. Alle Dateien verarbeitet wurden ODER Worker-Thread beendet ist
            # 2. UND mindestens eine Datei verarbeitet wurde (um leere Starts zu vermeiden)
            processing_finished = (
                (all_files_processed or worker_finished) and 
                total_files > 0 and
                (stats['processed_files'] > 0 or stats['cancelled_files'] > 0)
            )
            
            if processing_finished:
                print(f"🏁 Verarbeitung erkannt als beendet")
                self._finalize_processing()
            else:
                # Weiter prüfen, aber nur wenn tatsächlich noch Verarbeitung läuft
                if self.processing_worker.is_processing and total_files > 0:
                    self.after(200, self._check_processing_results)
                elif total_files == 0:
                    print("⚠️ Keine Dateien zur Verarbeitung - Checks gestoppt")
                    
        except Exception as e:
            print(f"Fehler beim Prüfen der Ergebnisse: {e}")
            # Bei Fehlern weiter prüfen
            if self.processing_worker.is_processing:
                self.after(200, self._check_processing_results)

    
    def _handle_processing_result(self, result) -> None:
        """Verarbeitet ein einzelnes Ergebnis"""
        try:
            filename = os.path.basename(result.file_path)
            display_name = self.file_manager.find_display_name_by_path(result.file_path)
            
            if result.status == "processing":
                self.status_label.configure(text=f"Verarbeite: {filename}")
                if display_name:
                    # Finde Index in Listbox und aktualisiere
                    for i in range(self.file_listbox.size()):
                        item_text = self.file_listbox.get_item(i)
                        if display_name in item_text:
                            self.file_listbox.update_item_status(i, Icons.PROCESSING)
                            break
            
            elif result.status == "done":
                self.status_label.configure(text=f"✅ Fertig: {filename}")
                if display_name:
                    for i in range(self.file_listbox.size()):
                        item_text = self.file_listbox.get_item(i)
                        if display_name in item_text:
                            self.file_listbox.update_item_status(i, Icons.SUCCESS)
                            break
            
            elif result.status == "cancelled":
                self.status_label.configure(text=f"⏹️ Abgebrochen: {filename}")
                if display_name:
                    for i in range(self.file_listbox.size()):
                        item_text = self.file_listbox.get_item(i)
                        if display_name in item_text:
                            self.file_listbox.update_item_status(i, Icons.CANCELLED)
                            break
            
            elif result.status == "error":
                self.status_label.configure(text=f"❌ Fehler: {filename}")
                if display_name:
                    for i in range(self.file_listbox.size()):
                        item_text = self.file_listbox.get_item(i)
                        if display_name in item_text:
                            self.file_listbox.update_item_status(i, Icons.ERROR)
                            break
            
            elif result.status == "warning":
                self.status_label.configure(text=f"⚠️ Warnung: {filename}")
            
            # Progress aktualisieren
            self._update_progress_bar()
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten des Ergebnisses: {e}")
    
    def _is_processing_finished(self) -> bool:
        """Prüft ob die Verarbeitung beendet ist"""
        if not self.processing_worker.is_processing:
            return True
        
        # Zusätzlich prüfen ob Worker-Thread beendet ist
        if self.processing_worker.is_worker_finished():
            return True
        
        return False
    
    def _finalize_processing(self) -> None:
        """Schließt die Verarbeitung ab und zeigt Ergebnisse"""
        try:
            stats = self.processing_worker.get_statistics()
            total_files = self.file_manager.get_file_count()
            
            # UI zurücksetzen
            self._reset_processing_ui()
            
            # Ergebnis-Dialog anzeigen
            self._show_processing_results(stats, total_files)
            
            print(f"🏁 Verarbeitung beendet: {stats['successful_files']}/{total_files} erfolgreich")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abschließen der Verarbeitung: {str(e)}")
            self._reset_processing_ui()
    
    def _show_processing_results(self, stats: Dict[str, int], total_files: int) -> None:
        """Zeigt die Verarbeitungsergebnisse in einem Dialog"""
        try:
            was_cancelled = stats['cancelled_files'] > 0
            
            if was_cancelled:
                # Abbruch-Meldung
                title = "Verarbeitung abgebrochen"
                icon_func = messagebox.showwarning
                
                result_text = f"⏹️ Verarbeitung wurde abgebrochen!\n\n"
                result_text += f"✅ Erfolgreich: {stats['successful_files']} von {total_files} Dateien\n"
                
                if stats['cancelled_files'] > 0:
                    result_text += f"⏹️ Abgebrochen: {stats['cancelled_files']} Dateien\n"
                if stats['error_files'] > 0:
                    result_text += f"❌ Fehler: {stats['error_files']} Dateien\n"
                if stats['warning_count'] > 0:
                    result_text += f"⚠️ Warnungen: {stats['warning_count']}\n"
                
                unprocessed = total_files - stats['processed_files']
                if unprocessed > 0:
                    result_text += f"📋 Nicht verarbeitet: {unprocessed} Dateien"
                
                self.status_label.configure(
                    text=f"⏹️ Abgebrochen - {stats['successful_files']} von {total_files} Dateien verarbeitet"
                )
            
            else:
                # Erfolg-Meldung
                if stats['error_files'] > 0:
                    title = "Verarbeitung abgeschlossen (mit Fehlern)"
                    icon_func = messagebox.showerror
                elif stats['warning_count'] > 0:
                    title = "Verarbeitung abgeschlossen (mit Warnungen)"
                    icon_func = messagebox.showwarning
                else:
                    title = "Erfolgreich abgeschlossen"
                    icon_func = messagebox.showinfo
                
                result_text = f"Verarbeitung erfolgreich abgeschlossen!\n\n"
                result_text += f"✅ Erfolgreich: {stats['successful_files']}/{total_files} Dateien\n"
                
                if stats['warning_count'] > 0:
                    result_text += f"⚠️ Warnungen: {stats['warning_count']}\n"
                if stats['error_files'] > 0:
                    result_text += f"❌ Fehler: {stats['error_files']}\n"
                
                self.status_label.configure(
                    text=f"🎉 Fertig: {stats['successful_files']}/{total_files} Dateien erfolgreich verarbeitet!"
                )
            
            # Dialog anzeigen
            icon_func(title, result_text)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Anzeigen der Ergebnisse: {str(e)}")

    # ========== UTILITY METHODS ========== #
    
    def _update_button_states(self) -> None:
        """Aktualisiert den Status aller Buttons basierend auf dem aktuellen Zustand"""
        try:
            has_files = self.file_manager.get_file_count() > 0
            is_processing = self.processing_worker.is_processing
            
            if not is_processing:
                # Normal-Modus
                if has_files:
                    self.start_btn.configure(state="normal", fg_color=Colors.SUCCESS_GREEN)
                    self.remove_btn.configure(state="normal", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                    self.clear_btn.configure(state="normal", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                else:
                    self.start_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
                    self.remove_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
                    self.clear_btn.configure(state="disabled", fg_color=Colors.DISABLED_GRAY)
                
                # Select-Button ist immer aktiv im Normal-Modus
                self.select_btn.configure(state="normal", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Button-Status: {e}")
    
    def _update_status_display(self) -> None:
        """Aktualisiert die Status-Anzeige mit aktuellen Datei-Informationen"""
        try:
            file_count = self.file_manager.get_file_count()
            
            if file_count == 0:
                self.status_label.configure(text="✅ Bereit für Verarbeitung")
            else:
                total_size = self.file_manager.get_total_size_mb()
                self.status_label.configure(
                    text=f"{file_count} Dateien geladen ({total_size:.1f} MB gesamt)"
                )
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Status-Anzeige: {e}")
            self.status_label.configure(text="Status-Update fehlgeschlagen")
    
    def _update_progress_bar(self) -> None:
        """Aktualisiert die Fortschrittsanzeige"""
        try:
            stats = self.processing_worker.get_statistics()
            total_files = self.file_manager.get_file_count()
            
            if total_files > 0:
                progress = stats['processed_files'] / total_files
                self.progress_bar.set(progress)
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Fortschrittsanzeige: {e}")
    
    def _clean_display_name(self, display_name: str) -> str:
        """Entfernt Status-Icons aus Display-Namen"""
        cleaned = display_name
        for icon in [Icons.PROCESSING, Icons.SUCCESS, Icons.ERROR, Icons.CANCELLED]:
            if cleaned.startswith(icon + " "):
                cleaned = cleaned[2:]
                break
        return cleaned

if __name__ == "__main__":
    from main import main
    main()


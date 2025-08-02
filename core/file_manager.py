"""Datei-Management und Pfad-Operationen"""

import os
from typing import Dict, List, Tuple, Optional
from .exceptions import FileOperationError

class FileManager:
    """Verwaltet Dateipfade und Datei-Operationen"""
    
    def __init__(self):
        self.file_paths: Dict[str, str] = {}
    
    def add_file(self, file_path: str) -> Optional[str]:
        """Fügt eine Datei hinzu und gibt den Display-Namen zurück"""
        if not os.path.exists(file_path):
            raise FileOperationError(f"Datei existiert nicht: {file_path}")
        
        if file_path in self.file_paths.values():
            return None  # Bereits vorhanden
        
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            display_name = f"{os.path.basename(file_path)} ({size_mb:.1f} MB)"
        except OSError:
            display_name = os.path.basename(file_path)
        
        self.file_paths[display_name] = file_path
        return display_name
    
    def remove_file(self, display_name: str) -> bool:
        """Entfernt eine Datei aus der Verwaltung"""
        if display_name in self.file_paths:
            del self.file_paths[display_name]
            return True
        return False
    
    def clear_files(self) -> None:
        """Entfernt alle Dateien"""
        self.file_paths.clear()
    
    def get_file_path(self, display_name: str) -> Optional[str]:
        """Gibt den echten Pfad für einen Display-Namen zurück"""
        return self.file_paths.get(display_name)
    
    def get_all_files(self) -> Dict[str, str]:
        """Gibt alle Dateien zurück"""
        return self.file_paths.copy()
    
    def get_file_count(self) -> int:
        """Gibt die Anzahl der verwalteten Dateien zurück"""
        return len(self.file_paths)
    
    def get_total_size_mb(self) -> float:
        """Berechnet die Gesamtgröße aller Dateien in MB"""
        total_size = 0
        for file_path in self.file_paths.values():
            try:
                total_size += os.path.getsize(file_path)
            except OSError:
                continue
        return total_size / (1024 * 1024)
    
    def find_display_name_by_path(self, file_path: str) -> Optional[str]:
        """Findet den Display-Namen für einen Dateipfad"""
        for display_name, stored_path in self.file_paths.items():
            if stored_path == file_path:
                return display_name
        return None
    
    def generate_output_path(self, input_path: str, filename_mode: str, 
                        custom_suffix: str, output_dir: Optional[str]) -> str:
        """Sichere Ausgabepfad-Generierung"""
        
        # Input-Validierung (existiert und ist Datei)
        if not os.path.isfile(input_path):
            raise FileOperationError(f"Ungültiger Eingabepfad: {input_path}")
        safe_input = input_path
        safe_suffix = self._sanitize_filename_component(custom_suffix)
        
        base, ext = os.path.splitext(safe_input)
        base_name = os.path.basename(base)
        
        # Dateiname generieren
        if filename_mode == "original":
            output_name = f"{base_name}{ext}"
        else:
            output_name = f"{base_name}_{safe_suffix}{ext}"
        
        # Ausgabepfad sicher bestimmen
        if output_dir:
            safe_output_dir = self._validate_output_directory(output_dir)
            return os.path.join(safe_output_dir, output_name)
        else:
            return os.path.join(os.path.dirname(safe_input), output_name)

    def _sanitize_filename_component(self, component: str) -> str:
        """Bereinigt Dateinamen-Komponenten"""
        if not component:
            return "output"
        
        # Gefährliche Zeichen entfernen
        import re
        safe_component = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', component)
        
        # Reservierte Namen vermeiden
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 
                        'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 
                        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 
                        'LPT7', 'LPT8', 'LPT9'}
        
        if safe_component.upper() in reserved_names:
            safe_component += "_file"
        
        # Länge begrenzen
        return safe_component[:50]

    def _validate_output_directory(self, output_dir: str) -> str:
        """Validiert Ausgabe-Verzeichnisse gegen Path Traversal"""
        normalized = os.path.normpath(output_dir)
        
        # Path Traversal verhindern
        if ".." in normalized:
            raise ValueError("Path Traversal in Ausgabeverzeichnis erkannt")
        
        # Absolute Pfade außerhalb erlaubter Bereiche verhindern
        if os.path.isabs(normalized):
            # Prüfe ob in erlaubten Bereichen (z.B. User-Verzeichnis)
            user_home = os.path.expanduser("~")
            if not normalized.startswith(user_home):
                raise ValueError("Ausgabe außerhalb des Benutzerverzeichnisses nicht erlaubt")
        
        return normalized

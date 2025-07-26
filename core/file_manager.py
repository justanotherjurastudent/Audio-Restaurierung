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
        """Generiert den Ausgabe-Pfad für eine verarbeitete Datei"""
        base, ext = os.path.splitext(input_path)
        base_name = os.path.basename(base)
        
        if filename_mode == "original":
            output_name = f"{base_name}{ext}"
            # Bei Konflikten Nummer hinzufügen
            counter = 1
            while True:
                if output_dir:
                    test_path = os.path.join(output_dir, output_name)
                else:
                    test_path = os.path.join(os.path.dirname(input_path), output_name)
                
                if not os.path.exists(test_path) or test_path == input_path:
                    break
                output_name = f"{base_name}_({counter}){ext}"
                counter += 1
        else:  # suffix mode
            output_name = f"{base_name}_{custom_suffix}{ext}"
        
        if output_dir:
            return os.path.join(output_dir, output_name)
        else:
            return os.path.join(os.path.dirname(input_path), output_name)

"""Validierung und Hilfsfunktionen"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

from utils.logger import log_with_prefix, get_normalized_logger

# Logger konfigurieren
logger = get_normalized_logger('validators')

def check_dependencies() -> bool:
    """
    Prüft alle notwendigen Abhängigkeiten
    
    Returns:
        True wenn alle Abhängigkeiten verfügbar sind
    """
    missing_deps = []
    
    # Python-Pakete prüfen
    required_packages = {
        'customtkinter': 'customtkinter',
        'soundfile': 'soundfile', 
        'numpy': 'numpy',
        'pyloudnorm': 'pyloudnorm',
        'scipy': 'scipy'
    }
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            msg = f"✅ {package_name} verfügbar"

            log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)
        except ImportError:
            missing_deps.append(package_name)
            msg = f"❌ {package_name} nicht verfügbar"

            log_with_prefix(logger, 'error', 'VALIDATORS', 'check_dependencies', msg)

    # FFmpeg prüfen
    if not check_ffmpeg():
        missing_deps.append('FFmpeg')
        msg = "❌ FFmpeg nicht verfügbar"

        log_with_prefix(logger, 'error', 'VALIDATORS', 'check_dependencies', msg)
    else:
        msg = "✅ FFmpeg verfügbar"

        log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)

    # DeepFilterNet3 prüfen (optional)
    try:
        import df.enhance
        msg = "✅ DeepFilterNet3 verfügbar"

        log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)
    except ImportError:
        msg = "⚠️ DeepFilterNet3 nicht verfügbar (optional)"

        log_with_prefix(logger, 'warning', 'VALIDATORS', 'check_dependencies', msg)

    # SpeechBrain AI prüfen (optional)
    try:
        import speechbrain
        msg = "✅ SpeechBrain AI verfügbar"

        log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)
    except ImportError:
        msg = "⚠️ SpeechBrain AI nicht verfügbar (optional)"

        log_with_prefix(logger, 'warning', 'VALIDATORS', 'check_dependencies', msg)
    
    if missing_deps:
        msg = f"\n❌ Fehlende Abhängigkeiten: {', '.join(missing_deps)}"

        log_with_prefix(logger, 'error', 'VALIDATORS', 'check_dependencies', msg)
        
        msg = "Bitte installieren Sie diese mit: pip install -r requirements.txt"

        log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)

        if 'FFmpeg' in missing_deps:
            msg = "FFmpeg muss separat installiert werden: https://ffmpeg.org/download.html"

            log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)
        return False
    
    msg = "\n✅ Alle notwendigen Abhängigkeiten verfügbar"

    log_with_prefix(logger, 'info', 'VALIDATORS', 'check_dependencies', msg)
    return True

def check_ffmpeg() -> bool:
    """Prüft FFmpeg-Verfügbarkeit"""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
        return False

def is_video_file(file_path: str) -> tuple[bool, str]:
    """Sichere Video-Datei-Validierung mit Magic Bytes Check"""
    
    try:
        # Basis-Checks
        if not os.path.exists(file_path):
            return False, "Datei existiert nicht"
        
        if not os.path.isfile(file_path):
            return False, "Pfad ist keine Datei"
        
        # Dateigröße prüfen
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "Datei ist leer"
        
        if file_size > 5 * 1024 * 1024 * 1024:  # 5GB Limit
            return False, "Datei zu groß (>5GB)"
        
        # Extension-Check
        video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.m4v', '.webm', '.flv', '.wmv'}
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in video_extensions:
            return False, "Unsupported format"
        
        # NEU: Magic Number Check (File Header)
        if not _verify_video_magic_bytes(file_path):
            return False, "Datei entspricht nicht dem Format (Magic Bytes)"
        
        return True, "OK"
        
    except (OSError, PermissionError) as e:
        return False, f"Dateizugriff fehlgeschlagen: {e}"

def _verify_video_magic_bytes(file_path: str) -> bool:
    """Prüft Video-File-Headers - NEU HINZUFÜGEN"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
            
        # MP4/MOV
        if b'ftyp' in header:
            return True
        
        # AVI
        if header.startswith(b'RIFF') and b'AVI ' in header:
            return True
        
        # MKV
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return True
        
        # WebM
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return True
            
        return False
        
    except:
        return False


def get_supported_video_formats() -> List[str]:
    """Gibt Liste unterstützter Video-Formate zurück"""
    return [
        "*.mp4", "*.mov", "*.mkv", "*.avi", "*.m4v", 
        "*.webm", "*.flv", "*.wmv", "*.mpg", "*.mpeg"
    ]

def validate_file_path(file_path: str) -> tuple[bool, str]:
    """
    Validiert einen Dateipfad
    
    Returns:
        Tuple[is_valid, error_message]
    """
    if not file_path:
        return False, "Dateipfad ist leer"
    
    if not os.path.exists(file_path):
        return False, f"Datei existiert nicht: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"Pfad ist keine Datei: {file_path}"
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "Datei ist leer"
        
        # Warnung bei sehr großen Dateien (>2GB)
        if file_size > 2 * 1024 * 1024 * 1024:
            return True, f"Warnung: Sehr große Datei ({file_size / (1024**3):.1f} GB)"
    
    except OSError as e:
        return False, f"Fehler beim Zugriff auf Datei: {e}"
    
    return True, ""

def validate_output_directory(dir_path: Optional[str]) -> tuple[bool, str]:
    """
    Validiert ein Ausgabeverzeichnis
    
    Returns:
        Tuple[is_valid, error_message]
    """
    if not dir_path:
        return True, ""  # Kein Verzeichnis ist OK (dann neben Original)
    
    # NEU: Path Traversal verhindern
    normalized = os.path.normpath(dir_path)
    if ".." in normalized:
        return False, "Path Traversal in Ausgabeverzeichnis erkannt"
    
    # NEU: Absolute Pfade außerhalb User-Bereiche verhindern
    if os.path.isabs(normalized):
        user_home = os.path.expanduser("~")
        if not normalized.startswith(user_home):
            return False, "Ausgabe außerhalb des Benutzerverzeichnisses nicht erlaubt"
    
    if not os.path.exists(dir_path):
        return False, f"Verzeichnis existiert nicht: {dir_path}"
    
    if not os.path.isdir(dir_path):
        return False, f"Pfad ist kein Verzeichnis: {dir_path}"
    
    # Schreibrechte testen
    try:
        test_file = os.path.join(dir_path, ".test_write_permissions")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, IOError) as e:
        return False, f"Keine Schreibrechte im Verzeichnis: {e}"
    
    return True, ""

def validate_processing_params(method: str, params: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validiert Verarbeitungsparameter
    
    Returns:
        Tuple[is_valid, error_message]
    """
    if method == "deepfilternet3":
        attenuation = params.get('attenuation_limit', 80.0)
        if not isinstance(attenuation, (int, float)):
            return False, "Dämpfungsgrenze muss eine Zahl sein"
        if not 20.0 <= attenuation <= 100.0:
            return False, "Dämpfungsgrenze muss zwischen 20 und 100 dB liegen"
    
    elif method == "audacity":
        # Rauschunterdrückung
        noise_gain = params.get('rauschunterdrückung', 12.0)
        if not isinstance(noise_gain, (int, float)):
            return False, "Rauschunterdrückung muss eine Zahl sein"
        if not 6.0 <= noise_gain <= 30.0:
            return False, "Rauschunterdrückung muss zwischen 6 und 30 dB liegen"
        
        # Empfindlichkeit
        sensitivity = params.get('empfindlichkeit', 6.0)
        if not isinstance(sensitivity, (int, float)):
            return False, "Empfindlichkeit muss eine Zahl sein"
        if not 0.0 <= sensitivity <= 20.0:
            return False, "Empfindlichkeit muss zwischen 0 und 20 liegen"
        
        # Frequenz-Glättung
        freq_smooth = params.get('frequenzglättung', 0)
        if not isinstance(freq_smooth, int):
            return False, "Frequenz-Glättung muss eine ganze Zahl sein"
        if not 0 <= freq_smooth <= 10:
            return False, "Frequenz-Glättung muss zwischen 0 und 10 liegen"
    
    else:
        return False, f"Unbekannte Methode: {method}"
    
    return True, ""

def validate_lufs_value(lufs: float) -> tuple[bool, str]:
    """
    Validiert LUFS-Wert
    
    Returns:
        Tuple[is_valid, error_message]
    """
    if not isinstance(lufs, (int, float)):
        return False, "LUFS-Wert muss eine Zahl sein"
    
    if not -30.0 <= lufs <= 0.0:
        return False, "LUFS-Wert muss zwischen -30 und 0 liegen"
    
    # Warnungen für unübliche Werte
    if lufs > -10.0:
        return True, f"Warnung: Sehr lauter LUFS-Wert ({lufs:.1f})"
    elif lufs < -30.0:
        return True, f"Warnung: Sehr leiser LUFS-Wert ({lufs:.1f})"
    
    return True, ""

def format_file_size(size_bytes: int) -> str:
    """
    Formatiert Dateigröße human-readable
    
    Args:
        size_bytes: Größe in Bytes
        
    Returns:
        Formatierte Größe (z.B. "1.5 GB")
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def format_duration(seconds: float) -> str:
    """
    Formatiert Zeitdauer human-readable
    
    Args:
        seconds: Dauer in Sekunden
        
    Returns:
        Formatierte Dauer (z.B. "2:30" oder "1h 23m")
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}:{secs:02d}"
    else:
        return f"{secs}s"

def sanitize_filename(filename: str) -> str:
    """
    Bereinigt Dateinamen von ungültigen Zeichen
    
    Args:
        filename: Original-Dateiname
        
    Returns:
        Bereinigter Dateiname
    """
    # Ungültige Zeichen für Windows und Unix
    invalid_chars = '<>:"/\\|?*'
    
    # Ersetze ungültige Zeichen durch Unterstriche
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Entferne führende/abschließende Leerzeichen und Punkte
    sanitized = sanitized.strip(' .')
    
    # Maximal 255 Zeichen (Dateisystem-Limit)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext
    
    # Fallback falls komplett leer
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

def get_available_methods() -> Dict[str, Dict[str, Any]]:
    """
    Gibt verfügbare Verarbeitungsmethoden zurück
    
    Returns:
        Dict mit Methoden-Informationen
    """
    methods = {
        'audacity': {
            'name': 'Audacity Spektral',
            'description': 'Zuverlässig • Konfigurierbar',
            'available': True,
            'sample_rate': 22050
        }
    }
    
    # DeepFilterNet3 prüfen
    try:
        import df.enhance
        methods['deepfilternet3'] = {
            'name': 'DeepFilterNet3 (KI)',
            'description': 'Beste QualitätModernste KI',
            'available': True,
            'sample_rate': 48000
        }
    except ImportError:
        methods['deepfilternet3'] = {
            'name': 'DeepFilterNet3 (KI)',
            'description': 'Nicht verfügbar - Installation erforderlich',
            'available': False,
            'sample_rate': 48000
        }
    
    return methods

def get_default_method() -> str:
    """Gibt die Standard-Verarbeitungsmethode zurück"""
    methods = get_available_methods()
    
    # Bevorzuge DeepFilterNet3 wenn verfügbar
    if methods['deepfilternet3']['available']:
        return 'deepfilternet3'
    else:
        return 'audacity'

"""Logging-System für das Audio-Restaurationstool - EXE-sicher"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

from .config import Config, APP_NAME, APP_VERSION, LOG_FORMAT, LOG_DATE_FORMAT

# Globale Session-ID für einmalige Log-Datei pro Programmstart
_SESSION_ID = None
_LOGGER_INITIALIZED = False

class EXESafeConsoleFormatter(logging.Formatter):
    """Formatter der Emojis für EXE-Konsolen-Ausgabe ersetzt"""
    
    # Emoji-Mapping für sichere Konsolen-Ausgabe
    EMOJI_MAP = {
        '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]', '🔄': '[PROCESSING]',
        '🤖': '[AI]', '🎵': '[AUDIO]', '🎛️': '[MIXER]', '🚀': '[START]',
        '⏹️': '[STOP]', '🔍': '[DEBUG]', '📁': '[FOLDER]', '🗑️': '[DELETE]',
        '⏸️': '[PAUSE]', '🏁': '[FINISH]', '💀': '[KILL]', '🔒': '[LOCK]',
        '🧹': '[CLEANUP]', '📊': '[STATS]', '⏰': '[TIMEOUT]', '🎯': '[TARGET]',
        '🔧': '[DEBUG]'
    }

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        formatted_message = super().format(record)
        if getattr(sys, 'frozen', False):
            safe_message = formatted_message
            for emoji, replacement in self.EMOJI_MAP.items():
                safe_message = safe_message.replace(emoji, replacement)
            try:
                safe_message.encode('ascii')
            except UnicodeEncodeError:
                safe_message = safe_message.encode('ascii', errors='replace').decode('ascii')
            return safe_message
        return formatted_message

class SafeFileFormatter(logging.Formatter):
    """Custom-Formatter für File-Handler, der fehlende Felder handhabt"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        # Fehlende Attribute mit Defaults füllen
        if not hasattr(record, 'herkunft'):
            record.herkunft = 'Unbekannt'
        
        try:
            return super().format(record)
        except (KeyError, AttributeError) as e:
            # Fallback-Format bei fehlenden Keys
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"{timestamp}\t{record.levelname}\t{getattr(record, 'herkunft', 'Unbekannt')}\t{record.getMessage()}"

def set_debug_mode(enabled: bool) -> None:
    """Aktiviert oder deaktiviert den Debug-Modus"""
    Config.set_debug_mode(enabled)
    
    # ✅ KORREKTUR: Alle Logger in der Hierarchie aktualisieren
    root_logger = logging.getLogger("AudioRestorer")
    root_logger.setLevel(logging.DEBUG if enabled else logging.INFO)
    
    # Alle Handler aktualisieren
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.DEBUG if enabled else logging.INFO)
    
    # ✅ NEU: Child-Logger auch aktualisieren
    for name in logging.Logger.manager.loggerDict:
        if name.startswith("AudioRestorer") or name in ["audacity", "speechbrain", "deepfilter"]:
            child_logger = logging.getLogger(name)
            child_logger.setLevel(logging.DEBUG if enabled else logging.INFO)
    
    root_logger.info(f"🔧 Debug-Modus {'aktiviert' if enabled else 'deaktiviert'}")

def _determine_log_directory() -> str:
    """Bestimmt das Log-Verzeichnis robust für alle Modi"""
    if getattr(sys, 'frozen', False):
        # EXE-Modus: Versuche mehrere Optionen
        exe_dir = os.path.dirname(sys.executable)
        possible_dirs = [
            os.path.join(exe_dir, "logs"),  # logs-Unterordner neben EXE
            exe_dir,  # Neben der EXE
            os.path.join(os.path.expanduser("~"), "Documents", "AudioRestorer", "logs"),  # User Documents
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "AudioRestorer", "logs"),  # AppData Local
            os.path.join(os.environ.get('TEMP', '/tmp'), "AudioRestorer", "logs")  # Temp-Fallback
        ]

        for log_dir in possible_dirs:
            try:
                # Versuche Verzeichnis zu erstellen
                os.makedirs(log_dir, exist_ok=True)
                # Test ob schreibbar
                test_file = os.path.join(log_dir, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"[LOG] EXE-Log-Verzeichnis erfolgreich: {log_dir}")
                return log_dir
            except (OSError, PermissionError) as e:
                print(f"[LOG] Verzeichnis {log_dir} nicht verfügbar: {e}")
                continue
        
        # Fallback: Aktuelles Verzeichnis
        fallback_dir = os.getcwd()
        print(f"[LOG] Verwende Fallback-Verzeichnis: {fallback_dir}")
        return fallback_dir
    else:
        # Entwicklungsmodus: Projektordner/logs
        try:
            # utils/logger.py -> utils -> projekt_root
            script_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
            project_root = os.path.dirname(script_dir)  # projekt_root/
            log_dir = os.path.join(project_root, "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # Test ob schreibbar
            test_file = os.path.join(log_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"[LOG] Development-Log-Verzeichnis: {log_dir}")
            return log_dir
        except Exception as e:
            print(f"[LOG] Fehler bei Development-Log-Verzeichnis: {e}")
            # Fallback: Aktuelles Verzeichnis
            fallback_dir = os.getcwd()
            print(f"[LOG] Verwende Fallback: {fallback_dir}")
            return fallback_dir

def get_session_id() -> str:
    """Gibt einmalige Session-ID für diese Programmsitzung zurück"""
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _SESSION_ID

def setup_logger(app_name: str = "AudioRestorer") -> logging.Logger:
    """Setup Logger - nur einmal pro Session"""
    global _LOGGER_INITIALIZED
    
    logger = logging.getLogger(app_name)
    
    # Verhindere mehrfache Initialisierung
    if _LOGGER_INITIALIZED and logger.handlers:
        return logger

    # Einmalige Log-Datei pro Session
    log_dir = _determine_log_directory()
    session_id = get_session_id()
    log_file = os.path.join(log_dir, f"{app_name}_{session_id}.log")

    # Logger konfigurieren (nur einmal)
    logger.setLevel(logging.INFO)
    
    # Alte Handler entfernen falls vorhanden
    if logger.handlers:
        logger.handlers.clear()

    # File Handler mit Session-ID
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # ✅ KORREKTUR: Strukturiertes Format für File-Handler
        file_formatter = SafeFileFormatter(
            "%(asctime)s\t%(levelname)s\t%(herkunft)s\t%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[LOG] Warnung: Log-Datei konnte nicht erstellt werden: {e}")

    # Console Handler mit EXE-sicherer Formatierung
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = EXESafeConsoleFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    _LOGGER_INITIALIZED = True

    # Nur beim ersten Setup Session-Info loggen
    logger.info("="*60)
    logger.info(f"🎵 Audio-Restaurationstool Session {session_id} gestartet")
    logger.info(f"📁 Log-Datei: {log_file}")
    logger.info("="*60)
    
    return logger

# ✅ KORREKTUR: Vereinfachte und robuste log_with_prefix Funktion
def log_with_prefix(logger, level, prefix, herkunft, message, *args):
    """Logs mit Präfix und Herkunft - vereinfacht und robust"""
    
    # Formatierung unterstützen
    if args:
        try:
            formatted_message = message % args
        except (TypeError, ValueError):
            formatted_message = f"{message} {args}"  # Fallback
    else:
        formatted_message = message
    
    # Finale Log-Nachricht zusammenstellen
    final_message = f"[{prefix.upper()}] {formatted_message}"
    
    # ✅ KORREKTUR: Logger-Level richtig setzen und extra-Daten korrekt übergeben
    log_func = getattr(logger, level.lower(), logger.info)
    
    # ✅ NEU: Herkunft als extra-Parameter für File-Handler
    try:
        log_func(final_message, extra={'herkunft': herkunft})
    except (TypeError, AttributeError):
        # Fallback ohne extra-Parameter
        log_func(final_message)

# ✅ NEU: Hilfsfunktion um alle Logger auf einen Namen zu normalisieren
def get_normalized_logger(name: str = None) -> logging.Logger:
    """Gibt normalisierten Logger zurück - alle verwenden 'AudioRestorer' Hierarchie"""
    if name is None or name == __name__:
        return logging.getLogger("AudioRestorer")
    
    # Module-spezifische Logger als Child von AudioRestorer
    if name in ['audacity', 'deepfilter', 'ffmpeg_utils', 'speechbrain', 'voice_enhancer', 'processors', 'workers']:
        return logging.getLogger(f"AudioRestorer.{name}")
    
    return logging.getLogger("AudioRestorer")

def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """Detailliertes Exception-Logging - EXE-sicher"""
    import traceback
    
    logger.error(f"❌ EXCEPTION in {context}:")
    logger.error(f"Exception Type: {type(exception).__name__}")
    logger.error(f"Exception Message: {str(exception)}")
    logger.error("Traceback:")
    
    # Vollständiger Traceback
    for line in traceback.format_exc().splitlines():
        logger.error(f"  {line}")
    logger.error("-" * 40)

def log_system_info(logger: logging.Logger):
    """Sammelt und loggt System-Informationen - EXE-sicher"""
    try:
        import platform
        import psutil
        
        logger.info("🔍 SYSTEM INFORMATION:")
        logger.info(f"OS: {platform.system()} {platform.release()}")
        logger.info(f"Architecture: {platform.architecture()[0]}")
        logger.info(f"Processor: {platform.processor()}")
        logger.info(f"RAM Total: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        logger.info(f"RAM Available: {psutil.virtual_memory().available / (1024**3):.1f} GB")
        logger.info(f"Disk Free: {psutil.disk_usage('.').free / (1024**3):.1f} GB")
    except ImportError:
        logger.warning("⚠️ psutil nicht verfügbar - System-Info übersprungen")
    except Exception as e:
        logger.warning(f"⚠️ System-Info-Sammlung fehlgeschlagen: {e}")

def sanitize_log_message(message: str) -> str:
    """Entfernt sensitive Informationen aus Log-Nachrichten"""
    import re
    
    # Pfade anonymisieren
    sanitized = re.sub(r'[A-Za-z]:\\[^:\s]+', '[PATH]', message)
    sanitized = re.sub(r'/[^\s]+', '[PATH]', sanitized)
    
    # IP-Adressen (falls vorhanden)
    sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', sanitized)
    
    return sanitized

def log_safe(logger: logging.Logger, level: str, message: str):
    """Sicheres Logging mit Sanitization"""
    safe_message = sanitize_log_message(message)
    getattr(logger, level)(safe_message)

"""
Audio-Restaurationstool v1.0.0
"""

import sys
from typing import NoReturn

# NEU: Import für log_with_prefix (behebt 'not defined'-Fehler)
from utils.logger import log_with_prefix

from gui.main_window import AudioRestorerMainWindow
from utils.validators import check_dependencies
from utils.logger import setup_logger, log_exception, log_system_info  # NEU

def setup_exe_environment():
    """Konfiguriert Umgebung für .exe-Version"""
    herkunft = 'main.py'
    logger = setup_logger("AudioRestorer")
    import sys
    import os
    if getattr(sys, 'frozen', False):
        # ULTIMATIVE LOGGER-DEAKTIVIERUNG GANZ AM ANFANG
        try:
            log_with_prefix(logger, 'info', 'MAIN', herkunft, '🔍 .exe-Modus erkannt - Konfiguriere Umgebung')
            # Deaktiviere alle bekannten Logger-Systeme
            os.environ['LOGURU_LEVEL'] = 'CRITICAL'
            os.environ['DF_LOG_LEVEL'] = 'CRITICAL'
            os.environ['DF_LOG_FILE'] = '/dev/null' if os.name != 'nt' else 'NUL'
            # Python Logging-Level hochsetzen
            import logging
            logging.getLogger().setLevel(logging.CRITICAL)
            log_with_prefix(logger, 'info', 'MAIN', herkunft, '🔍 Alle Logger-Systeme auf CRITICAL gesetzt')
        except Exception as e:
            log_with_prefix(logger, 'warning', 'MAIN', herkunft, f'🔍 Logger-Deaktivierung fehlgeschlagen: {e}')
        # GPU deaktivieren
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        
        # DeepFilterNet3 Pfade
        base_path = sys._MEIPASS
        possible_model_dirs = [
            os.path.join(base_path, 'DeepFilterNet3_models'),
            os.path.join(base_path, 'df', 'models'),
            os.path.join(base_path, 'models')
        ]
        for model_dir in possible_model_dirs:
            if os.path.exists(model_dir):
                os.environ['DF_MODEL_BASE_DIR'] = model_dir
                log_with_prefix(logger, 'info', 'MAIN', herkunft, f'🔍 Model-Verzeichnis gesetzt: {model_dir}')
                break
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        os.environ['OMP_NUM_THREADS'] = '1'
        log_with_prefix(logger, 'info', 'MAIN', herkunft, '✅ .exe-Umgebung mit Logger-Deaktivierung konfiguriert')

def main() -> NoReturn:
    """Haupteinstiegspunkt der Anwendung"""
    herkunft = 'main.py'
    logger = setup_logger("AudioRestorer")
    try:
        # NEU: .exe-Umgebung einrichten
        setup_exe_environment()
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Audio-Restaurationstool v1.0.0 wird gestartet...')
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Anwendungsstart')
        # System-Info sammeln
        log_system_info(logger)
        # Abhängigkeiten prüfen
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Prüfe Dependencies...')
        if not check_dependencies():
            log_with_prefix(logger, 'error', 'MAIN', herkunft, 'Dependencies-Check fehlgeschlagen')
            sys.exit(1)
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Dependencies erfolgreich validiert')
        # GUI starten
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Starte GUI...')
        app = AudioRestorerMainWindow()
        app.logger = logger  # Logger an GUI weitergeben
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'GUI erfolgreich initialisiert')
        app.mainloop()
    except Exception as e:
        # Kritische Fehler loggen
        log_exception(logger, e, "main()")
        log_with_prefix(logger, 'error', 'MAIN', herkunft, f"Kritischer Fehler: {e}")
        log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Details wurden in die Log-Datei geschrieben.')
        # Error-Dialog für Benutzer
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "Kritischer Fehler",
                f"Das Programm ist aufgrund eines Fehlers beendet worden.\n\n"
                f"Fehler: {str(e)}\n\n"
                f"Detaillierte Informationen finden Sie in der Log-Datei im 'logs' Ordner."
            )
        except:
            pass
        sys.exit(1)
    finally:
        if 'logger' in locals():
            log_with_prefix(logger, 'info', 'MAIN', herkunft, 'Anwendung beendet')

if __name__ == "__main__":
    main()

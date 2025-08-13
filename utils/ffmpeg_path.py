# utils/ffmpeg_path.py
"""
Hilfsfunktion zum Finden des Pfades zu den gebündelten FFMpeg-Dateien.
"""
import sys
import os
import logging

logger = logging.getLogger(__name__)

def get_ffmpeg_path(executable_name: str) -> str:
    """
    Ermittelt den Pfad zur FFMpeg- oder FFprobe-Executable.

    Prüft zuerst, ob die Anwendung als PyInstaller-Bundle läuft und sucht
    im temporären `_MEIPASS`-Verzeichnis. Wenn nicht, wird der
    lokale `ffmpeg`-Ordner geprüft.

    Args:
        executable_name (str): Der Name der ausführbaren Datei ('ffmpeg.exe' oder 'ffprobe.exe').

    Returns:
        str: Der absolute Pfad zur Executable.
    """
    # Prüfen, ob die Anwendung als PyInstaller-Bundle läuft
    if hasattr(sys, '_MEIPASS'):
        # Pfad innerhalb des entpackten Bundles
        base_path = sys._MEIPASS
        ffmpeg_dir = os.path.join(base_path, 'ffmpeg')
    else:
        # Pfad für die Entwicklungsumgebung (relativ zum Projektstamm)
        base_path = os.path.abspath(".")
        ffmpeg_dir = os.path.join(base_path, 'ffmpeg')

    executable_path = os.path.join(ffmpeg_dir, executable_name)

    if os.path.exists(executable_path):
        logger.info(f"✅ {executable_name} gefunden in: {executable_path}")
        return executable_path
    else:
        logger.warning(f"⚠️ {executable_name} nicht im erwarteten Pfad gefunden: {executable_path}. Fallback auf PATH.")
        # Als Fallback wird der Name der Executable zurückgegeben,
        # sodass `subprocess` sie im System-PATH suchen kann.
        return executable_name

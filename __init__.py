"""
Audio-Restaurationstool v0.6.8 - Refaktorierte Version

Copyright (C) 2025 [Lukas Collier]
GPL-3.0 License
"""

__version__ = "0.6.8"
__author__ = "Lukas Collier"
__license__ = "GPL-3.0"

# Hauptklassen für externe Nutzung verfügbar machen
from gui.main_window import AudioRestorerMainWindow
from audio.processors import VideoProcessor
from core.exceptions import AudioRestorerException

__all__ = [
    "AudioRestorerMainWindow",
    "VideoProcessor", 
    "AudioRestorerException"
]

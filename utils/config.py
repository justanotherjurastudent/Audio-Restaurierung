"""Globale Konfigurationsvariablen für das Audio-Restaurationstool"""

from typing import Dict, Any

# Debug-Einstellungen
DEBUG_MODE = False

# Versions-Info
APP_VERSION = "1.0.0"
APP_NAME = "Audio-Restaurationstool"

# Logging-Einstellungen
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Verarbeitungs-Einstellungen
DEFAULT_MAX_FILE_SIZE_GB = 5.0
DEFAULT_LUFS_TARGET = -23.0

# Audio-Format-Einstellungen
DEEPFILTER_SAMPLE_RATE = 48000  # Hz - DeepFilterNet3 benötigt 48kHz
DEFAULT_SAMPLE_RATE = 22050     # Hz - Standard für andere Methoden
WINDOW_OVERLAP_FACTOR = 4

# Audacity-Parameter
AUDACITY_DEFAULT_PARAMS = {
    'window_size': 2048,
    'noise_gain_db': 12.0,      # Rauschunterdrückungs-Stärke
    'sensitivity': 6.0,         # Erkennungsempfindlichkeit
    'smoothing_time_ms': 20,    # Zeitliche Glättung
    'freq_smoothing_bands': 0   # Frequenz-Glättung
}

AUDACITY_PARAM_RANGES = {
    'noise_gain_db': (6.0, 30.0),
    'sensitivity': (0.0, 20.0),
    'smoothing_time_ms': (0, 100),
    'freq_smoothing_bands': (0, 10)
}

# DeepFilterNet3-Parameter
DEEPFILTER_DEFAULT_PARAMS = {
    'attenuation_limit': 80.0   # dB - Dämpfungsgrenze
}

DEEPFILTER_PARAM_RANGES = {
    'attenuation_limit': (20.0, 100.0)
}

# ----------------- Voice Enhancement -----------------
VOICE_DEFAULTS = {
    "clarity_boost": 3.0,           # 2-4 kHz für Sprachverständlichkeit
    "warmth_boost": 2.5,            # 120-250 Hz für Körper und Fülle
    "bandwidth_extension": 1.5,     # Wiederherstellung hoher Frequenzen (6-12 kHz)
    "harmonic_restoration": 1.0,    # Reparatur von Kompressionsartefakten
    "compression_ratio": 2.0,          # NEU: 2:1 Kompression
    "compression_threshold": -18.0,  # NEU: -18 dB Threshold
}

VOICE_RANGES = {
    "clarity_boost": (0.0, 5.0),
    "warmth_boost": (0.0, 5.0), 
    "bandwidth_extension": (0.0, 5.0),
    "harmonic_restoration": (0.0, 5.0),
    "compression_ratio": (1.0, 5.0),         # NEU: 1:1 bis 5:1
    "compression_threshold": (-30.0, -10.0), # NEU: -30 bis -10 dB
}

VOICE_DESCRIPTIONS = {
    "clarity_boost": "Hebt 2-4 kHz für bessere Sprachverständlichkeit an.",
    "warmth_boost": "Betont 120-250 Hz für volleren, körperlichen Klang.",
    "bandwidth_extension": "Stellt hohe Frequenzen wieder her, die durch Kompression verloren gingen.",
    "harmonic_restoration": "Repariert Verzerrungen und Kompressionsartefakte für natürlicheren Klang.",
    "compression_ratio": "Kompression für gleichmäßigere Lautstärke (2:1 = subtil, 4:1 = stark).",
    "compression_threshold": "Pegel ab dem komprimiert wird (-18 dB = Standard).",
}

# ----------------- SpeechBrain Voice Enhancement -----------------
SPEECHBRAIN_DEFAULTS = {
    "enhancement_strength": 1.0,    # 0.5-2.0 (Mischung Original/Enhanced)
    "normalize_audio": True,        # Audio-Normalisierung nach Enhancement
    "model_variant": "mtl-mimic",   # Modell-Variante
}

SPEECHBRAIN_RANGES = {
    "enhancement_strength": (0.5, 2.0),
}

SPEECHBRAIN_DESCRIPTIONS = {
    "enhancement_strength": "Enhancement-Stärke (0.5=subtil, 1.0=standard, 2.0=stark)",
    "normalize_audio": "Audio nach Enhancement normalisieren",
    "model_variant": "SpeechBrain-Modell-Variante (mtl-mimic=Standard)",
}

class Config:
    """Zentrale Konfigurationsklasse"""
    
    @staticmethod
    def set_debug_mode(enabled: bool) -> None:
        """Setzt den Debug-Modus"""
        global DEBUG_MODE
        DEBUG_MODE = enabled
    
    @staticmethod
    def get_debug_mode() -> bool:
        """Gibt den aktuellen Debug-Modus zurück"""
        return DEBUG_MODE
    
    @staticmethod
    def get_app_info() -> Dict[str, str]:
        """Gibt Basis-Informationen über die Anwendung zurück"""
        return {
            "name": APP_NAME,
            "version": APP_VERSION
        }
    
    @staticmethod
    def get_audacity_defaults() -> Dict[str, Any]:
        """Gibt Standard-Parameter für Audacity-Rauschreduzierung zurück"""
        return AUDACITY_DEFAULT_PARAMS.copy()
    
    @staticmethod
    def get_audacity_ranges() -> Dict[str, tuple]:
        """Gibt Parameter-Bereiche für Audacity-Rauschreduzierung zurück"""
        return AUDACITY_PARAM_RANGES.copy()
    
    @staticmethod
    def get_deepfilter_defaults() -> Dict[str, Any]:
        """Gibt Standard-Parameter für DeepFilterNet3 zurück"""
        return DEEPFILTER_DEFAULT_PARAMS.copy()
    
    @staticmethod
    def get_deepfilter_ranges() -> Dict[str, tuple]:
        """Gibt Parameter-Bereiche für DeepFilterNet3 zurück"""
        return DEEPFILTER_PARAM_RANGES.copy()
    
    @staticmethod
    def get_voice_defaults() -> Dict[str, Any]:
        return VOICE_DEFAULTS.copy()

    @staticmethod
    def get_voice_ranges() -> Dict[str, tuple]:
        return VOICE_RANGES.copy()

    @staticmethod
    def get_voice_descriptions() -> Dict[str, str]:
        return VOICE_DESCRIPTIONS.copy()
    
    @staticmethod
    def get_speechbrain_defaults() -> Dict[str, Any]:
        return SPEECHBRAIN_DEFAULTS.copy()
    
    @staticmethod
    def get_speechbrain_ranges() -> Dict[str, tuple]:
        return SPEECHBRAIN_RANGES.copy()
    
    @staticmethod
    def get_speechbrain_descriptions() -> Dict[str, str]:
        return SPEECHBRAIN_DESCRIPTIONS.copy()

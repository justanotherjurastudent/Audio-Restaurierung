"""VoiceFixer als Rauschreduzierungsmethode - Multi-task AI"""

import os
import tempfile
import time
from typing import Dict, Any
import logging

from utils.logger import log_with_prefix, get_normalized_logger
from utils.config import Config
from .base import AudioProcessor
from core.exceptions import AudioProcessingError

# Logger konfigurieren
logger = get_normalized_logger('voicefixer')

class VoiceFixerProcessor(AudioProcessor):
    """VoiceFixer als Rauschreduzierungsprozessor - Multi-task AI"""

    def __init__(self):
        super().__init__("VoiceFixer Multi-task")
        log_with_prefix(logger, 'info', 'VOICEFIXER', 'voicefixer_processor.py', 
                       'VoiceFixer Multi-task Processor wird initialisiert')
        self._voicefixer = None

    def is_available(self) -> bool:
        """Prüft VoiceFixer-Verfügbarkeit"""
        try:
            import voicefixer
            log_with_prefix(logger, 'info', 'VOICEFIXER', 'voicefixer_processor.py', 
                           'VoiceFixer-Verfügbarkeitsprüfung: ✅ Verfügbar')
            return True
        except ImportError:
            log_with_prefix(logger, 'warning', 'VOICEFIXER', 'voicefixer_processor.py', 
                           'VoiceFixer-Verfügbarkeitsprüfung: ❌ Import fehlgeschlagen')
            return False
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICEFIXER', 'voicefixer_processor.py', 
                           'VoiceFixer-Verfügbarkeitsprüfung fehlgeschlagen: %s', str(e))
            return False

    def _load_model(self):
        """Lädt VoiceFixer-Modell"""
        herkunft = 'voicefixer_processor.py'
        
        if self._voicefixer is not None:
            log_with_prefix(logger, 'debug', 'VOICEFIXER', herkunft, 
                           'VoiceFixer-Modell bereits geladen, verwende Cache')
            return self._voicefixer

        try:
            import voicefixer
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, '📋 Lade VoiceFixer-Modell...')
            
            self._voicefixer = voicefixer.VoiceFixer()
            
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           'Initialisierung: ✅ VoiceFixer-Modell erfolgreich geladen')
            
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'VOICEFIXER', herkunft, 
                               'Initialisierung: Details - VoiceFixer bereit')
            
            return self._voicefixer

        except Exception as e:
            log_with_prefix(logger, 'error', 'VOICEFIXER', herkunft, 
                           'Initialisierung: ❌ Fehlgeschlagen: %s', str(e))
            raise AudioProcessingError(f"VoiceFixer-Modell laden fehlgeschlagen: {str(e)}")

    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Rauschreduzierung mit VoiceFixer Multi-task AI"""
        herkunft = 'voicefixer_processor.py'
        
        # Parameter extrahieren
        mode = params.get('mode', 2)
        cuda = params.get('cuda', False)
        
        log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                       'Rauschreduzierung gestartet mit Mode=%d, CUDA=%s', mode, cuda)

        try:
            # Modell laden
            voicefixer = self._load_model()
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           '✅ VoiceFixer-Modell erfolgreich geladen')

            # VoiceFixer-spezifische Parameter anzeigen
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           '🔧 VoiceFixer-Parameter: Mode=%d (Multi-task), CUDA=%s', mode, cuda)

            # Audio verarbeiten mit VoiceFixer
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           '🚀 Starte VoiceFixer Multi-task AI Verarbeitung...')
            
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'VOICEFIXER', herkunft, 
                               'Input: %s', os.path.basename(input_wav))
                log_with_prefix(logger, 'debug', 'VOICEFIXER', herkunft, 
                               'Output: %s', os.path.basename(output_wav))

            # VoiceFixer restore - Multi-task Verarbeitung
            voicefixer.restore(
                input=input_wav,
                output=output_wav,
                cuda=cuda,
                mode=mode
            )

            # Prüfe ob Ausgabedatei erstellt wurde
            if not os.path.exists(output_wav):
                log_with_prefix(logger, 'error', 'VOICEFIXER', herkunft, 
                               '❌ Ausgabedatei wurde nicht erstellt')
                raise AudioProcessingError("VoiceFixer: Ausgabedatei wurde nicht erstellt")

            # Erfolgreiche Fertigstellung
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           '🎉 VoiceFixer Multi-task Verarbeitung erfolgreich abgeschlossen!')
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           '📁 Ausgabedatei: %s', os.path.basename(output_wav))
            log_with_prefix(logger, 'info', 'VOICEFIXER', herkunft, 
                           'Verarbeitung: ✅ VoiceFixer erfolgreich abgeschlossen (Mode: %d)', mode)
            
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'VOICEFIXER', herkunft, 
                               'Verarbeitung: Details - VoiceFixer Mode %d verwendet', mode)

        except Exception as e:
            log_with_prefix(logger, 'error', 'VOICEFIXER', herkunft, 
                           '❌ VoiceFixer Verarbeitung fehlgeschlagen: %s', str(e))
            log_with_prefix(logger, 'error', 'VOICEFIXER', herkunft, 
                           'Verarbeitung: ❌ Fehlgeschlagen: %s', str(e))
            raise AudioProcessingError(f"VoiceFixer Verarbeitung fehlgeschlagen: {str(e)}")

    def get_default_params(self) -> Dict[str, Any]:
        """Gibt Standard-Parameter zurück"""
        return Config.get_voicefixer_defaults()

    def get_param_ranges(self) -> Dict[str, tuple]:
        """Gibt Parameterbereiche zurück"""
        return Config.get_voicefixer_ranges()

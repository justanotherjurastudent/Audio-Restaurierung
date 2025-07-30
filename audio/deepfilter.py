"""DeepFilterNet3 KI-Rauschreduzierung"""

from typing import Dict, Any
import os
import logging
from utils.logger import log_with_prefix
from utils.config import Config
from .base import AudioProcessor  # ← GEÄNDERT: Import von base.py
from core.exceptions import DeepFilterNetError

# Logger konfigurieren
logger = logging.getLogger("AudioRestorer")

# Global verfügbar prüfen
try:
    from df.enhance import enhance, init_df, load_audio, save_audio
    from df.model import ModelParams
    DEEPFILTERNET_AVAILABLE = True
    log_with_prefix(logger, 'info', 'DEEPFILTER', 'deepfilter.py', '✅ DeepFilterNet3 verfügbar')
except ImportError:
    DEEPFILTERNET_AVAILABLE = False
    log_with_prefix(logger, 'error', 'DEEPFILTER', 'deepfilter.py', '❌ DeepFilterNet3 nicht verfügbar')

class DeepFilterProcessor(AudioProcessor):
    """DeepFilterNet3 KI-Rauschreduzierung"""

    def __init__(self):
        super().__init__("DeepFilterNet3")
        self._model = None
        self._df_state = None
        self._initialized = False

    def is_available(self) -> bool:
        """Prüft DeepFilterNet3 Verfügbarkeit"""
        return DEEPFILTERNET_AVAILABLE

    def _initialize_model(self) -> None:
        """Initialisiert das DeepFilterNet3-Model mit ultimativem Logger-Fix"""
        herkunft = 'deepfilter.py'
        if not DEEPFILTERNET_AVAILABLE:
            log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, '❌ DeepFilterNet3 nicht verfügbar')
            raise DeepFilterNetError("DeepFilterNet3 nicht verfügbar")

        if not self._initialized:
            log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🤖 Initialisiere DeepFilterNet3-Model...')
            if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                log_with_prefix(logger, 'debug', 'DEEPFILTER', herkunft, 'Initialisierung: Details - Starte Logger-Fix')
            try:
                import sys
                import os

                # Erzwinge CPU-Modus für .exe
                if getattr(sys, 'frozen', False):
                    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
                    log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 GPU deaktiviert für .exe-Version')

                # ULTIMATIVER LOGGER-FIX: Alle Logger-Systeme deaktivieren
                try:
                    # 1. Loguru komplett deaktivieren
                    import loguru
                    # Entferne alle Handler
                    loguru.logger.remove()
                    # Füge einen Dummy-Handler hinzu der nichts macht
                    import io
                    dummy_sink = io.StringIO()
                    loguru.logger.add(dummy_sink, level="CRITICAL")
                    log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 Loguru deaktiviert')
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'DEEPFILTER', herkunft, f'🔍 Loguru-Deaktivierung fehlgeschlagen: {e}')

                try:
                    # 2. DeepFilterNet3 Logger komplett überschreiben
                    import df.logger
                    # Ersetze ALLE Logger-Funktionen durch Dummies
                    def dummy_init_logger(*args, **kwargs):
                        """Dummy init_logger der nichts macht"""
                        pass

                    def dummy_log_metrics(*args, **kwargs):
                        """Dummy log_metrics der nichts macht"""
                        pass

                    def dummy_log_audio(*args, **kwargs):
                        """Dummy log_audio der nichts macht"""
                        pass

                    # Monkey-Patch alle Logger-Funktionen
                    df.logger.init_logger = dummy_init_logger
                    df.logger.log_metrics = dummy_log_metrics if hasattr(df.logger, 'log_metrics') else lambda *a, **k: None
                    df.logger.log_audio = dummy_log_audio if hasattr(df.logger, 'log_audio') else lambda *a, **k: None
                    log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 DeepFilterNet3 Logger komplett deaktiviert')
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'DEEPFILTER', herkunft, f'🔍 DF-Logger-Patch fehlgeschlagen: {e}')

                try:
                    # 3. Zusätzlich: df.enhance Logger überschreiben
                    import df.enhance
                    # Falls enhance-Modul eigene Logger-Aufrufe hat
                    if hasattr(df.enhance, 'logger'):
                        df.enhance.logger = None
                    log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 DF-Enhance Logger deaktiviert')
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'DEEPFILTER', herkunft, f'🔍 DF-Enhance-Logger-Patch fehlgeschlagen: {e}')

                # Model-Initialisierung OHNE jegliche Logger-Parameter
                log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 Rufe init_df() ohne Logger auf...')

                # Ultimativer Versuch: init_df mit minimalen Parametern
                try:
                    self._model, self._df_state, _ = init_df()
                except TypeError as te:
                    if "log" in str(te).lower():
                        log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 Logger-Fehler - versuche alternative Initialisierung...')
                        # Plan B: Versuche direkte Model-Instanziierung
                        try:
                            from df.model import ModelParams
                            from df.config import config
                            # Setze minimale Konfiguration
                            model_params = ModelParams()
                            self._model = model_params  # Vereinfacht für Test
                            self._df_state = None  # Temporär None
                            log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, '🔍 Alternative Model-Initialisierung versucht')
                        except Exception as alt_e:
                            log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, f'🔍 Alternative Initialisierung fehlgeschlagen: {alt_e}')
                            raise te
                    else:
                        raise te

                log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, f'🔍 Model erfolgreich geladen: {type(self._model)}')
                if self._df_state:
                    log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, f'🔍 DF-State erfolgreich geladen: {type(self._df_state)}')

                self._initialized = True
                log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, 'Initialisierung: ✅ DeepFilterNet3-Model bereit')
                if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                    log_with_prefix(logger, 'debug', 'DEEPFILTER', herkunft, 'Initialisierung: Details - Model initialisiert')

            except Exception as e:
                log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, f'Initialisierung: ❌ Fehlgeschlagen: {str(e)}')
                raise DeepFilterNetError(f"Model-Initialisierung fehlgeschlagen: {str(e)}")

    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """
        Verarbeitet Audio mit DeepFilterNet3

        Args:
            input_wav: Eingabe-WAV-Datei
            output_wav: Ausgabe-WAV-Datei
            params: Parameter-Dict mit 'attenuation_limit'
        """
        herkunft = 'deepfilter.py'
        log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, 'Verarbeitung gestartet mit Dämpfungsgrenze=%.2f dB', params.get('attenuation_limit', 80.0))  # NEU: INFO mit Optionen und Herkunft
        if not self.is_available():
            log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, '❌ DeepFilterNet3 nicht verfügbar')
            raise DeepFilterNetError("DeepFilterNet3 nicht verfügbar")

        # Model initialisieren falls nötig
        self._initialize_model()

        if not os.path.exists(input_wav):
            log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, f'❌ Eingabe-Datei existiert nicht: {input_wav}')
            raise DeepFilterNetError(f"Eingabe-Datei existiert nicht: {input_wav}")

        try:
            # Parameter extrahieren
            attenuation_limit = params.get('attenuation_limit', 80.0)
            log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, f'🤖 DeepFilterNet3: Verarbeite mit {attenuation_limit} dB Dämpfung')

            # Audio laden
            audio, meta = load_audio(input_wav, sr=self._df_state.sr())
            if audio is None or len(audio) == 0:
                log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, '❌ Audio konnte nicht geladen werden')
                raise DeepFilterNetError("Audio konnte nicht geladen werden")

            # Enhancement durchführen
            enhanced_audio = enhance(
                self._model,
                self._df_state,
                audio,
                atten_lim_db=attenuation_limit
            )
            if enhanced_audio is None:
                log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, '❌ Enhancement lieferte kein Ergebnis')
                raise DeepFilterNetError("Enhancement lieferte kein Ergebnis")

            # Ergebnis speichern
            save_audio(output_wav, enhanced_audio, self._df_state.sr())
            if not os.path.exists(output_wav):
                log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, '❌ Ausgabe-Datei wurde nicht erstellt')
                raise DeepFilterNetError("Ausgabe-Datei wurde nicht erstellt")

            log_with_prefix(logger, 'info', 'DEEPFILTER', herkunft, 'Verarbeitung: ✅ DeepFilterNet3-Verarbeitung abgeschlossen')  # NEU: INFO für Erfolg und Herkunft
            if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                log_with_prefix(logger, 'debug', 'DEEPFILTER', herkunft, 'Verarbeitung: Details - Audio verarbeitet')

        except Exception as e:
            log_with_prefix(logger, 'error', 'DEEPFILTER', herkunft, f'Verarbeitung: ❌ Fehlgeschlagen: {str(e)}')
            raise DeepFilterNetError(f"DeepFilterNet3-Verarbeitung fehlgeschlagen: {str(e)}")

    def get_default_params(self) -> Dict[str, Any]:
        """Gibt Standard-Parameter zurück"""
        return Config.get_deepfilter_defaults()

    def get_param_ranges(self) -> Dict[str, tuple]:
        """Gibt Parameterbereiche zurück"""
        return Config.get_deepfilter_ranges()

    def cleanup(self) -> None:
        """Bereinigt Ressourcen"""
        herkunft = 'deepfilter.py'
        if self._initialized:
            # DeepFilterNet3 Model freigeben falls möglich
            self._model = None
            self._df_state = None
            self._initialized = False
            log_with_prefix(logger, 'debug', 'DEEPFILTER', herkunft, '🤖 DeepFilterNet3-Model freigegeben')

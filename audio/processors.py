"""Basis Audio-Verarbeitungsklassen und -funktionen"""

from typing import Dict, Optional, Tuple, Any

import tempfile
import os
import stat
import secrets
import logging

from utils.logger import log_with_prefix, get_normalized_logger
from utils.config import Config
from utils.validators import is_supported_file

# Logger konfigurieren
logger = get_normalized_logger('processors')

from core.exceptions import AudioProcessingError, ProcessingCancelledException
from .ffmpeg_utils import FFmpegUtils
from .base import AudioProcessor  # ← GEÄNDERT: Import von base.py

# Lazy Imports um Circular Imports zu vermeiden
def _get_deepfilter_processor():
    from .deepfilter import DeepFilterProcessor
    return DeepFilterProcessor()

def _get_audacity_processor():
    from .audacity import AudacityProcessor
    return AudacityProcessor()

def _get_speechbrain_processor():
    from .speechbrain_voice_enhancer import SpeechBrainVoiceEnhancer
    return SpeechBrainVoiceEnhancer()

class MediaProcessor:
    """Hauptklasse für Medienverarbeitung"""

    def __init__(self):
        log_with_prefix(logger, 'info', 'PROCESSORS', 'processors.py', 'MediaProcessor wird initialisiert')
        self.ffmpeg = FFmpegUtils()
        # Lazy Loading der Prozessoren
        self._processors_cache = {}
        log_with_prefix(logger, 'debug', 'PROCESSORS', 'processors.py', 'FFmpeg-Utils und Prozessor-Cache konfiguriert')

    def _get_processor(self, name: str) -> AudioProcessor:
        """Lazy Loading für Prozessoren"""
        herkunft = 'processors.py'
        if name not in self._processors_cache:
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Lade Prozessor: %s', name)
            if name == 'deepfilternet3':
                self._processors_cache[name] = _get_deepfilter_processor()
            elif name == 'audacity':
                self._processors_cache[name] = _get_audacity_processor()
            elif name == 'speechbrain':
                self._processors_cache[name] = _get_speechbrain_processor()
            elif name == 'fallback':
                self._processors_cache[name] = FallbackProcessor()
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Prozessor erfolgreich geladen: %s', name)
        else:
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Verwende gecachten Prozessor: %s', name)
        return self._processors_cache[name]

    def _create_secure_temp_files(self, temp_dir: str, session_id: str = None) -> tuple:
        """Erstellt sichere temporäre Dateien - NEU"""
        herkunft = 'processors.py'
        if session_id is None:
            session_id = secrets.token_hex(8)
        # Zufällige, aber erkennbare Namen
        wav_original = os.path.join(temp_dir, f"orig_{session_id}.wav")
        wav_normalized = os.path.join(temp_dir, f"norm_{session_id}.wav")
        wav_processed = os.path.join(temp_dir, f"proc_{session_id}.wav")
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Sichere temporäre Dateien erstellt - Session: %s', session_id)
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Dateien: orig_%s.wav, norm_%s.wav, proc_%s.wav', session_id, session_id, session_id)
        return wav_original, wav_normalized, wav_processed, session_id

    def _secure_cleanup(self, file_paths: list) -> None:
        """Sichere Bereinigung temporärer Dateien - NEU"""
        herkunft = 'processors.py'
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Beginne sichere Bereinigung von %d Dateien', len(file_paths))
        for path in file_paths:
            if os.path.exists(path):
                try:
                    # Datei überschreiben vor Löschung
                    with open(path, 'r+b') as f:
                        length = f.seek(0, 2)  # Dateigröße
                        if length > 0:
                            f.seek(0)
                            f.write(os.urandom(length))  # Random überschreiben
                            f.flush()
                            os.fsync(f.fileno())
                    os.remove(path)
                    log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Datei sicher gelöscht: %s (%d Bytes überschrieben)', os.path.basename(path), length)
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'PROCESSORS', herkunft, 'Sichere Löschung fehlgeschlagen für %s: %s', os.path.basename(path), str(e))

    def process_media(self, input_path: str, output_path: str,
                    noise_method: str, method_params: Dict[str, Any],
                    target_lufs: float = -20.0,
                    voice_enhancement: bool = False,  # NEU
                    voice_settings: Optional[Dict[str, Any]] = None,
                    voice_method: Optional[str] = None,
                    stop_event: Optional[Any] = None) -> Tuple[str, str]:
        """Verarbeitet ein Medium komplett"""
        herkunft = 'processors.py'
        log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Media-Verarbeitung wird gestartet')
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Eingabedatei: %s', os.path.basename(input_path))
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Ausgabedatei: %s', os.path.basename(output_path))
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Rauschreduzierung: %s', noise_method)
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Ziel-LUFS: %s', target_lufs)
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Voice Enhancement: %s', voice_enhancement)
        
        # Intelligente Bestimmung der voice_method
        if voice_method is None:
            voice_method = voice_settings.get('voice_method', 'classic') if voice_settings else 'classic'
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Voice-Methode bestimmt als: %s', voice_method)
        
        if stop_event and stop_event.is_set():
            raise ProcessingCancelledException("Verarbeitung abgebrochen")
        
        is_valid, msg, media_type = is_supported_file(input_path)
        if not is_valid:
            raise AudioProcessingError(msg)
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, f'Media-Typ: {media_type}')
        
        if not os.path.exists(input_path):
            log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Datei existiert nicht: %s', input_path)
            raise AudioProcessingError(f"Datei existiert nicht: {input_path}")
        
        # Bestimme Sample-Rate basierend auf Methode
        sample_rate = 48000 if noise_method == "deepfilternet3" else 22050
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Sample-Rate für Methode %s: %d Hz', noise_method, sample_rate)
        
        # NEU: Hole Original-Info für Audio-only (Bitrate, Sample-Rate, Codec) – vor der Verarbeitung
        original_info = self.ffmpeg.get_video_info(input_path)  # Funktioniert für Audio/Video
        original_sample_rate = original_info.get('audio_sample_rate', sample_rate)  # Fallback zu methodenbasierter Rate
        original_bitrate = original_info.get('audio_bitrate', '128k')  # Fallback 128k
        original_codec = original_info.get('audio_codec', 'aac')  # Fallback AAC
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, f'Original: Sample-Rate {original_sample_rate} Hz, Bitrate {original_bitrate}, Codec {original_codec}')
        
        # NEU: Sicheres Temp-Verzeichnis mit restriktiven Permissions
        with tempfile.TemporaryDirectory(prefix="audiorest_") as temp_dir:
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Temporäres Verzeichnis erstellt: %s', temp_dir)
            # NEU: Permissions nur für Owner setzen
            os.chmod(temp_dir, stat.S_IRWXU)  # 700
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Temporäres Verzeichnis mit restriktiven Berechtigungen (700) konfiguriert')
            
            # NEU: Sichere temporäre Dateien mit zufälligen Namen
            wav_original, wav_normalized, wav_processed, session_id = self._create_secure_temp_files(temp_dir)
            
            try:
                # 1. Audio extrahieren – NEU: Für Audio mit Original-Sample-Rate
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Extrahiere Audio aus Video')
                if media_type == 'video':
                    self.ffmpeg.extract_audio(input_path, wav_original, sample_rate)
                else:  # Audio
                    self.ffmpeg.convert_to_wav(input_path, wav_original, original_sample_rate)  # NEU: Verwende Original-Sample-Rate
                log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Audio-Extraktion abgeschlossen: %s', os.path.basename(wav_original))
                
                # 2. LUFS-Normalisierung
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Starte LUFS-Normalisierung auf %s LUFS', target_lufs)
                self._normalize_loudness(wav_original, wav_normalized, target_lufs)
                log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'LUFS-Normalisierung abgeschlossen')
                
                # 3. Rauschreduzierung mit Fallback-System
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Starte Rauschreduzierung mit Methode: %s', noise_method)
                used_method = self._process_with_fallback(
                    wav_normalized, wav_processed, noise_method, method_params, stop_event
                )
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Rauschreduzierung abgeschlossen mit Methode: %s', used_method)
                # NEU: 4. Voice-Enhancement (optional) mit Methodenauswahl
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔍 DEBUG - Voice Enhancement Check wird durchgeführt')
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔍 voice_enhancement Parameter: %s (Type: %s)', voice_enhancement, type(voice_enhancement))
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔍 voice_method Parameter: %s', voice_method)
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔍 voice_settings Parameter: %s', voice_settings)
                if voice_enhancement:
                    log_with_prefix(logger, 'info', 'VOICE', herkunft, '✅ Voice Enhancement ist aktiviert - Methode: %s', voice_method)
                    log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Voice Enhancement Einstellungen: %s', voice_settings)
                    if stop_event and stop_event.is_set():
                        raise ProcessingCancelledException("Verarbeitung abgebrochen")
                    wav_enhanced = os.path.join(temp_dir, f"enhanced_{session_id}.wav")
                    # Enhancer basierend auf Methode wählen
                    if voice_method == "speechbrain":
                        log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🤖 Starte SpeechBrain AI Voice Enhancement...')
                        from .speechbrain_voice_enhancer import SpeechBrainVoiceEnhancer
                        enhancer = SpeechBrainVoiceEnhancer()
                        log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔍 SpeechBrain Verfügbarkeit: %s', enhancer.is_available())
                        if enhancer.is_available():
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'Initialisierung: ✅ Verfügbar und initialisiert mit Settings: %s', voice_settings)  # NEU: INFO mit Optionen und Herkunft
                            # Original-Sample-Rate für korrektes Resampling mitgeben
                            voice_settings['original_sample_rate'] = sample_rate
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🚀 Verwende SpeechBrain AI Voice Enhancement')
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔍 Input-Datei: %s', os.path.basename(wav_processed))
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔍 Output-Datei: %s', os.path.basename(wav_enhanced))
                            enhancer.process(wav_processed, wav_enhanced, voice_settings)
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'Verarbeitung: ✅ Gelungen (Methode: SpeechBrain AI)')  # NEU: INFO für Erfolg und Herkunft
                            if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Verarbeitung: Details - Input: %s, Output: %s', wav_processed, wav_enhanced)
                            used_method += " + SpeechBrain AI"
                            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎉 SpeechBrain Voice Enhancement erfolgreich angewendet')
                        else:
                            log_with_prefix(logger, 'warning', 'SPEECHBRAIN', herkunft, 'Initialisierung: ❌ Nicht verfügbar - Fallback zu klassisch')
                            from .voice_enhancer import VoiceAudioEnhancer
                            enhancer = VoiceAudioEnhancer()
                            enhancer.process(wav_processed, wav_enhanced, voice_settings)
                            used_method += " + Voice-Classic"
                            log_with_prefix(logger, 'info', 'VOICE', herkunft, '🔄 Klassisches Voice Enhancement als Fallback angewendet')
                    else:
                        # Klassische Methode (Standard-Fallback)
                        log_with_prefix(logger, 'info', 'VOICE', herkunft, '🎛️ Verwende klassisches Voice Enhancement')
                        from .voice_enhancer import VoiceAudioEnhancer
                        enhancer = VoiceAudioEnhancer()
                        enhancer.process(wav_processed, wav_enhanced, voice_settings)
                        used_method += " + Voice-Classic"
                        log_with_prefix(logger, 'info', 'VOICE', herkunft, '✅ Klassisches Voice Enhancement angewendet')
                    # Wichtig: Verarbeitete Datei als Input für nächsten Schritt verwenden
                    wav_processed = wav_enhanced
                    log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔄 Audio-Pipeline: Voice Enhancement abgeschlossen')
                else:
                    log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'ℹ️ Voice Enhancement ist deaktiviert oder Parameter sind falsch')
                    log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, '🔍 Prüfung: voice_enhancement=%s, Typ=%s', voice_enhancement, type(voice_enhancement))
                # 5. Audio zurück ins Video – NEU: Für Audio mit Original-Parametern
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Füge verarbeitetes Audio zurück in Video ein')
                if media_type == 'video':
                    self.ffmpeg.mux_audio_back(input_path, wav_processed, output_path)
                else:  # Audio – NEU: Speichere mit Original-Parametern als MP3 (oder Original-Codec)
                    original_ext = os.path.splitext(input_path)[1].lower()
                    if original_codec == 'mp3':  # Oder passe an, falls andere Codecs
                        cmd = [
                            self.ffmpeg._ffmpeg_path, "-y",
                            "-i", wav_processed,
                            "-c:a", "libmp3lame",  # MP3-Encoder
                            "-b:a", original_bitrate,  # Original-Bitrate (z.B. "256k")
                            "-ar", str(original_sample_rate),  # Original-Sample-Rate
                            output_path
                        ]
                        import subprocess
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                        if result.returncode != 0:
                            raise AudioProcessingError(f"Audio-Konvertierung fehlgeschlagen: {result.stderr}")
                    else:
                        # Fallback für andere Audio-Codecs (z.B. AAC)
                        self.ffmpeg.convert_from_wav(wav_processed, output_path, original_ext, original_bitrate, original_sample_rate)
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Video-Verarbeitung erfolgreich abgeschlossen')
                log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Finale Ausgabedatei: %s', os.path.basename(output_path))
                return used_method, output_path
            
            except ProcessingCancelledException:
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Verarbeitung wurde vom Benutzer abgebrochen')
                raise
            except Exception as e:
                log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Video-Verarbeitung fehlgeschlagen')
                raise AudioProcessingError(f"Verarbeitung fehlgeschlagen: {str(e)}")
            finally:
                # NEU: Explizite sichere Bereinigung
                log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Starte Cleanup der temporären Dateien')
                self._secure_cleanup([wav_original, wav_normalized, wav_processed])

    def _normalize_loudness(self, input_wav: str, output_wav: str, target_lufs: float) -> None:
        """Normalisiert die Lautstärke"""
        herkunft = 'processors.py'
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Starte Lautstärke-Normalisierung auf %s LUFS', target_lufs)
        try:
            import soundfile as sf
            import pyloudnorm as pyln
            import numpy as np
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Lade Audio-Datei für LUFS-Messung: %s', os.path.basename(input_wav))
            data, rate = sf.read(input_wav)
            if len(data) == 0:
                log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Audio-Datei ist leer: %s', os.path.basename(input_wav))
                raise AudioProcessingError("Audio-Datei ist leer")
            # Stereo zu Mono falls nötig
            if data.ndim > 1:
                log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Konvertiere Stereo zu Mono für LUFS-Messung')
                data = np.mean(data, axis=1)
            # LUFS-Messung und Normalisierung
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Messe aktuelle LUFS-Lautstärke')
            meter = pyln.Meter(rate)
            loudness = meter.integrated_loudness(data)
            if loudness == -np.inf:
                log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Audio ist komplett stumm - keine LUFS-Messung möglich')
                raise AudioProcessingError("Audio ist komplett stumm")
            log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Aktuelle LUFS: %.2f, Ziel-LUFS: %.2f', loudness, target_lufs)
            data_normalized = pyln.normalize.loudness(data, loudness, target_lufs)
            sf.write(output_wav, data_normalized, rate, subtype="PCM_16")
            log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'LUFS-Normalisierung erfolgreich: %.2f → %.2f LUFS', loudness, target_lufs)
        except ImportError as e:
            log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Benötigte Audio-Bibliothek nicht verfügbar: %s', str(e))
            raise AudioProcessingError(f"Benötigte Audio-Bibliothek nicht verfügbar: {e}")
        except Exception as e:
            log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'LUFS-Normalisierung fehlgeschlagen')
            raise AudioProcessingError(f"LUFS-Normalisierung fehlgeschlagen: {e}")

    def _process_with_fallback(self, input_wav: str, output_wav: str,
                               method: str, params: Dict[str, Any],
                               stop_event: Optional[Any]) -> str:
        """Verarbeitet Audio mit Fallback-System"""
        herkunft = 'processors.py'
        log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Starte Audio-Verarbeitung mit Fallback-System')
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Gewünschte Methode: %s', method)
        log_with_prefix(logger, 'debug', 'PROCESSORS', herkunft, 'Parameter: %s', params)
        # Versuche gewünschte Methode
        processor = self._get_processor(method)
        if processor and processor.is_available():
            try:
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Verwende gewünschte Methode: %s', method)
                processor.process(input_wav, output_wav, params)
                log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Primäre Methode erfolgreich: %s', method)
                return method
            except ProcessingCancelledException:
                raise
            except Exception as e:
                log_with_prefix(logger, 'warning', 'PROCESSORS', herkunft, 'Primäre Methode %s fehlgeschlagen: %s', method, str(e))
        # Fallback 1: Audacity (wenn nicht bereits verwendet)
        if method != 'audacity':
            audacity_processor = self._get_processor('audacity')
            if audacity_processor.is_available():
                try:
                    if stop_event and stop_event.is_set():
                        raise ProcessingCancelledException("Verarbeitung abgebrochen")
                    log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Fallback zu Audacity-Methode')
                    audacity_processor.process(input_wav, output_wav, params)
                    log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Audacity-Fallback erfolgreich')
                    return 'audacity_fallback'
                except ProcessingCancelledException:
                    raise
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'PROCESSORS', herkunft, 'Audacity-Fallback fehlgeschlagen: %s', str(e))
        # Fallback 2: FFmpeg-Filter
        try:
            if stop_event and stop_event.is_set():
                raise ProcessingCancelledException("Verarbeitung abgebrochen")
            log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'Fallback zu FFmpeg-Filter')
            fallback_processor = self._get_processor('fallback')
            fallback_processor.process(input_wav, output_wav, params)
            log_with_prefix(logger, 'info', 'PROCESSORS', herkunft, 'FFmpeg-Fallback erfolgreich')
            return 'ffmpeg_fallback'
        except ProcessingCancelledException:
            raise
        except Exception as e:
            log_with_prefix(logger, 'error', 'PROCESSORS', herkunft, 'Alle Verarbeitungsmethoden fehlgeschlagen')
            raise AudioProcessingError(f"Alle Verarbeitungsmethoden fehlgeschlagen. Letzter Fehler: {e}")

class FallbackProcessor(AudioProcessor):
    """FFmpeg-basierter Fallback-Prozessor"""

    def __init__(self):
        super().__init__("FFmpeg Fallback")
        log_with_prefix(logger, 'info', 'FALLBACK', 'processors.py', 'FFmpeg Fallback-Prozessor initialisiert')
        self.ffmpeg = FFmpegUtils()

    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Einfache FFmpeg-Filterung"""
        herkunft = 'processors.py'
        log_with_prefix(logger, 'info', 'FALLBACK', herkunft, 'Wende FFmpeg-Fallback-Filter an')
        log_with_prefix(logger, 'debug', 'FALLBACK', herkunft, 'Eingabe: %s', os.path.basename(input_wav))
        log_with_prefix(logger, 'debug', 'FALLBACK', herkunft, 'Ausgabe: %s', os.path.basename(output_wav))
        log_with_prefix(logger, 'debug', 'FALLBACK', herkunft, 'Parameter: %s', params)
        self.ffmpeg.apply_basic_filter(input_wav, output_wav)
        log_with_prefix(logger, 'info', 'FALLBACK', herkunft, 'FFmpeg-Fallback-Filter erfolgreich angewendet')

    def is_available(self) -> bool:
        """FFmpeg sollte immer verfügbar sein"""
        herkunft = 'processors.py'
        available = self.ffmpeg.is_available()
        log_with_prefix(logger, 'debug', 'FALLBACK', herkunft, 'FFmpeg-Verfügbarkeit: %s', available)
        return available
"""Professionelle Voice-Audio-Enhancement mit detailliertem Logging"""

import numpy as np
import soundfile as sf
from scipy import signal
from typing import Dict, Any
import os
import logging

# NEU: Import für log_with_prefix (behebt 'not defined'-Fehler)
from utils.logger import log_with_prefix, get_normalized_logger

from .base import AudioProcessor
from core.exceptions import AudioProcessingError

# Logger konfigurieren
logger = get_normalized_logger('voice_enhancer')

class VoiceAudioEnhancer(AudioProcessor):
    """Voice Enhancement mit strukturiertem deutschem Logging"""
    
    def __init__(self):
        super().__init__("Voice Enhancer")
        log_with_prefix(logger, 'info', 'VOICE', 'voice_enhancer.py', 'Voice Audio Enhancer wird initialisiert')
        self.sample_rate = 48000
        log_with_prefix(logger, 'debug', 'VOICE', 'voice_enhancer.py', 'Standard-Sample-Rate konfiguriert: %d Hz', self.sample_rate)

    def is_available(self) -> bool:
        """Immer verfügbar - verwendet nur scipy/numpy"""
        log_with_prefix(logger, 'debug', 'VOICE', 'voice_enhancer.py', 'Voice Enhancer Verfügbarkeit geprüft: verfügbar (scipy/numpy-basiert)')
        return True

    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Voice Enhancement mit detailliertem strukturiertem Logging"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Voice Enhancement wird gestartet')
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Eingabedatei: %s', os.path.basename(input_wav))
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Ausgabedatei: %s', os.path.basename(output_wav))
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Verarbeitungsparameter: %s', params)
        try:
            # Defaults laden und Parameter zusammenführen
            from utils.config import Config
            settings = Config.get_voice_defaults()
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Standard-Parameter geladen: %s', settings)
            settings.update(params)  # User-Werte überschreiben
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Finale Voice Enhancement Parameter konfiguriert')
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Parameter-Details: clarity=%.1f, warmth=%.1f, bandwidth=%.1f, harmonic=%.1f',
                            settings.get('clarity_boost', 0), settings.get('warmth_boost', 0),
                            settings.get('bandwidth_extension', 0), settings.get('harmonic_restoration', 0))

            # Audio laden und analysieren
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Audio-Datei wird geladen: %s', os.path.basename(input_wav))
            audio, sr = sf.read(input_wav)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Audio erfolgreich geladen')
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Sample-Rate: %d Hz', sr)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Audio-Form: %s', str(audio.shape))
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Audio-Dauer: %.2f Sekunden', len(audio)/sr)
            if audio.ndim > 1:
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Konvertiere Stereo zu Mono')
                audio = np.mean(audio, axis=1)
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Stereo-zu-Mono-Konvertierung abgeschlossen')

            # Audio-Statistiken vor Verarbeitung
            original_rms = np.sqrt(np.mean(audio**2))
            original_max = np.max(np.abs(audio))
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Original-Audio analysiert - RMS: %.4f, Max: %.4f', original_rms, original_max)

            # Voice Enhancement Chain mit detailliertem Logging
            audio = self._apply_clarity_boost(audio, sr, settings["clarity_boost"])
            audio = self._apply_warmth_boost(audio, sr, settings["warmth_boost"])
            audio = self._apply_bandwidth_extension(audio, sr, settings["bandwidth_extension"])
            audio = self._apply_harmonic_restoration(audio, sr, settings["harmonic_restoration"])
            audio = self._apply_compression(
                audio, sr,
                settings["compression_ratio"],
                settings["compression_threshold"]
            )

            # Audio-Statistiken nach Verarbeitung
            processed_rms = np.sqrt(np.mean(audio**2))
            processed_max = np.max(np.abs(audio))
            rms_change = ((processed_rms/original_rms - 1) * 100)
            max_change = ((processed_max/original_max - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Verarbeitung abgeschlossen - RMS: %.4f, Max: %.4f', processed_rms, processed_max)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'RMS-Änderung: %+.1f%%, Max-Änderung: %+.1f%%', rms_change, max_change)

            # Clipping-Schutz
            if processed_max > 0.95:
                scaling_factor = 0.95 / processed_max
                audio = audio * scaling_factor
                log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Clipping-Schutz aktiviert - Audio um %.3f skaliert', scaling_factor)
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Audio-Maximum nach Skalierung: %.4f', np.max(np.abs(audio)))
            else:
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Kein Clipping-Schutz erforderlich - Maximum: %.4f', processed_max)

            # Speichern
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Speichere verarbeitetes Audio: %s', os.path.basename(output_wav))
            sf.write(output_wav, audio, sr, subtype='PCM_16')
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Voice Enhancement erfolgreich abgeschlossen')
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Ausgabedatei erstellt: %s', os.path.basename(output_wav))

        except Exception as e:
            log_with_prefix(logger, 'error', 'VOICE', herkunft, 'Voice Enhancement fehlgeschlagen')
            raise AudioProcessingError(f"Voice Enhancement fehlgeschlagen: {str(e)}")

    def _apply_clarity_boost(self, audio: np.ndarray, sr: int, boost_db: float) -> np.ndarray:
        """Hebt 2-4 kHz für bessere Sprachverständlichkeit an"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Starte Clarity Boost: %.1f dB bei 2500 Hz', boost_db)
        if boost_db <= 0:
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Clarity Boost übersprungen (Wert <= 0)')
            return audio
        try:
            # Audio-Statistiken vor Verarbeitung
            before_rms = np.sqrt(np.mean(audio**2))
            # Parametrisches EQ bei 2500 Hz
            center_freq = 2500
            q_factor = 1.0
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Parametrisches EQ: Frequenz=%d Hz, Q=%.1f', center_freq, q_factor)
            processed_audio = self._apply_parametric_eq(audio, sr, center_freq, boost_db, q_factor)
            # Audio-Statistiken nach Verarbeitung
            after_rms = np.sqrt(np.mean(processed_audio**2))
            change_percent = ((after_rms/before_rms - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Clarity Boost angewendet - RMS-Änderung: %+.1f%%', change_percent)
            return processed_audio
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Clarity Boost fehlgeschlagen: %s - verwende Original-Audio', str(e))
            return audio

    def _apply_warmth_boost(self, audio: np.ndarray, sr: int, boost_db: float) -> np.ndarray:
        """Betont 120-250 Hz für volleren, körperlichen Klang"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Starte Warmth Boost: %.1f dB bei 180 Hz (Low-Shelf)', boost_db)
        if boost_db <= 0:
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Warmth Boost übersprungen (Wert <= 0)')
            return audio
        try:
            # Audio-Statistiken vor Verarbeitung
            before_rms = np.sqrt(np.mean(audio**2))
            # Low-Shelf Filter bei 180 Hz
            center_freq = 180
            processed_audio = self._apply_shelf_eq(audio, sr, center_freq, boost_db, 'low')
            # Audio-Statistiken nach Verarbeitung
            after_rms = np.sqrt(np.mean(processed_audio**2))
            change_percent = ((after_rms/before_rms - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Warmth Boost angewendet - RMS-Änderung: %+.1f%%', change_percent)
            return processed_audio
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Warmth Boost fehlgeschlagen: %s - verwende Original-Audio', str(e))
            return audio

    def _apply_bandwidth_extension(self, audio: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        """Erweitert die Audio-Bandbreite durch Wiederherstellung hoher Frequenzen"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Starte Bandwidth Extension: Intensität %.1f (6-12 kHz)', intensity)
        if intensity <= 0:
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Bandwidth Extension übersprungen (Intensität <= 0)')
            return audio
        try:
            # Audio-Statistiken vor Verarbeitung
            before_rms = np.sqrt(np.mean(audio**2))
            # High-Shelf Filter für 6-12 kHz Bereich
            nyquist = sr / 2
            high_freq = 6000
            if high_freq >= nyquist:
                log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Bandwidth Extension übersprungen - 6 kHz >= Nyquist (%d Hz)', int(nyquist))
                return audio
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Frequency-Band-Extraktion: %d Hz bis %d Hz', high_freq, min(12000, int(nyquist)))
            # Harmonische Rekonstruktion
            high_band = self._extract_frequency_band(audio, sr, high_freq, min(12000, int(nyquist)))
            high_band_rms = np.sqrt(np.mean(high_band**2))
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'High-Band RMS: %.4f', high_band_rms)
            # Sanfte Anhebung
            gain_db = intensity * 0.8
            enhanced_high = high_band * (10 ** (gain_db / 20))
            processed_audio = audio + enhanced_high * 0.3
            # Audio-Statistiken nach Verarbeitung
            after_rms = np.sqrt(np.mean(processed_audio**2))
            change_percent = ((after_rms/before_rms - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Bandwidth Extension angewendet - RMS-Änderung: %+.1f%%', change_percent)
            return processed_audio
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Bandwidth Extension fehlgeschlagen: %s - verwende Original-Audio', str(e))
            return audio

    def _apply_harmonic_restoration(self, audio: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        """Sehr sanfte Harmonic Restoration ohne Multiband"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Starte Harmonic Restoration: Intensität %.1f', intensity)
        if intensity <= 0:
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Harmonic Restoration übersprungen (Intensität <= 0)')
            return audio
        try:
            # Sehr konservative Parameter
            saturation_amount = intensity * 0.02  # Stark reduziert
            if saturation_amount > 0.1:  # Sicherheitsgrenze
                saturation_amount = 0.1
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Saturation auf %.3f begrenzt (Sicherheitsgrenze)', saturation_amount)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Saturation-Parameter: %.3f', saturation_amount)
            # Sanfte Tube-style Sättigung
            drive = 1 + saturation_amount
            saturated = np.tanh(audio * drive) / drive
            # Sehr schwaches Blending (nur 5% gesättigt, 95% original)
            blend_factor = 0.05
            enhanced = audio * (1 - blend_factor) + saturated * blend_factor
            # Audio-Statistiken
            original_rms = np.sqrt(np.mean(audio**2))
            enhanced_rms = np.sqrt(np.mean(enhanced**2))
            change_percent = ((enhanced_rms/original_rms - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Harmonic Restoration angewendet - RMS-Änderung: %+.1f%%', change_percent)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Blend-Factor: %.3f, Drive: %.3f', blend_factor, drive)
            return enhanced
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Harmonic Restoration fehlgeschlagen: %s - verwende Original-Audio', str(e))
            return audio

    def _apply_compression(self, audio: np.ndarray, sr: int, ratio: float, threshold: float) -> np.ndarray:
        """Sanfte Kompression für voluminösere Stimmen"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Starte Kompression: Ratio %.1f:1, Threshold %.1f dB', ratio, threshold)
        if ratio <= 1.0:
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Kompression übersprungen (Ratio <= 1.0)')
            return audio
        try:
            # RMS-basierte Kompression
            rms = np.sqrt(np.mean(audio**2))
            threshold_linear = 10 ** (threshold / 20)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Audio-RMS: %.4f, Threshold-Linear: %.4f', rms, threshold_linear)
            if rms <= threshold_linear:
                log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'RMS unter Threshold - keine Kompression angewendet')
                return audio
            # Kompression anwenden
            over_threshold = rms - threshold_linear
            compressed_over = over_threshold / ratio
            compressed_rms = threshold_linear + compressed_over
            # Audio skalieren
            gain_reduction = compressed_rms / rms if rms > 0 else 1.0
            compressed_audio = audio * gain_reduction
            # Makeup Gain (leichte Anhebung nach Kompression)
            makeup_gain = 1.1  # 10% lauter
            compressed_audio *= makeup_gain
            # Statistiken
            before_rms = rms
            after_rms = np.sqrt(np.mean(compressed_audio**2))
            change_percent = ((after_rms/before_rms - 1) * 100)
            log_with_prefix(logger, 'info', 'VOICE', herkunft, 'Kompression angewendet - RMS-Änderung: %+.1f%%', change_percent)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Gain-Reduction: %.3f, Makeup-Gain: %.1f', gain_reduction, makeup_gain)
            return compressed_audio
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Kompression fehlgeschlagen: %s - verwende Original-Audio', str(e))
            return audio

    def _apply_parametric_eq(self, audio: np.ndarray, sr: int, freq: float, gain_db: float, q: float) -> np.ndarray:
        """Parametrisches EQ (Peaking Filter)"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Parametrisches EQ: %.0f Hz, %.1f dB, Q=%.1f', freq, gain_db, q)
        try:
            w0 = 2 * np.pi * freq / sr
            alpha = np.sin(w0) / (2 * q)
            A = 10 ** (gain_db / 40)
            b0 = 1 + alpha * A
            b1 = -2 * np.cos(w0)
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * np.cos(w0)
            a2 = 1 - alpha / A
            b = np.array([b0, b1, b2]) / a0
            a = np.array([a0, a1, a2]) / a0
            result = signal.filtfilt(b, a, audio)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Parametrisches EQ erfolgreich angewendet')
            return result
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Parametrisches EQ fehlgeschlagen: %s', str(e))
            return audio

    def _apply_shelf_eq(self, audio: np.ndarray, sr: int, freq: float, gain_db: float, shelf_type: str) -> np.ndarray:
        """Shelf EQ (Low-Shelf oder High-Shelf)"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Shelf EQ: %.0f Hz, %.1f dB, Typ=%s', freq, gain_db, shelf_type)
        try:
            nyquist = sr / 2
            normalized_freq = freq / nyquist
            if normalized_freq >= 1.0:
                log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Shelf EQ übersprungen - Frequenz >= Nyquist',)
                return audio
            # Butterworth Filter als Shelf approximation
            gain_linear = 10 ** (gain_db / 20)
            if shelf_type == 'low':
                b, a = signal.butter(2, normalized_freq, btype='low')
                filtered = signal.filtfilt(b, a, audio)
                result = audio + filtered * (gain_linear - 1)
            else:  # high
                b, a = signal.butter(2, normalized_freq, btype='high')
                filtered = signal.filtfilt(b, a, audio)
                result = audio + filtered * (gain_linear - 1)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Shelf EQ erfolgreich angewendet')
            return result
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Shelf EQ fehlgeschlagen: %s', str(e))
            return audio

    def _extract_frequency_band(self, audio: np.ndarray, sr: int, low_freq: float, high_freq: float) -> np.ndarray:
        """Extrahiert einen Frequenzbereich"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Frequency-Band-Extraktion: %.0f Hz - %.0f Hz', low_freq, high_freq)
        try:
            nyquist = sr / 2
            low_norm = max(low_freq / nyquist, 0.01)
            high_norm = min(high_freq / nyquist, 0.99)
            if low_norm >= high_norm:
                log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Ungültiger Frequenzbereich - Low >= High',)
                return np.zeros_like(audio)
            b, a = signal.butter(4, [low_norm, high_norm], btype='band')
            result = signal.filtfilt(b, a, audio)
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Frequency-Band erfolgreich extrahiert')
            return result
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Frequency-Band-Extraktion fehlgeschlagen: %s', str(e))
            return np.zeros_like(audio)

    def _apply_harmonic_enhancement(self, band_audio: np.ndarray, intensity: float) -> np.ndarray:
        """Sanfte harmonische Sättigung"""
        herkunft = 'voice_enhancer.py'
        log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Harmonische Sättigung: Intensität %.2f', intensity)
        try:
            # Tube-style saturation mit geringer Intensität
            drive = 1 + intensity * 0.5
            saturated = np.tanh(band_audio * drive) / drive
            log_with_prefix(logger, 'debug', 'VOICE', herkunft, 'Harmonische Sättigung angewendet - Drive: %.2f', drive)
            return saturated
        except Exception as e:
            log_with_prefix(logger, 'warning', 'VOICE', herkunft, 'Harmonische Sättigung fehlgeschlagen: %s', str(e))
            return band_audio
"""Basis Audio-Verarbeitungsklassen und -funktionen"""

from typing import Dict, Optional, Tuple, Any
import tempfile
import os

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

class VideoProcessor:
    """Hauptklasse für Video-zu-Audio-Verarbeitung"""
    
    def __init__(self):
        self.ffmpeg = FFmpegUtils()
        # Lazy Loading der Prozessoren
        self._processors_cache = {}
    
    def _get_processor(self, name: str) -> AudioProcessor:
        """Lazy Loading für Prozessoren"""
        if name not in self._processors_cache:
            if name == 'deepfilternet3':
                self._processors_cache[name] = _get_deepfilter_processor()
            elif name == 'audacity':
                self._processors_cache[name] = _get_audacity_processor()
            elif name == 'fallback':
                self._processors_cache[name] = FallbackProcessor()
        
        return self._processors_cache[name]
    
    def process_video(self, video_path: str, output_path: str, 
                     noise_method: str, method_params: Dict[str, Any],
                     target_lufs: float = -15.0, 
                     stop_event: Optional[Any] = None) -> Tuple[str, str]:
        """
        Verarbeitet ein Video komplett
        
        Returns:
            Tuple[used_method, output_path]: Verwendete Methode und Ausgabepfad
        """
        if stop_event and stop_event.is_set():
            raise ProcessingCancelledException("Verarbeitung abgebrochen")
        
        if not os.path.exists(video_path):
            raise AudioProcessingError(f"Video-Datei existiert nicht: {video_path}")
        
        # Bestimme Sample-Rate basierend auf Methode
        sample_rate = 48000 if noise_method == "deepfilternet3" else 22050
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Temporäre Dateien
            wav_original = os.path.join(temp_dir, "original.wav")
            wav_normalized = os.path.join(temp_dir, "normalized.wav") 
            wav_processed = os.path.join(temp_dir, "processed.wav")
            
            try:
                # 1. Audio extrahieren
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                
                self.ffmpeg.extract_audio(video_path, wav_original, sample_rate)
                
                # 2. LUFS-Normalisierung
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                
                self._normalize_loudness(wav_original, wav_normalized, target_lufs)
                
                # 3. Rauschreduzierung mit Fallback-System
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                
                used_method = self._process_with_fallback(
                    wav_normalized, wav_processed, noise_method, method_params, stop_event
                )
                
                # 4. Audio zurück ins Video
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                
                self.ffmpeg.mux_audio_back(video_path, wav_processed, output_path)
                
                return used_method, output_path
                
            except ProcessingCancelledException:
                raise
            except Exception as e:
                raise AudioProcessingError(f"Verarbeitung fehlgeschlagen: {str(e)}")
    
    def _normalize_loudness(self, input_wav: str, output_wav: str, target_lufs: float) -> None:
        """Normalisiert die Lautstärke"""
        try:
            import soundfile as sf
            import pyloudnorm as pyln
            import numpy as np
            
            data, rate = sf.read(input_wav)
            if len(data) == 0:
                raise AudioProcessingError("Audio-Datei ist leer")
            
            # Stereo zu Mono falls nötig
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            
            # LUFS-Messung und Normalisierung
            meter = pyln.Meter(rate)
            loudness = meter.integrated_loudness(data)
            
            if loudness == -np.inf:
                raise AudioProcessingError("Audio ist komplett stumm")
            
            data_normalized = pyln.normalize.loudness(data, loudness, target_lufs)
            sf.write(output_wav, data_normalized, rate, subtype="PCM_16")
            
        except ImportError as e:
            raise AudioProcessingError(f"Benötigte Audio-Bibliothek nicht verfügbar: {e}")
        except Exception as e:
            raise AudioProcessingError(f"LUFS-Normalisierung fehlgeschlagen: {e}")
    
    def _process_with_fallback(self, input_wav: str, output_wav: str, 
                              method: str, params: Dict[str, Any],
                              stop_event: Optional[Any]) -> str:
        """Verarbeitet Audio mit Fallback-System"""
        # Versuche gewünschte Methode
        processor = self._get_processor(method)
        if processor and processor.is_available():
            try:
                if stop_event and stop_event.is_set():
                    raise ProcessingCancelledException("Verarbeitung abgebrochen")
                
                processor.process(input_wav, output_wav, params)
                return method
            except ProcessingCancelledException:
                raise
            except Exception as e:
                print(f"⚠️ {method} fehlgeschlagen: {e}")
        
        # Fallback 1: Audacity (wenn nicht bereits verwendet)
        if method != 'audacity':
            audacity_processor = self._get_processor('audacity')
            if audacity_processor.is_available():
                try:
                    if stop_event and stop_event.is_set():
                        raise ProcessingCancelledException("Verarbeitung abgebrochen")
                    
                    print("🔄 Fallback zu Audacity-Methode")
                    audacity_processor.process(input_wav, output_wav, params)
                    return 'audacity_fallback'
                except ProcessingCancelledException:
                    raise
                except Exception as e:
                    print(f"⚠️ Audacity-Fallback fehlgeschlagen: {e}")
        
        # Fallback 2: FFmpeg-Filter
        try:
            if stop_event and stop_event.is_set():
                raise ProcessingCancelledException("Verarbeitung abgebrochen")
            
            print("🔄 Fallback zu FFmpeg-Filter")
            fallback_processor = self._get_processor('fallback')
            fallback_processor.process(input_wav, output_wav, params)
            return 'ffmpeg_fallback'
        except ProcessingCancelledException:
            raise
        except Exception as e:
            raise AudioProcessingError(f"Alle Verarbeitungsmethoden fehlgeschlagen. Letzter Fehler: {e}")

class FallbackProcessor(AudioProcessor):
    """FFmpeg-basierter Fallback-Prozessor"""
    
    def __init__(self):
        super().__init__("FFmpeg Fallback")
        self.ffmpeg = FFmpegUtils()
    
    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Einfache FFmpeg-Filterung"""
        self.ffmpeg.apply_basic_filter(input_wav, output_wav)
    
    def is_available(self) -> bool:
        """FFmpeg sollte immer verfügbar sein"""
        return self.ffmpeg.is_available()

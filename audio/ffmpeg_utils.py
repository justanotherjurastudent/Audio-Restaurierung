"""FFmpeg-Utilities für Audio/Video-Operationen"""

import subprocess
import os
from typing import List, Optional

from core.exceptions import FFmpegNotFoundError, AudioProcessingError

class FFmpegUtils:
    """Wrapper für FFmpeg-Operationen"""
    
    def __init__(self):
        self._ffmpeg_available = None
    
    def is_available(self) -> bool:
        """Prüft ob FFmpeg verfügbar ist (mit Caching)"""
        if self._ffmpeg_available is None:
            self._ffmpeg_available = self._check_ffmpeg()
        return self._ffmpeg_available
    
    def _check_ffmpeg(self) -> bool:
        """Prüft FFmpeg-Verfügbarkeit"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def extract_audio(self, video_path: str, wav_path: str, sample_rate: int = 48000) -> None:
        """
        Extrahiert Audio aus Video als Mono-WAV
        
        Args:
            video_path: Pfad zur Video-Datei
            wav_path: Pfad für die Audio-Ausgabe
            sample_rate: Gewünschte Sample-Rate
        """
        if not self.is_available():
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        
        if not os.path.exists(video_path):
            raise AudioProcessingError(f"Video-Datei existiert nicht: {video_path}")
        
        cmd = [
            "ffmpeg", "-y",  # Überschreiben
            "-i", video_path,
            "-vn",  # Keine Video-Streams
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", str(sample_rate),  # Sample-Rate
            "-ac", "1",  # Mono
            wav_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise AudioProcessingError(f"FFmpeg Audio-Extraktion fehlgeschlagen: {result.stderr}")
            
            if not os.path.exists(wav_path):
                raise AudioProcessingError("Audio-Datei wurde nicht erstellt")
            
            print(f"✅ Audio extrahiert: {sample_rate}Hz Mono WAV")
            
        except subprocess.TimeoutExpired:
            raise AudioProcessingError("FFmpeg Audio-Extraktion: Timeout erreicht")
        except Exception as e:
            raise AudioProcessingError(f"FFmpeg Audio-Extraktion: {str(e)}")
    
    def mux_audio_back(self, video_path: str, audio_path: str, output_path: str) -> None:
        """
        Ersetzt Audio-Spur in Video (ohne Video-Neukodierung)
        
        Args:
            video_path: Original-Video
            audio_path: Neue Audio-Spur
            output_path: Ausgabe-Video
        """
        if not self.is_available():
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        
        if not os.path.exists(video_path):
            raise AudioProcessingError(f"Video-Datei existiert nicht: {video_path}")
        
        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio-Datei existiert nicht: {audio_path}")
        
        cmd = [
            "ffmpeg", "-y",  # Überschreiben
            "-i", video_path,  # Video-Input
            "-i", audio_path,  # Audio-Input
            "-map", "0:v:0",  # Video vom ersten Input
            "-map", "1:a:0",  # Audio vom zweiten Input
            "-c:v", "copy",  # Video nicht neu kodieren
            "-c:a", "aac",  # Audio als AAC
            "-b:a", "128k",  # Audio-Bitrate
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise AudioProcessingError(f"FFmpeg Video-Zusammenführung fehlgeschlagen: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise AudioProcessingError("Ausgabe-Video wurde nicht erstellt")
            
            print("✅ Audio erfolgreich in Video eingebettet")
            
        except subprocess.TimeoutExpired:
            raise AudioProcessingError("FFmpeg Video-Zusammenführung: Timeout erreicht")
        except Exception as e:
            raise AudioProcessingError(f"FFmpeg Video-Zusammenführung: {str(e)}")
    
    def apply_basic_filter(self, input_wav: str, output_wav: str) -> None:
        """
        Wendet einfache Audio-Filter an (Fallback-Methode)
        
        Args:
            input_wav: Eingabe-Audio
            output_wav: Ausgabe-Audio
        """
        if not self.is_available():
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        
        if not os.path.exists(input_wav):
            raise AudioProcessingError(f"Audio-Datei existiert nicht: {input_wav}")
        
        # Einfacher Bandpass-Filter + Verstärkung
        cmd = [
            "ffmpeg", "-y",
            "-i", input_wav,
            "-af", "highpass=f=80,lowpass=f=8000,volume=1.2",
            output_wav
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise AudioProcessingError(f"FFmpeg Filter fehlgeschlagen: {result.stderr}")
            
            if not os.path.exists(output_wav):
                raise AudioProcessingError("Gefilterte Audio-Datei wurde nicht erstellt")
            
            print("✅ FFmpeg Basis-Filter angewendet")
            
        except subprocess.TimeoutExpired:
            raise AudioProcessingError("FFmpeg Filter: Timeout erreicht")
        except Exception as e:
            raise AudioProcessingError(f"FFmpeg Filter: {str(e)}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Extrahiert Video-Informationen
        
        Returns:
            Dict mit Video-Metadaten
        """
        if not self.is_available():
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise AudioProcessingError(f"FFprobe fehlgeschlagen: {result.stderr}")
            
            import json
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise AudioProcessingError("FFprobe: Timeout erreicht")
        except json.JSONDecodeError as e:
            raise AudioProcessingError(f"FFprobe JSON-Parsing: {str(e)}")
        except Exception as e:
            raise AudioProcessingError(f"FFprobe: {str(e)}")

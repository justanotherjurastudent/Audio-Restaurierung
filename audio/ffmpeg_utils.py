"""FFmpeg-Utilities mit embedded Binaries und konsistentem Logging"""

import subprocess
import os
import shlex
import sys
import logging
from typing import List, Optional
from utils.logger import log_with_prefix, get_normalized_logger

from core.exceptions import FFmpegNotFoundError, AudioProcessingError
from utils.config import Config

# Logger konfigurieren
logger = get_normalized_logger('ffmpeg_utils')

def get_ffmpeg_path() -> str:
    """Findet FFmpeg-Binary (embedded oder system-wide)"""
    herkunft = 'ffmpeg_utils.py'
    log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Suche FFmpeg-Binary')
    # 1. Prüfe embedded FFmpeg (in .exe oder Projektordner)
    if getattr(sys, 'frozen', False):
        # Wenn als .exe gepackt (PyInstaller)
        base_path = sys._MEIPASS  # PyInstaller temp folder
        ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'EXE-Modus erkannt: base_path=%s', base_path)
        if os.path.exists(ffmpeg_path):
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Verwende eingebettetes FFmpeg: %s', ffmpeg_path)
            return ffmpeg_path
        else:
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Eingebettetes FFmpeg nicht gefunden: %s', ffmpeg_path)
    else:
        # Entwicklungsmodus - relative zum Skript
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg', 'ffmpeg.exe')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Entwicklungsmodus: script_dir=%s', script_dir)
        if os.path.exists(ffmpeg_path):
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Verwende Projekt-FFmpeg: %s', ffmpeg_path)
            return ffmpeg_path
        else:
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Projekt-FFmpeg nicht gefunden: %s', ffmpeg_path)
    # 2. Fallback: System-FFmpeg
    log_with_prefix(logger, 'warning', 'FFMPEG', herkunft, 'Verwende System-FFmpeg aus PATH')
    return "ffmpeg"

def get_ffprobe_path() -> str:
    """Findet FFprobe-Binary"""
    herkunft = 'ffmpeg_utils.py'
    log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Suche FFprobe-Binary')
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        ffprobe_path = os.path.join(base_path, 'ffmpeg', 'ffprobe.exe')
        if os.path.exists(ffprobe_path):
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende eingebettetes FFprobe: %s', ffprobe_path)
            return ffprobe_path
    else:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffprobe_path = os.path.join(script_dir, 'ffmpeg', 'ffprobe.exe')
        if os.path.exists(ffprobe_path):
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende Projekt-FFprobe: %s', ffprobe_path)
            return ffprobe_path
    log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende System-FFprobe aus PATH')
    return "ffprobe"

class FFmpegUtils:
    """Wrapper für FFmpeg-Operationen mit embedded Binaries und konsistentem Logging"""
    def __init__(self):
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'FFmpegUtils wird initialisiert')
        self._ffmpeg_path = get_ffmpeg_path()
        self._ffprobe_path = get_ffprobe_path()
        self._ffmpeg_available = None
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Pfad: %s', self._ffmpeg_path)
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFprobe-Pfad: %s', self._ffprobe_path)

    def is_available(self) -> bool:
        """Prüft ob FFmpeg verfügbar ist (mit Caching)"""
        herkunft = 'ffmpeg_utils.py'
        if self._ffmpeg_available is None:
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Prüfe FFmpeg-Verfügbarkeit erstmalig')
            self._ffmpeg_available = self._check_ffmpeg()
        else:
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende gecachte FFmpeg-Verfügbarkeit: %s', self._ffmpeg_available)
        return self._ffmpeg_available

    def _check_ffmpeg(self) -> bool:
        """Prüft FFmpeg-Verfügbarkeit"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Führe FFmpeg-Verfügbarkeitsprüfung durch')
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
            if available:
                log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'FFmpeg erfolgreich gefunden und funktionsfähig')
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Version verfügbar')
            else:
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg-Aufruf fehlgeschlagen - Returncode: %d', result.returncode)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg stderr: %s', result.stderr)
            return available
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg-Verfügbarkeitsprüfung: Timeout erreicht')
            return False
        except FileNotFoundError:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg-Binary nicht gefunden: %s', self._ffmpeg_path)
            return False
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei FFmpeg-Verfügbarkeitsprüfung: %s', str(e))
            return False

    def _sanitize_file_path(self, file_path: str) -> str:
        """Bereinigt und validiert Dateipfade"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Validiere Dateipfad: %s', os.path.basename(file_path))
        # Normalisiere Pfad
        normalized = os.path.normpath(file_path)
        # Prüfe auf Path Traversal
        if ".." in normalized:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unsicherer Pfad erkannt (Path Traversal): %s', file_path)
            raise AudioProcessingError(f"Unsicherer Pfad erkannt: {file_path}")
        # Prüfe auf gefährliche Zeichen
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
        for char in dangerous_chars:
            if char in normalized:
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Gefährliches Zeichen im Pfad: %s in %s', char, file_path)
                raise AudioProcessingError(f"Gefährliches Zeichen in Pfad: {char}")
        # Validiere Existenz
        if not os.path.exists(normalized):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Datei nicht gefunden: %s', normalized)
            raise AudioProcessingError(f"Datei nicht gefunden: {normalized}")
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Dateipfad erfolgreich validiert')
        return normalized

    def _validate_sample_rate(self, sample_rate: int) -> int:
        """Validiert Sample-Rate"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Validiere Sample-Rate: %d', sample_rate)
        if not isinstance(sample_rate, int):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Sample-Rate ist keine Ganzzahl: %s (Typ: %s)', sample_rate, type(sample_rate))
            raise AudioProcessingError("Sample-Rate muss eine Ganzzahl sein")
        if not (8000 <= sample_rate <= 192000):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Ungültige Sample-Rate: %d Hz (erlaubt: 8000-192000 Hz)', sample_rate)
            raise AudioProcessingError(f"Ungültige Sample-Rate: {sample_rate}")
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Sample-Rate erfolgreich validiert: %d Hz', sample_rate)
        return sample_rate

    def extract_audio(self, media_path: str, wav_path: str, sample_rate: int = 48000) -> None:
        """Extrahiert Audio aus Video als Mono-WAV mit verbesserter Sicherheit"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio-Extraktion wird gestartet')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Video-Eingabe: %s', os.path.basename(media_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Audio-Ausgabe: %s', os.path.basename(wav_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Ziel-Sample-Rate: %d Hz', sample_rate)
        if not self.is_available():
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg ist nicht verfügbar für Audio-Extraktion')
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        # Sichere Validierung
        safe_media_path = self._sanitize_file_path(media_path)
        safe_sample_rate = self._validate_sample_rate(sample_rate)
        # Ausgabepfad normalisieren (aber nicht validieren, da er noch nicht existiert)
        safe_wav_path = os.path.normpath(wav_path)
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Sichere Pfade validiert')
        cmd = [
            self._ffmpeg_path,
            "-hide_banner",  # Reduziert Info-Leakage
            "-loglevel", "error",  # Nur Fehler ausgeben
            "-y",
            "-i", safe_media_path,
            "-vn",  # Kein Video
            "-acodec", "pcm_s16le",
            "-ar", str(safe_sample_rate),
            "-ac", "1",  # Mono
            "-t", "3600",  # Max 1 Stunde (DoS-Schutz)
            safe_wav_path
        ]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Kommando vorbereitet mit %d Parametern', len(cmd))
        try:
            # Prozess mit Working Directory starten
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 Minuten max
                cwd=os.path.dirname(safe_wav_path)
            )
            if result.returncode != 0:
                # Gefilterte Fehlerausgabe
                safe_error = self._filter_error_message(result.stderr)
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Audio-Extraktion fehlgeschlagen - Returncode: %d', result.returncode)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg stderr (gefiltert): %s', safe_error)
                raise AudioProcessingError(f"FFmpeg Audio-Extraktion fehlgeschlagen: {safe_error}")
            # Prüfe ob Ausgabedatei erstellt wurde
            if not os.path.exists(safe_wav_path):
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Audio-Datei wurde nicht erstellt: %s', os.path.basename(safe_wav_path))
                raise AudioProcessingError("Audio-Datei wurde nicht erstellt")
            # Erfolg loggen
            file_size = os.path.getsize(safe_wav_path) / 1024  # KB
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio erfolgreich extrahiert: %d Hz Mono WAV', safe_sample_rate)
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Ausgabedatei: %s (%.1f KB)', os.path.basename(safe_wav_path), file_size)
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Audio-Extraktion: Timeout nach 10 Minuten erreicht')
            raise AudioProcessingError("FFmpeg Audio-Extraktion: Timeout erreicht")
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei Audio-Extraktion: %s', str(e))
            raise AudioProcessingError(f"FFmpeg Audio-Extraktion: {str(e)}")
        
    def convert_to_wav(self, input_path: str, wav_path: str, sample_rate: int = 48000) -> None:
        """Konvertiert eine Audio-Datei zu Mono-WAV"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio-Konvertierung zu WAV gestartet')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Input: %s', os.path.basename(input_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Output: %s', os.path.basename(wav_path))

        if not self.is_available():
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")

        safe_input = self._sanitize_file_path(input_path)
        safe_sample_rate = self._validate_sample_rate(sample_rate)
        safe_wav_path = os.path.normpath(wav_path)

        cmd = [
            self._ffmpeg_path,
            "-hide_banner", "-loglevel", "error",
            "-y", "-i", safe_input,
            "-acodec", "pcm_s16le",
            "-ar", str(safe_sample_rate),
            "-ac", "1",  # Mono
            "-t", "3600",  # Max 1 Stunde
            safe_wav_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                safe_error = self._filter_error_message(result.stderr)
                raise AudioProcessingError(f"FFmpeg Konvertierung fehlgeschlagen: {safe_error}")
            if not os.path.exists(safe_wav_path):
                raise AudioProcessingError("WAV-Datei wurde nicht erstellt")
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio erfolgreich zu WAV konvertiert')
        except Exception as e:
            raise AudioProcessingError(f"FFmpeg Konvertierung: {str(e)}")

    def convert_from_wav(self, input_wav: str, output_path: str, ext: str, bitrate: str, sample_rate: str, channels: int = 1) -> None:
        """Konvertiert WAV zurück zu Original-Audio-Format mit Parametern"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Konvertiere WAV zu Audio-Format')
        
        # Wähle Codec basierend auf Extension (erweitere bei Bedarf)
        codec = "libmp3lame" if ext.lower() == '.mp3' else "aac"  # Fallback für andere (z.B. .m4a)
        
        cmd = [
            self._ffmpeg_path, "-y",
            "-i", input_wav,
            "-c:a", codec,
            "-b:a", bitrate,  # Original-Bitrate (z.B. "256k")
            "-ar", str(sample_rate),  # Original-Sample-Rate
            "-ac", str(channels),  # Original-Kanäle (1=Mono, 2=Stereo)
            output_path
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            safe_error = self._filter_error_message(result.stderr)
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Konvertierung fehlgeschlagen - Returncode: %d', result.returncode)
            raise AudioProcessingError(f"Audio-Konvertierung fehlgeschlagen: {safe_error}")
        
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Konvertierung abgeschlossen')

    def _get_codec_for_format(self, ext: str) -> str:
        """Wählt Codec basierend auf Extension (erweiterbar)"""
        codecs = {
            '.mp3': 'libmp3lame',
            '.aac': 'aac',
            '.wav': 'pcm_s16le',
            '.flac': 'flac',
            '.ogg': 'libvorbis',
            '.opus': 'libopus'
        }
        return codecs.get(ext, 'copy')  # Fallback: Copy wenn unbekannt

    def _filter_error_message(self, error_output: str) -> str:
        """Filtert sensitive Informationen aus Fehlermeldungen"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Filtere FFmpeg-Fehlermeldung (Länge: %d Zeichen)', len(error_output))
        import re
        filtered = error_output
        # Entferne Dateipfade
        path_patterns = [
            r'[A-Za-z]:\\[^:\s]+',  # Windows-Pfade
            r'/[^\s]+',  # Unix-Pfade
        ]
        for pattern in path_patterns:
            filtered = re.sub(pattern, '[PFAD_ENTFERNT]', filtered)
        # Begrenze Länge
        filtered = filtered[:200]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Fehlermeldung gefiltert (neue Länge: %d Zeichen)', len(filtered))
        return filtered

    def mux_audio_back(self, media_path: str, audio_path: str, output_path: str) -> None:
        """Ersetzt Audio-Spur in Video (ohne Video-Neukodierung)"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio-Video-Zusammenführung wird gestartet')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Video-Eingabe: %s', os.path.basename(media_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Audio-Eingabe: %s', os.path.basename(audio_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Video-Ausgabe: %s', os.path.basename(output_path))
        if not self.is_available():
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg ist nicht verfügbar für Video-Zusammenführung')
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        # Eingabedateien validieren
        if not os.path.exists(media_path):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Video-Datei existiert nicht: %s', media_path)
            raise AudioProcessingError(f"Video-Datei existiert nicht: {media_path}")
        if not os.path.exists(audio_path):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Audio-Datei existiert nicht: %s', audio_path)
            raise AudioProcessingError(f"Audio-Datei existiert nicht: {audio_path}")
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Eingabedateien validiert')
        cmd = [
            self._ffmpeg_path, "-y",
            "-i", media_path,
            "-i", audio_path,
            "-map", "0:v:0",  # Video vom ersten Input
            "-map", "1:a:0",  # Audio vom zweiten Input
            "-c:v", "copy",  # Video nicht neu kodieren
            "-c:a", "aac",  # Audio als AAC kodieren
            "-b:a", "128k",  # Audio-Bitrate
            output_path
        ]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Kommando für Video-Zusammenführung vorbereitet')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                safe_error = self._filter_error_message(result.stderr)
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Video-Zusammenführung fehlgeschlagen - Returncode: %d', result.returncode)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg stderr (gefiltert): %s', safe_error)
                raise AudioProcessingError(f"FFmpeg Video-Zusammenführung fehlgeschlagen: {safe_error}")
            if not os.path.exists(output_path):
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Ausgabe-Video wurde nicht erstellt: %s', os.path.basename(output_path))
                raise AudioProcessingError("Ausgabe-Video wurde nicht erstellt")
            # Erfolg loggen
            output_size = os.path.getsize(output_path) / (1024*1024)  # MB
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio erfolgreich in Video eingebettet')
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Finale Video-Datei: %s (%.1f MB)', os.path.basename(output_path), output_size)
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Video-Zusammenführung: Timeout nach 10 Minuten erreicht')
            raise AudioProcessingError("FFmpeg Video-Zusammenführung: Timeout erreicht")
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei Video-Zusammenführung: %s', str(e))
            raise AudioProcessingError(f"FFmpeg Video-Zusammenführung: {str(e)}")

    def apply_basic_filter(self, input_wav: str, output_wav: str) -> None:
        """Wendet einfache Audio-Filter an (Fallback-Methode)"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'FFmpeg Basis-Filter werden angewendet')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Eingabe: %s', os.path.basename(input_wav))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Ausgabe: %s', os.path.basename(output_wav))
        if not self.is_available():
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg ist nicht verfügbar für Filter-Anwendung')
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        if not os.path.exists(input_wav):
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Audio-Eingabedatei existiert nicht: %s', input_wav)
            raise AudioProcessingError(f"Audio-Datei existiert nicht: {input_wav}")
        # Filter-Kette: High-Pass, Low-Pass, Lautstärke
        filter_chain = "highpass=f=80,lowpass=f=8000,volume=1.2"
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Filter-Kette: %s', filter_chain)
        cmd = [
            self._ffmpeg_path, "-y",
            "-i", input_wav,
            "-af", filter_chain,
            output_wav
        ]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Kommando für Filter vorbereitet')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                safe_error = self._filter_error_message(result.stderr)
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Filter fehlgeschlagen - Returncode: %d', result.returncode)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg stderr (gefiltert): %s', safe_error)
                raise AudioProcessingError(f"FFmpeg Filter fehlgeschlagen: {safe_error}")
            if not os.path.exists(output_wav):
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Gefilterte Audio-Datei wurde nicht erstellt: %s', os.path.basename(output_wav))
                raise AudioProcessingError("Gefilterte Audio-Datei wurde nicht erstellt")
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'FFmpeg Basis-Filter erfolgreich angewendet')
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Gefilterte Datei erstellt: %s', os.path.basename(output_wav))
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg Filter: Timeout nach 2 Minuten erreicht')
            raise AudioProcessingError("FFmpeg Filter: Timeout erreicht")
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei Filter-Anwendung: %s', str(e))
            raise AudioProcessingError(f"FFmpeg Filter: {str(e)}")

    def get_video_info(self, media_path: str) -> dict:
        """Extrahiert Video-Informationen mit FFprobe"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Extrahiere Video-Informationen: %s', os.path.basename(media_path))
        if not self.is_available():
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg ist nicht verfügbar für Video-Info-Extraktion')
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        cmd = [
            self._ffprobe_path, "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            media_path
        ]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFprobe-Kommando vorbereitet')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                safe_error = self._filter_error_message(result.stderr)
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFprobe fehlgeschlagen - Returncode: %d', result.returncode)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFprobe stderr (gefiltert): %s', safe_error)
                raise AudioProcessingError(f"FFprobe fehlgeschlagen: {safe_error}")
            # JSON parsen
            import json
            video_info = json.loads(result.stdout)
            # Log-Zusammenfassung der wichtigsten Infos
            if 'format' in video_info:
                duration = float(video_info['format'].get('duration', 0))
                file_size = int(video_info['format'].get('size', 0)) / (1024*1024)  # MB
                log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Video-Informationen extrahiert - Dauer: %.1f s, Größe: %.1f MB', duration, file_size)
                log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Video-Info JSON erfolgreich geparst')
            return video_info
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFprobe: Timeout nach 30 Sekunden erreicht')
            raise AudioProcessingError("FFprobe: Timeout erreicht")
        except json.JSONDecodeError as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFprobe JSON-Parsing fehlgeschlagen: %s', str(e))
            raise AudioProcessingError(f"FFprobe JSON-Parsing: {str(e)}")
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei Video-Info-Extraktion: %s', str(e))
            raise AudioProcessingError(f"FFprobe: {str(e)}")

    def extract_audio_preview(self, media_path: str, wav_path: str, duration: int = 30, sample_rate: int = None) -> None:
        """Extrahiert Audio-Vorschau mit variabler Sample-Rate"""
        herkunft = 'ffmpeg_utils.py'
        log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio-Vorschau-Extraktion wird gestartet')
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Video: %s', os.path.basename(media_path))
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Vorschau-Dauer: %d Sekunden', duration)
        if not self.is_available():
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'FFmpeg ist nicht verfügbar für Vorschau-Extraktion')
            raise FFmpegNotFoundError("FFmpeg ist nicht verfügbar")
        # Automatische Sample-Rate falls nicht spezifiziert
        if sample_rate is None:
            sample_rate = 22050  # Standard-Fallback
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende Standard-Sample-Rate für Vorschau: %d Hz', sample_rate)
        else:
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Verwende spezifizierte Sample-Rate: %d Hz', sample_rate)
        safe_media_path = self._sanitize_file_path(media_path)
        safe_wav_path = os.path.normpath(wav_path)
        cmd = [
            self._ffmpeg_path,
            "-hide_banner", "-loglevel", "error",
            "-y",
            "-i", safe_media_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-t", str(duration),
            safe_wav_path
        ]
        log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'FFmpeg-Kommando für Vorschau vorbereitet')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                safe_error = self._filter_error_message(result.stderr)
                log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Audio-Vorschau-Extraktion fehlgeschlagen - Returncode: %d', result.returncode)
                raise AudioProcessingError(f"Audio-Vorschau-Extraktion fehlgeschlagen: {safe_error}")
            log_with_prefix(logger, 'info', 'FFMPEG', herkunft, 'Audio-Vorschau erfolgreich erstellt: %d s @ %d Hz Mono', duration, sample_rate)
            log_with_prefix(logger, 'debug', 'FFMPEG', herkunft, 'Vorschau-Datei: %s', os.path.basename(safe_wav_path))
        except subprocess.TimeoutExpired:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Audio-Vorschau-Extraktion: Timeout nach 1 Minute erreicht')
            raise AudioProcessingError("Audio-Vorschau-Extraktion: Timeout erreicht")
        except Exception as e:
            log_with_prefix(logger, 'error', 'FFMPEG', herkunft, 'Unerwarteter Fehler bei Vorschau-Extraktion: %s', str(e))
            raise AudioProcessingError(f"Audio-Vorschau-Extraktion: {str(e)}")

"""Audio-Vorschau-Widget mit Verarbeitung und Play/Pause/Stop-Funktionalität"""

import sys
import tkinter as tk
import customtkinter as ctk
import threading
import time
import os
import shutil
from typing import Optional
import tempfile
import numpy as np
import logging

# NEU: Import für log_with_prefix (behebt 'not defined'-Fehler)
from utils.logger import log_with_prefix
from utils.config import Config  # NEU: Import für Konfiguration

from audio.ffmpeg_utils import FFmpegUtils

# Logger konfigurieren
logger = logging.getLogger(__name__)

# Playsound/Winsound-Setup (vereinfacht, ohne Subprocess)
PLAYSOUND_AVAILABLE = False
WINSOUND_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
    logger.info("Playsound erfolgreich geladen")
except ImportError:
    pass

if getattr(sys, 'frozen', False) and os.name == 'nt':
    try:
        import winsound
        WINSOUND_AVAILABLE = True
        logger.info("Winsound erfolgreich geladen (EXE-Modus)")
    except ImportError:
        pass

class AudioPreviewPlayer:
    """Vereinfachter Audio-Player mit korrektem Progress-Update"""

    def __init__(self):
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'AudioPreviewPlayer wird initialisiert (vereinfacht)')
        self.is_exe = getattr(sys, 'frozen', False)
        self.use_winsound = self.is_exe and WINSOUND_AVAILABLE and os.name == 'nt'
        self.is_playing = False
        self.is_paused = False  # NEU: Pause-Status
        self.current_file = None
        self.duration = 0
        self.position = 0
        self.play_thread = None
        self.should_stop = threading.Event()
        self.start_time = None
        self.pause_time = None  # NEU: Pause-Zeitpunkt
        self._player_lock = threading.Lock()

    def is_available(self) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Prüfe Audio-Wiedergabe-Verfügbarkeit')
        return PLAYSOUND_AVAILABLE or self.use_winsound

    def load(self, wav_path: str) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Datei wird geladen: %s', os.path.basename(wav_path))
        if not self.is_available():
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Keine Audio-Wiedergabe-Methode verfügbar')
            return False
        self.stop()
        self.current_file = wav_path
        try:
            import soundfile as sf
            info = sf.info(wav_path)
            self.duration = min(30, info.duration)
        except:
            file_size = os.path.getsize(wav_path)
            self.duration = min(30, file_size / (22050 * 2))
        return True

    def play(self) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird gestartet')
        if not self.current_file:
            return False
        with self._player_lock:
            if self.is_playing and not self.is_paused:
                return False
            # Resume von Pause oder neuer Start
            if self.is_paused:
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Resume von Pause')
                self.is_paused = False
                # Adjust start_time für korrekte Position
                if self.pause_time and self.start_time:
                    pause_duration = self.pause_time - self.start_time
                    self.start_time = time.time() - pause_duration
                self.is_playing = True
                return True
            else:
                # Neuer Start
                self.stop()
                def play_worker():
                    try:
                        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Play-Worker Thread gestartet')
                        if self.use_winsound:
                            winsound.PlaySound(self.current_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                            # Warte auf Ende oder Stop-Signal
                            elapsed = 0
                            while elapsed < self.duration and not self.should_stop.is_set():
                                time.sleep(0.1)
                                elapsed += 0.1
                        else:
                            playsound(self.current_file, block=True)
                        if not self.should_stop.is_set():
                            self.is_playing = False
                            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Wiedergabe natürlich beendet')
                    except Exception as e:
                        log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Wiedergabe fehlgeschlagen: %s', str(e))
                        self.is_playing = False
                self.should_stop.clear()
                self.play_thread = threading.Thread(target=play_worker, daemon=True)
                self.play_thread.start()
                self.is_playing = True
                self.is_paused = False
                self.start_time = time.time()
                self.pause_time = None
                return True

    def pause(self):
        """Echte Pause-Funktionalität"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird pausiert')
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.pause_time = time.time()
            # Position zum Pause-Zeitpunkt speichern
            if self.start_time:
                self.position = self.pause_time - self.start_time
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Audio pausiert bei Position: %.2f s', self.position)

    def stop(self):
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird gestoppt')
        self.should_stop.set()
        if self.use_winsound:
            try:
                winsound.PlaySound(None, 0)
            except:
                pass
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.start_time = None
        self.pause_time = None

    def get_status(self) -> dict:
        """Korrigierte Status-Berechnung"""
        if self.is_playing and not self.is_paused and self.start_time:
            # Laufende Wiedergabe
            self.position = min(self.duration, time.time() - self.start_time)
        elif self.is_paused and self.pause_time and self.start_time:
            # Pausiert - Position eingefroren
            self.position = min(self.duration, self.pause_time - self.start_time)
        return {
            "playing": self.is_playing and not self.is_paused,
            "paused": self.is_paused,
            "position": self.position,
            "duration": self.duration
        }

    def cleanup(self):
        self.stop()

class AudioPreviewWidget(ctk.CTkFrame):
    """Audio-Vorschau-Widget mit Verarbeitung"""

    def __init__(self, parent, width=300):
        super().__init__(parent, width=width)
        self._width = width
        self.player = AudioPreviewPlayer()
        self.ffmpeg = FFmpegUtils()
        self.current_video = None
        self.temp_preview_file = None
        self.processed_preview_file = None
        self.update_thread = None
        self.should_update = False
        self.is_processing = False
        self.used_methods = None
        self.processing_details = {}
        self.main_window = None
        self._create_ui()

    def set_main_window(self, main_window):
        self.main_window = main_window

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Erstelle AudioPreview UI-Komponenten')
        # Titel
        title = ctk.CTkLabel(self, text="🎵 Audio-Vorschau",
                             font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(10, 5))
        # Info-Text
        self.info_label = ctk.CTkLabel(self, text="Datei in Liste wählen",
                                       font=ctk.CTkFont(size=11),
                                       text_color="gray")
        self.info_label.pack(pady=2)
        # Status-Label (für Processing-Info)
        self.status_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=10),
                                         text_color="orange")
        self.status_label.pack(pady=2)
        # Button-Container
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        # Play/Pause Button (kombiniert)
        self.play_pause_btn = ctk.CTkButton(
            button_frame, text="▶️", width=50, height=35,
            command=self._toggle_play_pause
        )
        self.play_pause_btn.pack(side="left", padx=5)
        # Stop Button
        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏹️", width=50, height=35,
            command=self._stop
        )
        self.stop_btn.pack(side="left", padx=5)
        # Process Button
        self.process_btn = ctk.CTkButton(
            button_frame, text="🔄", width=50, height=35,
            command=self._process_preview,
            font=ctk.CTkFont(size=12)
        )
        self.process_btn.pack(side="left", padx=5)
        # Zeit-Anzeige
        self.time_label = ctk.CTkLabel(button_frame, text="00:00/00:00",
                                       font=ctk.CTkFont(size=10))
        self.time_label.pack(side="right", padx=5)
        # Fortschrittsbalken
        self.progress = ctk.CTkProgressBar(self, width=self._width-40)
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        # Initial deaktiviert
        self._set_controls_enabled(False)
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'UI-Komponenten erfolgreich erstellt')

    def load_video(self, video_path: str):
        """Lädt Video für Audio-Vorschau"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Video wird für Audio-Vorschau geladen: %s', os.path.basename(video_path))
        self.current_video = video_path
        self.info_label.configure(text=f"Lade: {os.path.basename(video_path)}")
        self.status_label.configure(text="")
        # Verarbeitete Datei zurücksetzen
        self.processed_preview_file = None
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Vorherige verarbeitete Vorschau zurückgesetzt')
        # In separatem Thread laden
        threading.Thread(target=self._load_video_async,
                         args=(video_path,), daemon=True).start()

    def _load_video_async(self, video_path: str):
        """Lädt Video asynchron (nur Extraktion, keine Verarbeitung)"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Asynchrone Video-Ladung gestartet')
        try:
            # Temporäre Vorschau-Datei erstellen
            if self.temp_preview_file:
                try:
                    os.remove(self.temp_preview_file)
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Alte temporäre Vorschau-Datei gelöscht')
                except:
                    log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Alte temporäre Datei konnte nicht gelöscht werden')
            # Neue temporäre Datei
            temp_dir = tempfile.gettempdir()
            temp_name = f"audio_preview_{int(time.time())}.wav"
            self.temp_preview_file = os.path.join(temp_dir, temp_name)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Neue temporäre Vorschau-Datei: %s', os.path.basename(self.temp_preview_file))
            # Audio extrahieren (30s Vorschau)
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Extrahiere 30s Audio-Vorschau aus Video')
            self.ffmpeg.extract_audio_preview(video_path, self.temp_preview_file)
            self._debug_audio_info(self.temp_preview_file, "Original-Vorschau")
            # UI aktualisieren (im Main Thread)
            self.after(0, self._on_load_success)
        except Exception as e:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Asynchrone Video-Ladung fehlgeschlagen: %s', str(e))
            self.after(0, self._on_load_error, str(e))

    def _on_load_success(self):
        """Erfolgreich geladen"""
        herkunft = 'audio_preview.py'
        filename = os.path.basename(self.current_video) if self.current_video else "Unbekannt"
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Video-Vorschau erfolgreich geladen: %s', filename)
        self.info_label.configure(text=f"Bereit: {filename}")
        self.status_label.configure(text="Klicke 🔄 für Verarbeitung oder ▶️ für Original")
        self._set_controls_enabled(True)

    def _on_load_error(self, error_msg: str):
        """Fehler beim Laden"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Video-Vorschau-Ladung fehlgeschlagen: %s', error_msg)
        self.info_label.configure(text=f"Fehler: {error_msg}")
        self.status_label.configure(text="")
        self._set_controls_enabled(False)

    def _process_preview(self):
        """Verarbeitet die Audio-Vorschau mit aktuellen Einstellungen"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Vorschau-Verarbeitung wird gestartet')
        if not self.temp_preview_file or not self.main_window:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Vorschau-Verarbeitung nicht möglich - fehlende Datei oder Hauptfenster-Referenz')
            return
        self.is_processing = True
        self.status_label.configure(text="🔄 Verarbeitung läuft...")
        self._set_controls_enabled(False, processing=True)
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'UI für Verarbeitung vorbereitet')
        # In separatem Thread verarbeiten
        threading.Thread(target=self._process_preview_async, daemon=True).start()

    def _process_preview_async(self):
        """Verarbeitet Audio-Vorschau asynchron - mit methodenspezifischer Sample-Rate"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Asynchrone Vorschau-Verarbeitung gestartet')
        try:
            from audio.processors import VideoProcessor
            # Konfiguration vom Hauptfenster sammeln
            config = self.main_window._collect_processing_config()
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitungskonfiguration vom Hauptfenster erhalten')
            # Sample-Rate basierend auf gewählter Rauschreduzierungsmethode
            noise_method = config['method']
            if noise_method == "deepfilternet3":
                target_sample_rate = 48000
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'DeepFilterNet3 erkannt - verwende 48kHz Vorschau')
            else:
                target_sample_rate = 22050
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Andere Methode erkannt - verwende 22kHz Vorschau für Performance')
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Ziel-Sample-Rate: %d Hz', target_sample_rate)
            # Temporäre Datei für verarbeitetes Audio
            temp_dir = tempfile.gettempdir()
            processed_name = f"processed_preview_{int(time.time())}.wav"
            self.processed_preview_file = os.path.join(temp_dir, processed_name)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitete Vorschau-Datei: %s', os.path.basename(self.processed_preview_file))
            # Mini-Processor erstellen
            processor = VideoProcessor()
            with tempfile.TemporaryDirectory(prefix="preview_") as temp_processing_dir:
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Temporäres Verarbeitungsverzeichnis erstellt')
                # Zwischendateien - alle mit methodenspezifischer Sample-Rate
                wav_input = os.path.join(temp_processing_dir, f"input_{target_sample_rate}.wav")
                wav_normalized = os.path.join(temp_processing_dir, f"norm_{target_sample_rate}.wav")
                wav_processed = os.path.join(temp_processing_dir, f"proc_{target_sample_rate}.wav")
                # 1. Original-Vorschau zur Ziel-Sample-Rate konvertieren
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Schritt 1: Sample-Rate-Konvertierung')
                self._convert_to_target_sample_rate(self.temp_preview_file, wav_input, target_sample_rate)
                # 2. LUFS-Normalisierung
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Schritt 2: LUFS-Normalisierung auf %.1f LUFS', config['target_lufs'])
                processor._normalize_loudness(wav_input, wav_normalized, config['target_lufs'])
                # 3. Rauschreduzierung
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Schritt 3: Rauschreduzierung mit Methode: %s', noise_method)
                used_method = processor._process_with_fallback(
                    wav_normalized, wav_processed, noise_method,
                    config['method_params'], None
                )
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Rauschreduzierung abgeschlossen: %s', used_method)
                # 4. Voice Enhancement (falls aktiviert)
                if config['voice_enhancement']:
                    log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Schritt 4: Voice Enhancement aktiviert')
                    wav_enhanced = os.path.join(temp_processing_dir, f"enhanced_{target_sample_rate}.wav")
                    voice_method = config.get('voice_method', 'classic')
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Voice Enhancement Methode: %s', voice_method)
                    if voice_method == "speechbrain":
                        # SpeechBrain mit expliziter Sample-Rate-Kontrolle
                        from audio.speechbrain_voice_enhancer import SpeechBrainVoiceEnhancer
                        enhancer = SpeechBrainVoiceEnhancer()
                        if enhancer.is_available():
                            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende SpeechBrain Voice Enhancement')
                            voice_settings = config['voice_settings'].copy()
                            voice_settings['original_sample_rate'] = target_sample_rate
                            voice_settings['target_sample_rate'] = target_sample_rate
                            enhancer.process(wav_processed, wav_enhanced, voice_settings)
                            used_method += " + SpeechBrain"
                            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitung: ✅ Gelungen (Methode: SpeechBrain AI)')  # NEU: INFO für Erfolg und Herkunft
                            if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitung: Details - Input: %s, Output: %s', wav_processed, wav_enhanced)
                        else:
                            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Initialisierung: ❌ Nicht verfügbar - Fallback zu klassisch')
                            from audio.voice_enhancer import VoiceAudioEnhancer
                            enhancer = VoiceAudioEnhancer()
                            enhancer.process(wav_processed, wav_enhanced, config['voice_settings'])
                            used_method += " + Voice-Klassisch"
                            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, '🔄 Klassisches Voice Enhancement als Fallback angewendet')
                    else:
                        # Klassische Voice Enhancement
                        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende klassisches Voice Enhancement')
                        from audio.voice_enhancer import VoiceAudioEnhancer
                        enhancer = VoiceAudioEnhancer()
                        enhancer.process(wav_processed, wav_enhanced, config['voice_settings'])
                        used_method += " + Voice-Klassisch"
                        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, '✅ Klassisches Voice Enhancement angewendet')
                    # Finale Audio-Datei für Wiedergabe vorbereiten
                    self._prepare_final_preview(wav_enhanced, self.processed_preview_file, target_sample_rate)
                else:
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Voice Enhancement deaktiviert')
                    # Keine Voice Enhancement
                    self._prepare_final_preview(wav_processed, self.processed_preview_file, target_sample_rate)
            # UI im Main Thread aktualisieren
            self.after(0, self._on_process_success, used_method)
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitung: ✅ Abgeschlossen mit Methode %s', used_method)  # NEU: INFO für Abschluss und Herkunft
            if Config.get_debug_mode():  # NEU: DEBUG nur bei aktiviertem Modus
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitung: Details - Sample-Rate: %d Hz', target_sample_rate)
        except Exception as e:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Asynchrone Vorschau-Verarbeitung fehlgeschlagen: %s', str(e))
            self.after(0, self._on_process_error, str(e))

    def _convert_to_target_sample_rate(self, input_path: str, output_path: str, target_rate: int):
        """Konvertiert Audio zur Ziel-Sample-Rate für die gewählte Methode"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Sample-Rate-Konvertierung: Ziel %d Hz', target_rate)
        try:
            import soundfile as sf
            # Prüfe aktuelle Sample-Rate
            info = sf.info(input_path)
            current_rate = int(info.samplerate)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Aktuelle Sample-Rate: %d Hz', current_rate)
            if current_rate == target_rate:
                # Bereits korrekt - einfach kopieren
                import shutil
                shutil.copy2(input_path, output_path)
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio bereits bei %d Hz - kopiert', target_rate)
            else:
                # FFmpeg-Konvertierung zur Ziel-Sample-Rate
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'FFmpeg-Konvertierung erforderlich: %d Hz → %d Hz', current_rate, target_rate)
                cmd = [
                    self.ffmpeg._ffmpeg_path,
                    "-hide_banner", "-loglevel", "error",
                    "-y", "-i", input_path,
                    "-ar", str(target_rate), "-ac", "1",
                    "-acodec", "pcm_s16le",
                    output_path
                ]
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(f"Sample-Rate-Konvertierung fehlgeschlagen: {result.stderr}")
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio erfolgreich konvertiert: %d Hz → %d Hz', current_rate, target_rate)
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Sample-Rate-Konvertierung fehlgeschlagen: %s', str(e))
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende Fallback: Kopiere Original-Datei')
            # Fallback: Datei kopieren
            import shutil
            shutil.copy2(input_path, output_path)

    def _prepare_final_preview(self, input_path: str, output_path: str, current_rate: int):
        """Bereitet finale Vorschau-Datei für optimale Wiedergabe vor"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Bereite finale Vorschau für Wiedergabe vor')
        try:
            # Für die Wiedergabe: Konvertiere zu einer Standard-Rate falls nötig
            # playsound funktioniert am besten mit Standard-Raten
            playback_rate = 44100 if current_rate > 32000 else 22050
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Optimale Wiedergabe-Rate bestimmt: %d Hz', playback_rate)
            if current_rate != playback_rate:
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Konvertierung für Wiedergabe erforderlich: %d Hz → %d Hz', current_rate, playback_rate)
                cmd = [
                    self.ffmpeg._ffmpeg_path,
                    "-hide_banner", "-loglevel", "error",
                    "-y", "-i", input_path,
                    "-ar", str(playback_rate), "-ac", "1",
                    "-acodec", "pcm_s16le",
                    output_path
                ]
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(f"Playback-Konvertierung fehlgeschlagen: {result.stderr}")
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Für Wiedergabe konvertiert: %d Hz → %d Hz', current_rate, playback_rate)
            else:
                # Bereits optimale Rate
                import shutil
                shutil.copy2(input_path, output_path)
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Wiedergabe-Rate bereits optimal: %d Hz', current_rate)
            # Debug-Info für finale Datei
            self._debug_audio_info(output_path, "Finale Vorschau für Wiedergabe")
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Playback-Vorbereitung fehlgeschlagen: %s', str(e))
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende Fallback: Kopiere Eingabe-Datei')
            # Fallback: Original verwenden
            import shutil
            shutil.copy2(input_path, output_path)

    def _on_process_success(self, used_method: str):
        """Verarbeitung erfolgreich abgeschlossen"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Vorschau-Verarbeitung erfolgreich abgeschlossen: %s', used_method)
        self.is_processing = False
        self.used_methods = used_method
        self.status_label.configure(text=f"✅ Verarbeitet mit {used_method}")
        self._set_controls_enabled(True)
        # Verarbeitete Datei in Player laden
        if self.player.load(self.processed_preview_file):
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitete Vorschau in Player geladen')
            self._start_progress_update()
        else:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Verarbeitete Vorschau konnte nicht in Player geladen werden')

    def _on_process_error(self, error_msg: str):
        """Verarbeitungsfehler"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Vorschau-Verarbeitung fehlgeschlagen: %s', error_msg)
        self.is_processing = False
        self.status_label.configure(text=f"❌ Fehler: {error_msg}")
        self._set_controls_enabled(True)

    def _toggle_play_pause(self):
        """Play/Pause umschalten - mit echter Pause-Funktionalität"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Play/Pause-Toggle wurde ausgelöst')
        if self.is_processing:
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Toggle während Verarbeitung ignoriert')
            return
        # Bestimme welche Datei gespielt werden soll
        target_file = None
        file_type = "original"
        if self.processed_preview_file and os.path.exists(self.processed_preview_file):
            target_file = self.processed_preview_file
            file_type = "verarbeitet"
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verwende verarbeitete Vorschau-Datei')
        elif self.temp_preview_file and os.path.exists(self.temp_preview_file):
            target_file = self.temp_preview_file
            file_type = "original"
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verwende Original-Vorschau-Datei')
        if not target_file:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Keine Datei zum Abspielen verfügbar')
            return
        # Player mit neuer Datei laden falls nötig
        if self.player.current_file != target_file:
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Lade neue Datei in Player: %s', file_type)
            if not self.player.load(target_file):
                log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Konnte %s Datei nicht in Player laden', file_type)
                return
        # Play/Pause Toggle
        status = self.player.get_status()
        if status["playing"]:
            # Pausieren
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Pausiere Wiedergabe: %s', file_type)
            self.player.pause()
            self.play_pause_btn.configure(text="▶️")
            # Progress-Updates weiterlaufen lassen für Pause-Anzeige
            if file_type == "verarbeitet" and self.used_methods:
                self.status_label.configure(text=f"⏸️ Pausiert: {self.used_methods}")
            else:
                self.status_label.configure(text="⏸️ Pausiert: Original")
        else:
            # Starten/Fortsetzen
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Starte/Setze fort Wiedergabe: %s', file_type)
            if self.player.play():
                self.play_pause_btn.configure(text="⏸️")
                # Progress-Updates garantiert starten
                self._start_progress_update()
                if file_type == "verarbeitet" and self.used_methods:
                    self.status_label.configure(text=f"🎵 Spielt: {self.used_methods}")
                else:
                    self.status_label.configure(text="🎵 Spielt: Original")
            else:
                log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Wiedergabe-Start fehlgeschlagen')

    def _stop(self):
        """Wiedergabe stoppen - mit korrigiertem Progress-Reset"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Stoppe Wiedergabe')
        # **FIX: Progress-Updates explizit stoppen**
        self.should_update = False
        # Player stoppen
        self.player.stop()
        # **FIX: UI sofort zurücksetzen**
        self.play_pause_btn.configure(text="▶️")
        self.progress.set(0)
        self.time_label.configure(text="00:00/00:00")
        # Zeige Methode wenn verarbeitete Version verfügbar
        if self.used_methods:
            self.status_label.configure(text=f"⏹️ Gestoppt: {self.used_methods}")
        else:
            self.status_label.configure(text="⏹️ Gestoppt")

    def _set_controls_enabled(self, enabled: bool, processing: bool = False):
        """Aktiviert/deaktiviert Steuerelemente"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Setze Steuerelement-Status: enabled=%s, processing=%s', enabled, processing)
        if processing:
            # Während der Verarbeitung nur Process-Button deaktivieren
            self.process_btn.configure(state="disabled", text="⏳")
            self.play_pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
        else:
            state = "normal" if enabled else "disabled"
            self.play_pause_btn.configure(state=state)
            self.stop_btn.configure(state=state)
            self.process_btn.configure(state=state, text="🔄")

    def _start_progress_update(self):
        """Startet Fortschritts-Updates - robuste Version"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Starte Fortschritts-Updates')
        # **FIX: Vorherige Updates explizit stoppen**
        self.should_update = False
        # Kurz warten damit vorheriger Thread beendet wird
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=0.2)
        # **FIX: Frischen Thread starten**
        self.should_update = True
        self.update_thread = threading.Thread(target=self._update_progress_loop, daemon=True)
        self.update_thread.start()
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Progress-Update-Thread gestartet')

    def _update_progress_loop(self):
        """Update-Loop für Fortschritt - verbesserte Version"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Fortschritts-Update-Loop gestartet')
        while self.should_update:
            try:
                # **FIX: Prüfe ob Player noch existiert**
                if not hasattr(self, 'player') or not self.player:
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Player nicht mehr verfügbar - beende Update-Loop')
                    break
                status = self.player.get_status()
                # **FIX: UI-Update garantiert im Main Thread**
                self.after(0, self._update_progress_ui, status)
                # **FIX: Prüfe ob Wiedergabe natürlich beendet wurde**
                if not status["playing"] and hasattr(self, 'player') and self.player.is_playing:
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Wiedergabe natürlich beendet - triggere Stop')
                    self.after(0, self._stop)
                    break
                time.sleep(0.1)  # 100ms Updates
            except Exception as e:
                log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Fehler in Fortschritts-Update-Loop: %s', str(e))
                break
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Fortschritts-Update-Loop beendet')

    def _update_progress_ui(self, status: dict):
        """Aktualisiert UI mit Status - robuste Version"""
        herkunft = 'audio_preview.py'
        try:
            # **FIX: Nur aktualisieren wenn wir noch Updates wollen**
            if not self.should_update:
                return
            # **FIX: Prüfe ob Komponenten noch existieren**
            if not hasattr(self, 'progress') or not hasattr(self, 'time_label'):
                return
            # Fortschritt aktualisieren
            if status["duration"] > 0:
                progress = min(1.0, status["position"] / status["duration"])
                self.progress.set(progress)
            else:
                self.progress.set(0)
            # Zeit-Anzeige aktualisieren
            pos_str = self._format_time(status["position"])
            dur_str = self._format_time(status["duration"])
            self.time_label.configure(text=f"{pos_str}/{dur_str}")
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'UI-Update-Fehler ignoriert: %s', str(e))

    def _format_time(self, seconds: float) -> str:
        """Formatiert Zeit als mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def destroy(self):
        """Cleanup beim Zerstören - mit expliziter Player-Aufräumung"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'AudioPreviewWidget wird aufgeräumt')
        # Threading sauber beenden
        self.should_update = False
        # Player explizit aufräumen
        try:
            if hasattr(self, 'player') and self.player:
                self.player.cleanup()
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Player erfolgreich aufgeräumt')
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Player-Cleanup-Fehler ignoriert: %s', str(e))
        # Temporäre Dateien löschen
        temp_files = [self.temp_preview_file, self.processed_preview_file]
        deleted_count = 0
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    deleted_count += 1
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Temporäre Datei gelöscht: %s', os.path.basename(temp_file))
                except Exception as e:
                    log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Konnte temporäre Datei nicht löschen: %s', str(e))
        if deleted_count > 0:
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Temporäre Dateien aufgeräumt: %d Dateien', deleted_count)
        # Parent destroy aufrufen
        try:
            super().destroy()
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'AudioPreviewWidget erfolgreich zerstört')
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Parent-Destroy-Fehler: %s', str(e))

    def _debug_audio_info(self, file_path: str, description: str):
        """Debugging-Information für Audio-Dateien"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Debug-Info für %s', description)
        try:
            import soundfile as sf
            info = sf.info(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Datei: %s', os.path.basename(file_path))
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Sample-Rate: %d Hz', info.samplerate)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Kanäle: %d', info.channels)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Dauer: %.2f s', info.duration)
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Dateigröße: %.1f KB', file_size)
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Debug-Info fehlgeschlagen für %s: %s', description, str(e))

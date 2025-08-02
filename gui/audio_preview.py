"""Audio-Vorschau-Widget mit Verarbeitung und Play/Pause/Stop-Funktionalität"""

import customtkinter as ctk
import threading
import time
import os
import shutil
from typing import Optional
import tempfile
import numpy as np
import logging
import hashlib
import json

# NEU: Import für log_with_prefix (behebt 'not defined'-Fehler)
from utils.logger import log_with_prefix, get_normalized_logger
from utils.config import Config  # NEU: Import für Konfiguration
from utils.validators import is_supported_file  # NEU: Import für Dateityp-Prüfung
from audio.ffmpeg_utils import FFmpegUtils

# Logger konfigurieren
logger = get_normalized_logger('AudioPreview')

# Geändert: Nur pygame für Audio-Wiedergabe verwenden
PYGAME_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
    logger.info("Pygame erfolgreich geladen ✅")
except ImportError:
    logger.error("Pygame konnte nicht geladen werden ❌")

class AudioPreviewPlayer:
    """Vereinfachter Audio-Player mit korrektem Progress-Update"""

    def __init__(self):
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'AudioPreviewPlayer wird initialisiert (vereinfacht) ✅')

        # Geändert: Nur pygame als Player-Typ
        if PYGAME_AVAILABLE:
            self.player_type = 'pygame'
        else:
            self.player_type = None
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Keine Audio-Wiedergabe-Methode verfügbar ❌')

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
        # Geändert: Für pygame: Sound-Objekt
        self.pygame_sound = None
        self.is_unloaded = False

    def is_available(self) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Prüfe Audio-Wiedergabe-Verfügbarkeit')
        return self.player_type is not None

    def load(self, wav_path: str) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Datei wird geladen: %s ✅', os.path.basename(wav_path))
        if not self.is_available():
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Keine Audio-Wiedergabe-Methode verfügbar ❌')
            return False

        self.stop()
        self.current_file = wav_path
        try:
            import soundfile as sf
            info = sf.info(wav_path)
            self.duration = min(30, info.duration)
            # Geändert: Für pygame: Lade Sound zur Duration-Prüfung
            if self.player_type == 'pygame':
                self.pygame_sound = pygame.mixer.Sound(wav_path)
                self.duration = min(30, self.pygame_sound.get_length())
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Duration-Berechnung fehlgeschlagen ⚠️: %s', str(e))
            file_size = os.path.getsize(wav_path)
            self.duration = min(30, file_size / (22050 * 2))
        return True

    def play(self) -> bool:
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird gestartet ✅')
        if not self.current_file:
            return False

        with self._player_lock:
            if self.is_playing and not self.is_paused:
                return False

            # Resume von Pause oder neuer Start
            if self.is_paused:
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Resume von Pause ✅')
                self.is_paused = False
                if self.player_type == 'pygame':
                    pygame.mixer.music.unpause()
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
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Play-Worker Thread gestartet ✅')
                    if self.player_type == 'pygame':
                        pygame.mixer.music.load(self.current_file)
                        pygame.mixer.music.play()
                        elapsed = 0
                        while elapsed < self.duration and not self.should_stop.is_set():
                            time.sleep(0.1)
                            elapsed += 0.1

                    if not self.should_stop.is_set():
                        self.is_playing = False
                        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Wiedergabe natürlich beendet ✅')
                except Exception as e:
                    log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Wiedergabe fehlgeschlagen ❌: %s', str(e))
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
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird pausiert ✅')
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.pause_time = time.time()
            # Geändert: Bibliothek-spezifische Pause
            if self.player_type == 'pygame':
                pygame.mixer.music.pause()
            # Position zum Pause-Zeitpunkt speichern
            if self.start_time:
                self.position = self.pause_time - self.start_time
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Audio pausiert bei Position: %.2f s ✅', self.position)

    def stop(self):
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Audio-Wiedergabe wird gestoppt ✅')
        self.should_stop.set()
        
        # Geändert: Bibliothek-spezifischer Stop und explizite Freigabe
        if self.player_type == 'pygame':
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()  # Neu: Explizit die geladene Musik freigeben
                self.is_unloaded = True
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Pygame Musik erfolgreich freigegeben ✅')
                time.sleep(0.1)  # Neu: Kurze Verzögerung für Windows-Dateilocks
            except Exception as e:
                log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Pygame unload fehlgeschlagen ⚠️: %s', str(e))
                self.is_unloaded = False
        
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()  # Geändert: Voller join() ohne Timeout für sicheres Beenden
        
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.start_time = None
        self.pause_time = None
        self.pygame_sound = None  # Geändert: Freigabe

    def get_status(self) -> dict:
        """Korrigierte Status-Berechnung"""
        if self.is_playing and not self.is_paused and self.start_time:
            # Laufende Wiedergabe
            # Geändert: Verwende bibliothek-spezifische Position
            if self.player_type == 'pygame' and pygame.mixer.music.get_busy():
                self.position = min(self.duration, pygame.mixer.music.get_pos() / 1000.0)
            else:
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
        herkunft = 'audio_preview.py'
        self.stop()  # Bestehend: Ruft stop() auf, was nun unload() enthält
        
        # Geändert: Zusätzliche Prüfung und Logging für Freigabe
        if self.player_type == 'pygame' and not self.is_unloaded:
            try:
                pygame.mixer.music.unload()  # Neu: Fallback-Freigabe, falls stop() es verpasst hat
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Fallback: Pygame Musik freigegeben ✅')
                time.sleep(0.1)
            except Exception as e:
                log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Fallback-unload fehlgeschlagen ⚠️: %s', str(e))
        
        # Neu: Mixer sauber beenden (sichere Abschaltung)
        try:
            pygame.mixer.quit()
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Pygame Mixer erfolgreich beendet ✅')
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Pygame Mixer-Beendung fehlgeschlagen ⚠️: %s', str(e))


class AudioPreviewWidget(ctk.CTkFrame):
    """Audio-Vorschau-Widget mit Verarbeitung"""

    def __init__(self, parent, width=300):
        super().__init__(parent, width=width)
        self._width = width
        self.player = AudioPreviewPlayer()
        self.ffmpeg = FFmpegUtils()
        self.current_media = None
        self.temp_preview_file = None
        self.processed_preview_file = None
        self.temp_processed_files = []
        self.processed_previews = {}
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
            button_frame, text="▶️", width=50, height=35,  # Geändert: Höhe auf 35 für bessere vertikale Zentrierung
            command=self._toggle_play_pause,
            font=ctk.CTkFont(size=16),  # Bestehend: Größere Font
            anchor="center"  # Geändert: Explizite Zentrierung (horizontal/vertikal)
        )
        self.play_pause_btn.pack(side="left", padx=5)
        
        # Stop Button
        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏹️", width=50, height=35,  # Geändert: Höhe auf 35
            command=self._stop,
            font=ctk.CTkFont(size=15),
            anchor="center"  # Geändert: Zentrierung
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Process Button
        self.process_btn = ctk.CTkButton(
            button_frame, text="🔄", width=50, height=35,  # Geändert: Höhe auf 35
            command=self._process_preview,
            font=ctk.CTkFont(size=18),  # Geändert: Größere Font (vorher 12)
            anchor="center"  # Geändert: Zentrierung
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

    def load_media(self, media_path: str):
        """Lädt Medien für Audio-Vorschau"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Medien wird für Audio-Vorschau geladen: %s', os.path.basename(media_path))
        self.current_media = media_path
        self.info_label.configure(text=f"Lade: {os.path.basename(media_path)}")
        self.status_label.configure(text="")
        # Verarbeitete Datei zurücksetzen
        self.processed_preview_file = None
        self.used_methods = None
        if media_path in self.processed_previews:
            processed_file, used_method, saved_hash = self.processed_previews[media_path]
            if os.path.exists(processed_file):
                self.processed_preview_file = processed_file
                self.used_methods = used_method
                self.status_label.configure(text=f"✅ Verarbeitet mit {used_method}")  # Geändert: Immer setzen, unabhängig von Hash
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Bestehende verarbeitete Preview geladen: %s (Methode: %s)', os.path.basename(processed_file), used_method)
                # Lade direkt in Player
                if self.player.load(processed_file):
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitete Preview in Player geladen')
            else:
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Bestehende Preview nicht gefunden (gelöscht?) - setze zurück')
                del self.processed_previews[media_path]
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Vorherige verarbeitete Vorschau zurückgesetzt')
        # In separatem Thread laden
        threading.Thread(target=self._load_media_async,
                         args=(media_path,), daemon=True).start()

    def _load_media_async(self, media_path: str):
        """Lädt Medien asynchron (nur Extraktion, keine Verarbeitung)"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Asynchrone Medien-Ladung gestartet')
        try:
            is_valid, msg, media_type = is_supported_file(media_path)
            if not is_valid:
                raise Exception(msg)
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
            # Audio extrahieren/kopieren (30s Vorschau)
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, f'Extrahiere/Lade 30s Audio-Vorschau ({media_type})')
            if media_type == 'video':
                self.ffmpeg.extract_audio_preview(media_path, self.temp_preview_file)
            else:  # Audio
                # Für Audio: Direkt zu WAV konvertieren (Mono, 30s)
                self.ffmpeg.convert_to_wav(media_path, self.temp_preview_file, sample_rate=22050)
            self._debug_audio_info(self.temp_preview_file, "Original-Vorschau")
            # UI aktualisieren (im Main Thread)
            self.after(0, self._on_load_success)
        except Exception as e:
            log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Asynchrone Audio-Ladung fehlgeschlagen: %s', str(e))
            self.after(0, self._on_load_error, str(e))

    def _on_load_success(self):
        """Erfolgreich geladen"""
        herkunft = 'audio_preview.py'
        filename = os.path.basename(self.current_media) if self.current_media else "Unbekannt"
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Medien-Vorschau erfolgreich geladen: %s', filename)
        self.info_label.configure(text=f"Bereit: {filename}")
            
        # Geändert: Bedingter Status-Set basierend auf verarbeiteter Version
        if self.processed_preview_file and self.used_methods:
            self.status_label.configure(text=f"✅ Verarbeitet mit {self.used_methods}")
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Status auf verarbeitete Version gesetzt (Methode: %s)', self.used_methods)
        else:
            self.status_label.configure(text="Klicke 🔄 für Verarbeitung oder ▶️ für Original")
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Status auf Original gesetzt')
        
        self._set_controls_enabled(True)

    def _on_load_error(self, error_msg: str):
        """Fehler beim Laden"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Audio-Vorschau-Ladung fehlgeschlagen: %s', error_msg)
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
            from audio.processors import MediaProcessor
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
            self.temp_processed_files.append(self.processed_preview_file)
            # Mini-Processor erstellen
            processor = MediaProcessor()
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
                        try:
                            # SpeechBrain Voice Enhancement (AI)
                            from audio.speechbrain_voice_enhancer import SpeechBrainVoiceEnhancer
                            enhancer = SpeechBrainVoiceEnhancer()
                            if enhancer.is_available():
                                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende SpeechBrain Voice Enhancement')
                                voice_settings = config['voice_settings'].copy()
                                voice_settings['original_sample_rate'] = target_sample_rate
                                voice_settings['target_sample_rate'] = target_sample_rate
                                enhancer.process(wav_processed, wav_enhanced, voice_settings)
                                used_method += " + SpeechBrain"
                                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitung: ✅ Gelungen (Methode: SpeechBrain AI)')
                                if Config.get_debug_mode():
                                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitung: Details - Input: %s, Output: %s', wav_processed, wav_enhanced)
                            else:
                                log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Initialisierung: ❌ Nicht verfügbar - Fallback zu klassisch')
                                from audio.voice_enhancer import VoiceAudioEnhancer
                                enhancer = VoiceAudioEnhancer()
                                enhancer.process(wav_processed, wav_enhanced, config['voice_settings'])
                                used_method += " + Voice-Klassisch"
                                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, '🔄 Klassisches Voice Enhancement als Fallback angewendet')
                        except ImportError:
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
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitung: ✅ Abgeschlossen mit Methode %s', used_method)
                 # Geändert: Nach Erfolg, speichere in Dict und Liste
                config_hash = self._get_config_hash(config)
                if self.current_media in self.processed_previews:
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Überschreibe bestehende Verarbeitung für %s (neue Config)', os.path.basename(self.current_media))
                self.processed_previews[self.current_media] = (self.processed_preview_file, used_method, config_hash)
                self.temp_processed_files.append(self.processed_preview_file)  # Bestehend: Tracke für Löschung
                log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Verarbeitete Preview in Dict gespeichert (Hash: %s)', config_hash)
                if Config.get_debug_mode():
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
            
            shutil.copy2(input_path, output_path)

    def _prepare_final_preview(self, input_path: str, output_path: str, current_rate: int):
        """Bereitet finale Vorschau-Datei für optimale Wiedergabe vor"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Bereite finale Vorschau für Wiedergabe vor')
        try:
            # Für die Wiedergabe: Konvertiere zu einer Standard-Rate falls nötig
            # pygame funktioniert am besten mit Standard-Raten
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
                
                shutil.copy2(input_path, output_path)
                log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Wiedergabe-Rate bereits optimal: %d Hz', current_rate)
            # Debug-Info für finale Datei
            self._debug_audio_info(output_path, "Finale Vorschau für Wiedergabe")
        except Exception as e:
            log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Playback-Vorbereitung fehlgeschlagen: %s', str(e))
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verwende Fallback: Kopiere Eingabe-Datei')
            # Fallback: Original verwenden
            
            shutil.copy2(input_path, output_path)

    def _on_process_success(self, used_method: str):
        """Verarbeitung erfolgreich abgeschlossen"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Vorschau-Verarbeitung erfolgreich abgeschlossen: %s', used_method)
        self.is_processing = False
        self.used_methods = used_method
        self.status_label.configure(text=f"✅ Verarbeitet mit {used_method}")
        self._set_controls_enabled(True)
        
        # Geändert: Logging erweitern für Klarheit bei Neuverarbeiten
        if self.current_media in self.processed_previews:
            log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Updated verarbeitete Preview für %s mit neuer Methode: %s', os.path.basename(self.current_media), used_method)
        
        # Verarbeitete Datei in Player laden
        if self.player.load(self.processed_preview_file):
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Verarbeitete Vorschau in Player geladen')
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
                    self.status_label.configure(text=f"🎵 Spielt mit Verbesserung: {self.used_methods}")
                else:
                    self.status_label.configure(text="🎵 Spielt: Original")
            else:
                log_with_prefix(logger, 'error', 'PREVIEW', herkunft, 'Wiedergabe-Start fehlgeschlagen')

    def _stop(self):
        """Wiedergabe stoppen - mit korrigiertem Progress-Reset"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Stoppe Wiedergabe')
        # FIX: Progress-Updates explizit stoppen
        self.should_update = False
        # Player stoppen
        self.player.stop()
        # FIX: UI sofort zurücksetzen
        self.play_pause_btn.configure(text="▶️")
        self.progress.set(0)
        self.time_label.configure(text="00:00/00:00")
        # Zeige Methode wenn verarbeitete Version verfügbar
        if self.used_methods:
            self.status_label.configure(text=f"⏹️ Gestoppt mit Verbesserung: {self.used_methods}")
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
        # FIX: Vorherige Updates explizit stoppen
        self.should_update = False
        # Kurz warten damit vorheriger Thread beendet wird
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=0.2)
        # FIX: Frischen Thread starten
        self.should_update = True
        self.update_thread = threading.Thread(target=self._update_progress_loop, daemon=True)
        self.update_thread.start()
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Progress-Update-Thread gestartet')

    def _update_progress_loop(self):
        """Update-Loop für Fortschritt - verbesserte Version"""
        herkunft = 'audio_preview.py'
        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Fortschritts-Update-Loop gestartet')
        time.sleep(0.2)  # Kurze Pause vor dem Start
        while self.should_update:
            try:
                # FIX: Prüfe ob Player noch existiert
                if not hasattr(self, 'player') or not self.player:
                    log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Player nicht mehr verfügbar - beende Update-Loop')
                    break
                status = self.player.get_status()
                # FIX: UI-Update garantiert im Main Thread
                self.after(0, self._update_progress_ui, status)
                # FIX: Prüfe ob Wiedergabe natürlich beendet wurde
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
            # FIX: Nur aktualisieren wenn wir noch Updates wollen
            if not self.should_update:
                return
            # FIX: Prüfe ob Komponenten noch existieren
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
        all_processed = [data[0] for data in self.processed_previews.values() if data[0]]  # Alle processed_files
        temp_files = [self.temp_preview_file] + self.temp_processed_files + all_processed  # Kombiniere
        # Entferne Duplikate für Sicherheit
        temp_files = list(set(temp_files))
        deleted_count = 0
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                for attempt in range(3):  # Bestehend: Bis zu 3 Versuche
                    try:
                        os.remove(temp_file)
                        deleted_count += 1
                        log_with_prefix(logger, 'debug', 'PREVIEW', herkunft, 'Temporäre Datei gelöscht: %s (Versuch %d) ✅', os.path.basename(temp_file), attempt + 1)
                        break
                    except Exception as e:
                        log_with_prefix(logger, 'warning', 'PREVIEW', herkunft, 'Löschversuch %d fehlgeschlagen ⚠️: %s', attempt + 1, str(e))
                        time.sleep(0.2)  # Bestehend: Wartezeit
        if deleted_count > 0:
            log_with_prefix(logger, 'info', 'PREVIEW', herkunft, 'Temporäre Dateien aufgeräumt: %d Dateien ✅', deleted_count)
        
        # Neu: Dict leeren
        self.processed_previews = {}
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
            
    # Neu: Hilfsfunktion für Config-Hash (füge ans Ende der Klasse hinzu)
    def _get_config_hash(self, config: dict) -> str:
        """Berechnet reproduzierbaren Hash der Config für Vergleich"""
        config_str = json.dumps(config, sort_keys=True)  # Sortiert für Konsistenz
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()

"""Threading und Queue-Management für die Verarbeitung"""

import threading
import queue
from typing import Dict, Any, Optional, Callable
import os
import time
import logging

# NEU: Import für log_with_prefix (behebt 'not defined'-Fehler)
from utils.logger import log_with_prefix

from core.exceptions import ProcessingCancelledException
from audio.processors import VideoProcessor
from utils.config import Config, DEFAULT_MAX_FILE_SIZE_GB

# Logger konfigurieren
logger = logging.getLogger("AudioRestorer")

class ProcessingWorker:
    """Worker-Thread für die Video-Verarbeitung"""
    
    def __init__(self, result_callback: Callable[[str, str, str], None],
                 max_queue_size: int = 50, max_file_size_gb: float = DEFAULT_MAX_FILE_SIZE_GB):
        herkunft = 'workers.py'
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'ProcessingWorker wird initialisiert')
        self.result_callback = result_callback
        # NEU: Sichere Queue mit Größenlimit
        self.file_queue = queue.Queue(maxsize=max_queue_size)
        self.result_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_processing = False
        # NEU: Sicherheitslimits
        self.max_file_size = max_file_size_gb * 1024 * 1024 * 1024
        self.max_queue_size = max_queue_size
        self.active_workers = 0
        self.max_workers = 2  # CPU-Schutz
        # Statistiken
        self.processed_files = 0
        self.successful_files = 0
        self.cancelled_files = 0
        self.warnings = []
        self.errors = []
        self.video_processor = VideoProcessor()
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Sicherheitslimits: Max-Queue=%d, Max-Dateigröße=%.1f GB', max_queue_size, max_file_size_gb)

    def _validate_file_for_processing(self, file_path: str) -> None:
        """Validiert Datei vor der Verarbeitung - NEU"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Validiere Datei: %s', os.path.basename(file_path))
        # Dateigröße prüfen
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"Datei zu groß: {file_size / (1024**3):.1f} GB (Max: {self.max_file_size / (1024**3):.1f} GB)")
        except OSError:
            raise ValueError("Datei nicht zugänglich")
        # Dateityp-Validierung
        if not os.path.isfile(file_path):
            raise ValueError("Pfad ist keine gültige Datei")
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Datei validiert: %s', os.path.basename(file_path))

    def _can_add_job(self) -> tuple[bool, str]:
        """Prüft ob neuer Job hinzugefügt werden kann - NEU"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Prüfe Job-Kapazität')
        # Queue-Kapazität prüfen
        if self.file_queue.qsize() >= self.max_queue_size:
            return False, "Verarbeitungsqueue voll - bitte warten"
        # Worker-Limit prüfen
        if self.active_workers >= self.max_workers:
            return False, "Maximale Anzahl paralleler Verarbeitungen erreicht"
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Job kann hinzugefügt werden')
        return True, "OK"

    def start_processing(self, file_paths: Dict[str, str], processing_config: Dict[str, Any]) -> None:
        """
        Startet die Batch-Verarbeitung - SICHERHEIT VERBESSERT
        Args:
            file_paths: Dict[display_name, real_path]
            processing_config: Verarbeitungs-Konfiguration
        """
        herkunft = 'workers.py'
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Batch-Verarbeitung wird gestartet')
        if self.is_processing:
            raise RuntimeError("Verarbeitung läuft bereits")
        # NEU: Validiere alle Dateien vor Start
        validated_files = {}
        for display_name, real_path in file_paths.items():
            try:
                if hasattr(self, '_validate_file_for_processing'):
                    self._validate_file_for_processing(real_path)
                validated_files[display_name] = real_path
                log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Datei validiert: %s', display_name)
            except ValueError as e:
                log_with_prefix(logger, 'error', 'WORKERS', herkunft, 'Validierung fehlgeschlagen für %s: %s', display_name, str(e))
                raise RuntimeError(f"Datei {display_name}: {str(e)}")
        # NEU: Prüfe Kapazität
        can_add, error_msg = self._can_add_job()
        if not can_add:
            raise RuntimeError(f"Verarbeitung nicht möglich: {error_msg}")
        self._reset_statistics()
        self.stop_event.clear()
        self.is_processing = True
        # Dateien zur Queue hinzufügen
        jobs_added = 0
        for display_name, real_path in file_paths.items():
            job = ProcessingJob(
                file_path=real_path,
                display_name=display_name,
                config=processing_config
            )
            try:
                self.file_queue.put(job, block=False)
                jobs_added += 1
                log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Job hinzugefügt: %s', display_name)
            except queue.Full:
                log_with_prefix(logger, 'error', 'WORKERS', herkunft, 'Queue voll für: %s', display_name)
        # Worker-Thread starten
        self.active_workers += 1  # NEU: Worker-Zählung
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Worker gestartet für %d Dateien', len(file_paths))

    def cancel_processing(self) -> None:
        """Bricht die laufende Verarbeitung ab"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Verarbeitung wird abgebrochen')
        if not self.is_processing:
            return
        print("⏹️ Verarbeitung wird abgebrochen...")
        self.stop_event.set()
        # Noch nicht gestartete Jobs als abgebrochen markieren
        remaining_count = 0
        while not self.file_queue.empty():
            try:
                job = self.file_queue.get_nowait()
                self.result_queue.put(ProcessingResult(
                    status="cancelled",
                    file_path=job.file_path,
                    message="Verarbeitung vor Start abgebrochen"
                ))
                remaining_count += 1
            except queue.Empty:
                break
        if remaining_count > 0:
            log_with_prefix(logger, 'info', 'WORKERS', herkunft, '%d Jobs als abgebrochen markiert', remaining_count)

    def is_worker_finished(self) -> bool:
        """Prüft ob der Worker-Thread beendet ist"""
        return self.worker_thread is None or not self.worker_thread.is_alive()

    def get_results(self) -> list:
        """Holt alle verfügbaren Ergebnisse aus der Queue"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'get_results() aufgerufen. Queue-Size: %d', self.result_queue.qsize())
        results = []
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Ergebnis aus Queue: %s', result)
                results.append(result)
                self._update_statistics(result)
            except queue.Empty:
                log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Queue war beim get_results() leer')
                break
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'get_results() fertig. %d Ergebnisse verarbeitet. Stats: %s', len(results), self.get_statistics())
        # Fehler ausgeben
        for res in results:
            if hasattr(res, 'status') and res.status == "error":
                log_with_prefix(logger, 'error', 'WORKERS', herkunft, 'Fehler bei %s: %s', res.file_path, res.message)
        return results

    def get_statistics(self) -> Dict[str, int]:
        """Gibt aktuelle Verarbeitungsstatistiken zurück"""
        return {
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'cancelled_files': self.cancelled_files,
            'error_files': len(self.errors),
            'warning_count': len(self.warnings)
        }

    def _reset_statistics(self) -> None:
        """Setzt Statistiken zurück"""
        self.processed_files = 0
        self.successful_files = 0
        self.cancelled_files = 0
        self.warnings.clear()
        self.errors.clear()

    def _worker_loop(self) -> None:
        """Haupt-Worker-Schleife - SICHERHEIT VERBESSERT"""
        herkunft = 'workers.py'
        start_time = time.time()
        max_processing_time = 7200  # NEU: 2 Stunden Maximum
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Worker-Loop gestartet')
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Queue leer? %s', self.file_queue.empty())
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Stop-Event gesetzt? %s', self.stop_event.is_set())
        try:
            job_count = 0
            while not self.file_queue.empty() and not self.stop_event.is_set():
                log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Verarbeite Job #%d', job_count + 1)
                # NEU: Timeout-Prüfung
                if time.time() - start_time > max_processing_time:
                    log_with_prefix(logger, 'warning', 'WORKERS', herkunft, 'Worker-Timeout erreicht - beende Verarbeitung')
                    break
                try:
                    job = self.file_queue.get_nowait()
                    # Abbruch-Prüfung vor Verarbeitung
                    if self.stop_event.is_set():
                        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Stop-Event während Job-Verarbeitung')
                        self.result_queue.put(ProcessingResult(
                            status="cancelled",
                            file_path=job.file_path,
                            message="Verarbeitung abgebrochen"
                        ))
                        continue
                    # NEU: Job-Timeout pro Datei
                    job_start_time = time.time()
                    max_job_time = 1800  # 30 Minuten pro Job
                    # Job verarbeiten mit Timeout-Überwachung
                    self._process_job_with_timeout(job, max_job_time)
                    job_count += 1
                    log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Job abgeschlossen: %s', job.display_name)
                except queue.Empty:
                    log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Queue ist leer')
                    break
                except Exception as e:
                    log_with_prefix(logger, 'error', 'WORKERS', herkunft, 'Worker-Fehler: %s', str(e))
                    if 'job' in locals():
                        self.result_queue.put(ProcessingResult(
                            status="error",
                            file_path=job.file_path,
                            message=f"Worker-Fehler: {str(e)}"
                        ))
            log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Worker-Loop beendet. Jobs verarbeitet: %d', job_count)
            # Finale Queue-Leerung bei Abbruch
            if self.stop_event.is_set():
                self._clear_remaining_jobs()
        finally:
            # WICHTIG: Cleanup
            self.active_workers = max(0, self.active_workers - 1)  # NEU: Worker-Zählung
            self.is_processing = False
            log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Worker-Thread beendet. Verarbeitet: %d, Abgebrochen: %s', self.processed_files, self.stop_event.is_set())

    def _process_job_with_timeout(self, job: 'ProcessingJob', max_job_time: int) -> None:
        """Verarbeitet Job mit Timeout-Überwachung - NEU"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Starte Job mit Timeout: %d s', max_job_time)
        import threading
        import time
        result_container = {'result': None, 'exception': None}
        def job_runner():
            try:
                result_container['result'] = self._process_job(job)
            except Exception as e:
                result_container['exception'] = e
        # Job in separatem Thread mit Timeout starten
        job_thread = threading.Thread(target=job_runner, daemon=True)
        job_thread.start()
        job_thread.join(timeout=max_job_time)
        if job_thread.is_alive():
            log_with_prefix(logger, 'warning', 'WORKERS', herkunft, 'Job-Timeout für %s', os.path.basename(job.file_path))
            self.result_queue.put(ProcessingResult(
                status="error",
                file_path=job.file_path,
                message="Verarbeitung-Timeout erreicht"
            ))
        elif result_container['exception']:
            # Exception aufgetreten
            raise result_container['exception']
        # Sonst: Normaler Erfolg
        log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Job erfolgreich verarbeitet: %s', job.display_name)

    def _process_job(self, job: 'ProcessingJob') -> 'ProcessingResult':
        """Verarbeitet einen einzelnen Job und gibt das Ergebnis zurück"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, '_process_job() gestartet für %s', job.display_name)
        try:
            # Status-Update: Verarbeitung gestartet
            processing_result = ProcessingResult(
                status="processing",
                file_path=job.file_path,
                message=f"Starte {job.config['method']}"
            )
            self.result_queue.put(processing_result)
            log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'ProcessingResult (processing) in Queue: %s', processing_result)
            # DEBUG: Voice Enhancement Config prüfen
            voice_enhancement = job.config.get('voice_enhancement', False)
            voice_method = job.config.get('voice_method', 'classic')
            voice_settings = job.config.get('voice_settings', {})
            print(f"\n🔧 DEBUG - Workers.py (ERWEITERT):")
            print(f" Job Config Keys: {list(job.config.keys())}")
            print(f" Voice Enhancement: {voice_enhancement} (Type: {type(voice_enhancement)})")
            print(f" Voice Method: {voice_method}")
            print(f" Voice Settings: {voice_settings} (Type: {type(voice_settings)})")
            print(f" Voice Settings Keys: {list(voice_settings.keys()) if voice_settings else 'None'}")
            # WICHTIG: Explizite Typprüfung
            if isinstance(voice_enhancement, str):
                print(f" WARNUNG: voice_enhancement ist String '{voice_enhancement}' statt Boolean!")
                voice_enhancement = voice_enhancement.lower() in ['true', '1', 'yes', 'on']
                print(f" Korrigiert auf: {voice_enhancement}")
            print(f"🔧 DEBUG Ende\n")
            # Video verarbeiten - ERWEITERT mit Voice Enhancement
            used_method, output_path = self.video_processor.process_video(
                video_path=job.file_path,
                output_path=job.get_output_path(),
                noise_method=job.config['method'],
                method_params=job.config['method_params'],
                target_lufs=job.config['target_lufs'],
                voice_enhancement=voice_enhancement,  # ← NEU
                voice_settings=voice_settings,  # ← NEU
                voice_method=voice_method,  # ← NEU
                stop_event=self.stop_event
            )
            # Erfolg melden
            success_msg = f"{output_path} (Methode: {used_method}, LUFS: {job.config['target_lufs']})"
            result = ProcessingResult(
                status="done",
                file_path=job.file_path,
                message=success_msg
            )
            self.result_queue.put(result)
            log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Verarbeitung abgeschlossen: %s', result)
            return result
        except ProcessingCancelledException:
            result = ProcessingResult(
                status="cancelled",
                file_path=job.file_path,
                message="Verarbeitung abgebrochen"
            )
            self.result_queue.put(result)
            log_with_prefix(logger, 'info', 'WORKERS', herkunft, 'Verarbeitung abgebrochen: %s', result)
            return result
        except Exception as e:
            result = ProcessingResult(
                status="error",
                file_path=job.file_path,
                message=str(e)
            )
            self.result_queue.put(result)
            log_with_prefix(logger, 'error', 'WORKERS', herkunft, 'Fehler bei Verarbeitung: %s', result)
            return result

    def _clear_remaining_jobs(self) -> None:
        """Leert verbleibende Jobs bei Abbruch"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Leere verbleibende Jobs bei Abbruch')
        while not self.file_queue.empty():
            try:
                job = self.file_queue.get_nowait()
                self.result_queue.put(ProcessingResult(
                    status="cancelled",
                    file_path=job.file_path,
                    message="Verarbeitung abgebrochen"
                ))
            except queue.Empty:
                break

    def _update_statistics(self, result: 'ProcessingResult') -> None:
        """Aktualisiert Statistiken basierend auf Ergebnis"""
        herkunft = 'workers.py'
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Aktualisiere Statistik für %s', result)
        if result.status == "done":
            self.processed_files += 1
            self.successful_files += 1
        elif result.status == "cancelled":
            self.cancelled_files += 1
            self.processed_files += 1
        elif result.status == "error":
            self.processed_files += 1
            self.errors.append(f"{os.path.basename(result.file_path)}: {result.message}")
        elif result.status == "warning":
            self.warnings.append(f"{os.path.basename(result.file_path)}: {result.message}")
        log_with_prefix(logger, 'debug', 'WORKERS', herkunft, 'Aktuelle Statistik: processed=%d, success=%d, cancelled=%d, errors=%d, warnings=%d', self.processed_files, self.successful_files, self.cancelled_files, len(self.errors), len(self.warnings))

class ProcessingJob:
    """Einzelner Verarbeitungsjob"""
    
    def __init__(self, file_path: str, display_name: str, config: Dict[str, Any]):
        self.file_path = file_path
        self.display_name = display_name
        self.config = config
    
    def get_output_path(self) -> str:
        """Generiert den Ausgabepfad"""
        from core.file_manager import FileManager
        file_manager = FileManager()
        return file_manager.generate_output_path(
            input_path=self.file_path,
            filename_mode=self.config['filename_mode'],
            custom_suffix=self.config['custom_suffix'],
            output_dir=self.config.get('output_dir')
        )

class ProcessingResult:
    """Verarbeitungsergebnis"""
    
    def __init__(self, status: str, file_path: str, message: str):
        self.status = status  # "processing", "done", "cancelled", "error", "warning"
        self.file_path = file_path
        self.message = message
    
    def __repr__(self) -> str:
        return f"ProcessingResult(status={self.status}, file={os.path.basename(self.file_path)})"

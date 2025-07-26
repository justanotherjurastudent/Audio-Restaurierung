"""Threading und Queue-Management für die Verarbeitung"""

import threading
import queue
from typing import Dict, Any, Optional, Callable
import os

from .exceptions import ProcessingCancelledException
from audio.processors import VideoProcessor

class ProcessingWorker:
    """Worker-Thread für die Video-Verarbeitung"""
    
    def __init__(self, result_callback: Callable[[str, str, str], None]):
        self.result_callback = result_callback
        self.file_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_processing = False
        
        # Statistiken
        self.processed_files = 0
        self.successful_files = 0
        self.cancelled_files = 0
        self.warnings = []
        self.errors = []
        
        self.video_processor = VideoProcessor()
    
    def start_processing(self, file_paths: Dict[str, str], processing_config: Dict[str, Any]) -> None:
        """
        Startet die Batch-Verarbeitung
        
        Args:
            file_paths: Dict[display_name, real_path]
            processing_config: Verarbeitungs-Konfiguration
        """
        if self.is_processing:
            raise RuntimeError("Verarbeitung läuft bereits")
        
        self._reset_statistics()
        self.stop_event.clear()
        self.is_processing = True
        
        # Dateien zur Queue hinzufügen
        for display_name, real_path in file_paths.items():
            job = ProcessingJob(
                file_path=real_path,
                display_name=display_name,
                config=processing_config
            )
            self.file_queue.put(job)
        
        # Worker-Thread starten
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        print(f"🚀 Worker gestartet für {len(file_paths)} Dateien")
    
    def cancel_processing(self) -> None:
        """Bricht die laufende Verarbeitung ab"""
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
            print(f"⏹️ {remaining_count} Jobs als abgebrochen markiert")
    
    def is_worker_finished(self) -> bool:
        """Prüft ob der Worker-Thread beendet ist"""
        return self.worker_thread is None or not self.worker_thread.is_alive()
    
    def get_results(self) -> list:
        """Holt alle verfügbaren Ergebnisse aus der Queue"""
        results = []
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
                self._update_statistics(result)
            except queue.Empty:
                break
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
        """Haupt-Worker-Schleife"""
        try:
            while not self.file_queue.empty() and not self.stop_event.is_set():
                try:
                    job = self.file_queue.get_nowait()
                    
                    # Abbruch-Prüfung vor Verarbeitung
                    if self.stop_event.is_set():
                        self.result_queue.put(ProcessingResult(
                            status="cancelled",
                            file_path=job.file_path,
                            message="Verarbeitung abgebrochen"
                        ))
                        continue
                    
                    # Job verarbeiten
                    self._process_job(job)
                    
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"❌ Worker-Fehler: {e}")
            
            # Finale Queue-Leerung bei Abbruch
            if self.stop_event.is_set():
                self._clear_remaining_jobs()
        
        finally:
            # WICHTIG: is_processing explizit auf False setzen
            self.is_processing = False
            print(f"🔚 Worker-Thread beendet. Verarbeitet: {self.processed_files}, Abgebrochen: {self.stop_event.is_set()}")

    
    def _process_job(self, job: 'ProcessingJob') -> None:
        """Verarbeitet einen einzelnen Job"""
        try:
            # Status-Update: Verarbeitung gestartet
            self.result_queue.put(ProcessingResult(
                status="processing",
                file_path=job.file_path,
                message=f"Starte {job.config['method']}"
            ))
            
            # Video verarbeiten
            used_method, output_path = self.video_processor.process_video(
                video_path=job.file_path,
                output_path=job.get_output_path(),
                noise_method=job.config['method'],
                method_params=job.config['method_params'],
                target_lufs=job.config['target_lufs'],
                stop_event=self.stop_event
            )
            
            # Erfolg melden
            success_msg = f"{output_path} (Methode: {used_method}, LUFS: {job.config['target_lufs']})"
            self.result_queue.put(ProcessingResult(
                status="done",
                file_path=job.file_path,
                message=success_msg
            ))
            
        except ProcessingCancelledException:
            self.result_queue.put(ProcessingResult(
                status="cancelled",
                file_path=job.file_path,
                message="Verarbeitung abgebrochen"
            ))
        except Exception as e:
            self.result_queue.put(ProcessingResult(
                status="error",
                file_path=job.file_path,
                message=str(e)
            ))
    
    def _clear_remaining_jobs(self) -> None:
        """Leert verbleibende Jobs bei Abbruch"""
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

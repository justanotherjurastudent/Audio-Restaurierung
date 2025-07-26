"""Audacity-kompatible Rauschreduzierung"""

from typing import Dict, Any
import os

import numpy as np
import soundfile as sf
from scipy import signal

from .base import AudioProcessor  # ← GEÄNDERT: Import von base.py
from core.exceptions import AudacityError

class AudacityProcessor(AudioProcessor):
    """Audacity-kompatible spektrale Rauschreduzierung"""
    
    def __init__(self):
        super().__init__("Audacity Spectral")
    
    def is_available(self) -> bool:
        """Audacity-Prozessor ist immer verfügbar (nutzt nur scipy/numpy)"""
        try:
            import numpy
            import soundfile
            from scipy import signal
            return True
        except ImportError:
            return False
    
    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """
        Verarbeitet Audio mit Audacity-Algorithmus
        
        Args:
            input_wav: Eingabe-WAV-Datei
            output_wav: Ausgabe-WAV-Datei
            params: Parameter-Dict
        """
        if not os.path.exists(input_wav):
            raise AudacityError(f"Eingabe-Datei existiert nicht: {input_wav}")
        
        try:
            # Audio laden
            data, sample_rate = sf.read(input_wav)
            
            if len(data) == 0:
                raise AudacityError("Audio-Datei ist leer")
            
            # Stereo zu Mono falls nötig
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            
            # Mindestlänge prüfen
            if len(data) < sample_rate * 0.5:
                raise AudacityError("Audio zu kurz für Audacity-Methode (min. 0.5s)")
            
            # Parameter extrahieren und validieren
            validated_params = self._validate_params(params)
            
            print(f"🎛️ Audacity: Rauschreduzierung {validated_params['noise_gain_db']:.1f}dB, "
                  f"Empfindlichkeit {validated_params['sensitivity']:.1f}")
            
            # Rauschreduzierung anwenden
            noise_reducer = AudacityNoiseReduction(**validated_params)
            
            # Rauschprofil aus den ersten Sekunden erstellen
            profile_duration = min(1.0, len(data) / sample_rate * 0.3)
            noise_reducer.create_noise_profile(data, sample_rate, profile_duration)
            
            # Rauschreduzierung durchführen
            cleaned_audio = noise_reducer.reduce_noise(data, sample_rate)
            
            # Clipping verhindern
            max_val = np.max(np.abs(cleaned_audio))
            if max_val > 0.95:
                cleaned_audio = cleaned_audio * (0.95 / max_val)
                print("🎛️ Audio-Pegel reduziert um Clipping zu verhindern")
            
            # Ergebnis speichern
            sf.write(output_wav, cleaned_audio, sample_rate, subtype="PCM_16")
            
            if not os.path.exists(output_wav):
                raise AudacityError("Ausgabe-Datei wurde nicht erstellt")
            
            print("✅ Audacity: Verarbeitung abgeschlossen")
            
        except Exception as e:
            error_msg = f"Audacity-Verarbeitung fehlgeschlagen: {str(e)}"
            print(f"❌ {error_msg}")
            raise AudacityError(error_msg)
    
    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validiert und korrigiert Parameter"""
        validated = {
            'window_size': params.get('window_size', 2048),
            'overlap_factor': 4,
            'noise_gain_db': max(6.0, min(30.0, params.get('rauschunterdrückung', 12.0))),
            'sensitivity': max(0.0, min(20.0, params.get('empfindlichkeit', 6.0))),
            'smoothing_time_ms': params.get('zeitglättung', 20),
            'freq_smoothing_bands': max(0, min(10, params.get('frequenzglättung', 0)))
        }
        
        # Window size validieren (muss Potenz von 2 sein)
        window_sizes = [1024, 2048, 4096, 8192]
        if validated['window_size'] not in window_sizes:
            validated['window_size'] = 2048
        
        return validated
    
    def get_default_params(self) -> Dict[str, Any]:
        """Gibt Standard-Parameter zurück"""
        return {
            'window_size': 2048,
            'rauschunterdrückung': 12.0,
            'empfindlichkeit': 6.0,
            'zeitglättung': 20,
            'frequenzglättung': 0
        }
    
    def get_param_ranges(self) -> Dict[str, tuple]:
        """Gibt Parameterbereiche zurück"""
        return {
            'rauschunterdrückung': (6.0, 30.0),
            'empfindlichkeit': (0.0, 20.0),
            'zeitglättung': (0, 100),
            'frequenzglättung': (0, 10)
        }

class AudacityNoiseReduction:
    """Implementierung des Audacity Rauschreduzierungs-Algorithmus"""
    
    def __init__(self, window_size: int = 2048, overlap_factor: int = 4,
                 noise_gain_db: float = 12.0, sensitivity: float = 6.0,
                 smoothing_time_ms: int = 20, freq_smoothing_bands: int = 0):
        
        self.window_size = window_size
        self.hop_size = window_size // overlap_factor
        self.noise_gain_db = noise_gain_db
        self.sensitivity = sensitivity
        self.smoothing_time_ms = smoothing_time_ms
        self.freq_smoothing_bands = freq_smoothing_bands
        
        self.noise_profile_means = None
        self.sample_rate = None
        self.window = np.hanning(window_size)
    
    def create_noise_profile(self, audio_data: np.ndarray, sample_rate: int, 
                           profile_duration: float = 0.5) -> np.ndarray:
        """Erstellt Rauschprofil aus den ersten Sekunden"""
        self.sample_rate = sample_rate
        
        profile_samples = int(profile_duration * sample_rate)
        noise_data = audio_data[:min(profile_samples, len(audio_data))]
        
        if len(noise_data) < self.window_size:
            raise ValueError(f"Audio zu kurz. Mindestens {self.window_size/sample_rate:.2f}s benötigt.")
        
        # STFT des Rauschsegments
        f, t, noise_stft = signal.stft(
            noise_data,
            fs=sample_rate,
            window=self.window,
            nperseg=self.window_size,
            noverlap=self.window_size - self.hop_size,
            return_onesided=True
        )
        
        # Leistungsspektrum und Mittelwert über Zeit
        noise_power = np.abs(noise_stft) ** 2
        self.noise_profile_means = np.mean(noise_power, axis=1)
        
        return self.noise_profile_means
    
    def reduce_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Führt Rauschreduzierung durch"""
        if self.noise_profile_means is None:
            raise ValueError("Rauschprofil muss zuerst erstellt werden!")
        
        if sample_rate != self.sample_rate:
            raise ValueError("Sample-Rate muss mit Rauschprofil übereinstimmen!")
        
        # STFT des gesamten Audios
        f, t, audio_stft = signal.stft(
            audio_data,
            fs=sample_rate,
            window=self.window,
            nperseg=self.window_size,
            noverlap=self.window_size - self.hop_size,
            return_onesided=True
        )
        
        # Spektrale Verstärkungsberechnung
        audio_power = np.abs(audio_stft) ** 2
        gains = self._calculate_spectral_gains(audio_power)
        
        # Optionale Frequenz-Glättung
        if self.freq_smoothing_bands > 0:
            gains = self._apply_frequency_smoothing(gains)
        
        # Zeitliche Glättung
        gains = self._apply_time_smoothing(gains, sample_rate)
        
        # Verstärkung anwenden
        cleaned_stft = audio_stft * gains
        
        # Zurück in Zeitbereich
        _, cleaned_audio = signal.istft(
            cleaned_stft,
            fs=sample_rate,
            window=self.window,
            nperseg=self.window_size,
            noverlap=self.window_size - self.hop_size
        )
        
        return cleaned_audio
    
    def _calculate_spectral_gains(self, audio_power: np.ndarray) -> np.ndarray:
        """Berechnet spektrale Verstärkungsfaktoren"""
        n_freq, n_time = audio_power.shape
        gains = np.ones((n_freq, n_time))
        
        # Rausch-Dämpfungsfaktor
        noise_atten_factor = 10 ** (-self.noise_gain_db / 20.0)
        
        # Empfindlichkeits-Schwellwerte
        sensitivity_linear = 10 ** (self.sensitivity / 10.0)
        thresholds = sensitivity_linear * self.noise_profile_means[:, np.newaxis]
        
        # Maske für Rauschbereiche
        noise_mask = audio_power <= thresholds
        
        # Verstärkung anwenden
        gains[noise_mask] = noise_atten_factor
        gains[~noise_mask] = 1.0
        
        return gains
    
    def _apply_frequency_smoothing(self, gains: np.ndarray) -> np.ndarray:
        """Glättet Verstärkungen über Frequenzbänder"""
        if self.freq_smoothing_bands <= 0:
            return gains
        
        smoothed_gains = np.copy(gains)
        n_freq, n_time = gains.shape
        
        for t in range(n_time):
            for f in range(n_freq):
                f_start = max(0, f - self.freq_smoothing_bands)
                f_end = min(n_freq, f + self.freq_smoothing_bands + 1)
                
                # Logarithmische Mittelung
                log_gains = np.log(gains[f_start:f_end, t])
                smoothed_gains[f, t] = np.exp(np.mean(log_gains))
        
        return smoothed_gains
    
    def _apply_time_smoothing(self, gains: np.ndarray, sample_rate: int) -> np.ndarray:
        """Zeitliche Glättung für natürlicheren Klang"""
        if self.smoothing_time_ms <= 0:
            return gains
        
        time_constant = self.smoothing_time_ms / 1000.0
        hop_time = self.hop_size / sample_rate
        alpha = 1.0 - np.exp(-hop_time / time_constant)
        
        smoothed_gains = np.copy(gains)
        n_freq, n_time = gains.shape
        
        # Über Zeit glätten (Attack/Release-Verhalten)
        for t in range(1, n_time):
            for f in range(n_freq):
                current = gains[f, t]
                previous = smoothed_gains[f, t-1]
                
                if current < previous:  # Attack (sofortige Dämpfung)
                    smoothed_gains[f, t] = current
                else:  # Release (langsame Erholung)
                    smoothed_gains[f, t] = previous + alpha * (current - previous)
        
        return smoothed_gains

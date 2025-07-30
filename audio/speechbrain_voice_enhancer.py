"""SpeechBrain Voice Enhancement für EXE - WaveformEnhancement"""

import os
import sys
import tempfile
import time
import base64
from typing import Dict, Any
import torch
import torchaudio
import logging
from utils.logger import log_with_prefix, get_normalized_logger
from utils.config import Config

# **KRITISCHER PYTORCH-KOMPATIBILITÄTS-FIX**
def patch_pytorch_for_speechbrain():
    """Patcht PyTorch für SpeechBrain-Kompatibilität"""
    logger = get_normalized_logger(__name__)
    try:
        # Fix für Conv1d padding-Probleme
        original_conv1d_forward = torch.nn.Conv1d.forward
        def patched_conv1d_forward(self, input):
            # Entferne problematische padding_mode Parameter
            if hasattr(self, 'padding_mode') and self.padding_mode != 'zeros':
                logger.debug("Patche Conv1d padding_mode: %s → zeros", self.padding_mode)
                original_padding_mode = self.padding_mode
                self.padding_mode = 'zeros'
                try:
                    result = original_conv1d_forward(self, input)
                    return result
                finally:
                    self.padding_mode = original_padding_mode
            else:
                return original_conv1d_forward(self, input)
        # Monkey-Patch anwenden
        torch.nn.Conv1d.forward = patched_conv1d_forward
        logger.info("PyTorch Conv1d Kompatibilitäts-Patch erfolgreich angewendet")
    except Exception as e:
        logger.warning("PyTorch-Kompatibilitäts-Patch fehlgeschlagen: %s", str(e))

# Patch beim Import anwenden
patch_pytorch_for_speechbrain()

from .base import AudioProcessor
from core.exceptions import AudioProcessingError

# Logger konfigurieren
logger = get_normalized_logger('speechbrain')

EMBEDDED_HYPERPARAMS_YAML = """
# STFT arguments
sample_rate: 16000
n_fft: 512
win_length: 32
hop_length: 16
mask_weight: 0.99
# Enhancement model args
enhance_model: !new:speechbrain.lobes.models.EnhanceResnet.EnhanceResnet
  n_fft: !ref <n_fft>
  win_length: !ref <win_length>
  hop_length: !ref <hop_length>
  sample_rate: !ref <sample_rate>
  channel_counts: [128, 128, 256, 256, 512, 512]
  normalization: !name:speechbrain.nnet.normalization.BatchNorm2d
  activation: !new:torch.nn.GELU
  dense_count: 2
  dense_nodes: 1024
  dropout: 0.1
  mask_weight: !ref <mask_weight>
modules:
  enhance_model: !ref <enhance_model>
pretrainer: !new:speechbrain.utils.parameter_transfer.Pretrainer
  loadables:
    enhance_model: !ref <enhance_model>
"""

class SpeechBrainVoiceEnhancer(AudioProcessor):
    """SpeechBrain Voice Enhancer mit PyTorch-Kompatibilität"""
    def __init__(self):
        super().__init__("SpeechBrain Voice Enhancer")
        log_with_prefix(logger, 'info', 'SPEECHBRAIN', 'speechbrain_voice_enhancer.py', 'SpeechBrain Voice Enhancer wird initialisiert (PyTorch-kompatibel)')
        # CPU-only für EXE-Kompatibilität
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        self.device = "cpu"
        self._model = None
        self._temp_model_dir = None

    def is_available(self) -> bool:
        """Prüft SpeechBrain-Verfügbarkeit"""
        try:
            import speechbrain
            # Test-Import für kritische Module
            from speechbrain.inference.enhancement import WaveformEnhancement
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', 'speechbrain_voice_enhancer.py', 'SpeechBrain-Verfügbarkeitsprüfung: ✅ Verfügbar')
            return True
        except ImportError:
            log_with_prefix(logger, 'warning', 'SPEECHBRAIN', 'speechbrain_voice_enhancer.py', 'SpeechBrain-Verfügbarkeitsprüfung: ❌ Import fehlgeschlagen')
            return False
        except Exception as e:
            log_with_prefix(logger, 'warning', 'SPEECHBRAIN', 'speechbrain_voice_enhancer.py', 'SpeechBrain-Verfügbarkeitsprüfung fehlgeschlagen: {str(e)}')
            return False

    def _load_model(self):
        """Lädt SpeechBrain-Modell mit PyTorch-Kompatibilität"""
        herkunft = 'speechbrain_voice_enhancer.py'
        if self._model is not None:
            log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Modell bereits geladen, verwende Cache')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Initialisierung: Details - Modell gecacht')
            return self._model

        try:
            from speechbrain.inference.enhancement import WaveformEnhancement
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📋 Lade SpeechBrain-Modell (PyTorch-kompatibel)')

            # Base64-Modell importieren
            try:
                from speechbrain_model_base64 import ENHANCE_MODEL
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📦 Base64-Modell-Daten erfolgreich importiert')
            except ImportError as e:
                raise AudioProcessingError(f"speechbrain_model_base64.py nicht gefunden: {str(e)}")

            # Temporäres Verzeichnis
            temp_base = tempfile.gettempdir()
            session_id = str(int(time.time()))[-6:]
            temp_model_dir = os.path.join(temp_base, f"sb_compat_{session_id}")
            os.makedirs(temp_model_dir, exist_ok=True)
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📁 Temporäres Modell-Verzeichnis erstellt: {os.path.basename(temp_model_dir)}')

            # Base64-Dekodierung
            try:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔓 Dekodiere Base64-Modell...')
                base64_content = ENHANCE_MODEL.strip()
                model_data = base64.b64decode(base64_content)
                model_path = os.path.join(temp_model_dir, "enhance_model.ckpt")
                with open(model_path, "wb") as f:
                    f.write(model_data)
                os.chmod(model_path, 0o666)
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Base64-Modell dekodiert und gespeichert: %.1f MB', len(model_data) / (1024*1024))
            except Exception as e:
                raise AudioProcessingError(f"Base64-Dekodierung fehlgeschlagen: {str(e)}")

            # YAML-Konfiguration
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📋 Erstelle YAML-Konfiguration...')
            yaml_path = os.path.join(temp_model_dir, 'hyperparams.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(EMBEDDED_HYPERPARAMS_YAML)
            os.chmod(yaml_path, 0o666)
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ YAML-Konfiguration erstellt')

            # Modell laden
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔄 Lade SpeechBrain WaveformEnhancement...')
            os.environ['SPEECHBRAIN_CACHE_DIR'] = temp_model_dir
            os.environ['TORCH_USE_RTLD_GLOBAL'] = 'YES'
            self._model = WaveformEnhancement.from_hparams(
                source=temp_model_dir,
                hparams_file=yaml_path,
                savedir=temp_model_dir,
                run_opts={
                    "device": self.device,
                    "precision": "fp32",
                    "use_amp": False
                }
            )
            self._temp_model_dir = temp_model_dir
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'Initialisierung: ✅ Modell erfolgreich initialisiert (Gerät: {self.device}, Precision: fp32)')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Initialisierung: Details - Temp-Dir: {temp_model_dir}')
            return self._model

        except Exception as e:
            log_with_prefix(logger, 'error', 'SPEECHBRAIN', herkunft, 'Initialisierung: ❌ Fehlgeschlagen: {str(e)}')
            raise AudioProcessingError(f"SpeechBrain-Modell laden fehlgeschlagen: {str(e)}")

    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Voice Enhancement mit PyTorch-Kompatibilität"""
        herkunft = 'speechbrain_voice_enhancer.py'
        log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'Verarbeitung gestartet mit Stärke=%.2f, Normalisierung=%s', params.get('enhancement_strength', 1.0), params.get('normalize_audio', True))
        try:
            # Modell laden
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📋 Lade SpeechBrain-Modell...')
            model = self._load_model()
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ SpeechBrain-Modell erfolgreich geladen')

            # Parameter extrahieren und anzeigen
            enhance_strength = params.get('enhancement_strength', 1.0)
            normalize_audio = params.get('normalize_audio', True)
            target_sample_rate = params.get('target_sample_rate', None)
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔧 Enhancement-Parameter: Stärke=%.2f, Normalisierung={normalize_audio}')

            # Audio laden
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📁 Lade Audio-Datei für SpeechBrain...')
            waveform, sr = torchaudio.load(input_wav)
            original_sr = sr
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎵 Audio geladen: {sr} Hz, Form={waveform.shape}')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Audio geladen: {sr} Hz, Form={waveform.shape}')

            # Tensor-Format normalisieren
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔄 Normalisiere Audio-Format für SpeechBrain...')
            if waveform.dim() > 2:
                waveform = waveform.squeeze()
            if waveform.dim() == 2:
                if waveform.shape[0] > 1:
                    # Multi-channel → Mono
                    waveform = torch.mean(waveform, dim=0, keepdim=True)
                    log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔊 Multi-Channel zu Mono konvertiert')
            elif waveform.dim() == 1:
                # Add channel dimension
                waveform = waveform.unsqueeze(0)
            # Ensure waveform is [1, samples]
            if waveform.shape[0] != 1:
                waveform = waveform.unsqueeze(0)
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Audio-Format normalisiert: {waveform.shape}')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Normalisierte Form: {waveform.shape}')

            # Resampling zu 16kHz
            if sr != 16000:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🔄 Resampling: {sr} Hz → 16000 Hz für SpeechBrain')
                resampler = torchaudio.transforms.Resample(sr, 16000)
                waveform = resampler(waveform)
                sr = 16000
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Resampling abgeschlossen')
            else:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'ℹ️ Audio bereits bei 16000 Hz - kein Resampling nötig')

            # SpeechBrain Enhancement
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🚀 Starte SpeechBrain AI Enhancement...')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Starte kompatibles SpeechBrain Enhancement')
            with torch.no_grad():
                # Input-Format vorbereiten
                if waveform.dim() == 2 and waveform.shape[0] == 1:
                    input_tensor = waveform  # Already [1, samples]
                else:
                    input_tensor = waveform.unsqueeze(0)  # Add batch dimension
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎯 Enhancement Input vorbereitet: {input_tensor.shape}')
                if Config.get_debug_mode():
                    log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Enhancement Input: {input_tensor.shape}')

                # Enhancement durchführen
                try:
                    log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '⚡ Führe AI-Enhancement durch...')
                    enhanced = model.enhance_batch(
                        input_tensor,
                        lengths=torch.tensor([1.0], device=self.device)
                    )
                    # Output normalisieren
                    if enhanced.dim() > 2:
                        enhanced = enhanced.squeeze(0)  # Remove batch
                    if enhanced.dim() == 1:
                        enhanced = enhanced.unsqueeze(0)  # Ensure [1, samples]
                    log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎉 AI-Enhancement erfolgreich abgeschlossen')
                except RuntimeError as padding_error:
                    if "padding" in str(padding_error).lower():
                        log_with_prefix(logger, 'error', 'SPEECHBRAIN', herkunft, f'❌ Padding-Fehler erkannt: {str(padding_error)}')
                        raise AudioProcessingError(f"PyTorch-Padding-Kompatibilitätsproblem: {str(padding_error)}")
                    else:
                        raise
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ SpeechBrain-Verarbeitung abgeschlossen: {enhanced.shape}')
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, 'Enhancement abgeschlossen: {enhanced.shape}')

            # Post-Processing
            if enhance_strength != 1.0:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎛️ Wende Enhancement-Stärke an: %.2', enhance_strength)
                enhanced = (enhance_strength * enhanced + (1.0 - enhance_strength) * waveform)
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Enhancement-Stärke angewendet')

            # Normalisierung
            if normalize_audio:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '📊 Normalisiere Audio-Lautstärke...')
                max_val = torch.max(torch.abs(enhanced))
                if max_val > 0:
                    enhanced = enhanced / max_val * 0.95
                    log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Audio normalisiert (Peak: %.3f)', max_val.item())
                else:
                    log_with_prefix(logger, 'warning', 'SPEECHBRAIN', herkunft, '⚠️ Audio ist stumm - keine Normalisierung möglich')

            # Sample-Rate zurück konvertieren
            final_sr = target_sample_rate if target_sample_rate else original_sr
            if final_sr != sr:
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, f'🔄 Sample-Rate-Rückkonvertierung: {sr} Hz → {final_sr} Hz')
                resampler = torchaudio.transforms.Resample(sr, final_sr)
                enhanced = resampler(enhanced)
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '✅ Sample-Rate-Konvertierung abgeschlossen')

            # Speichern
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '💾 Speichere verbessertes Audio...')
            torchaudio.save(output_wav, enhanced, final_sr)
            # Erfolgreiche Fertigstellung
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, '🎉 SpeechBrain Enhancement erfolgreich abgeschlossen!')
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, f'📁 Ausgabedatei: {os.path.basename(output_wav)}')
            log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, f'Verarbeitung: ✅ Erfolgreich abgeschlossen (Form: {enhanced.shape})')  # NEU: INFO für Erfolg und Herkunft
            if Config.get_debug_mode():
                log_with_prefix(logger, 'debug', 'SPEECHBRAIN', herkunft, f'Verarbeitung: Details - Sample-Rate: {final_sr} Hz')

        except Exception as e:
            log_with_prefix(logger, 'error', 'SPEECHBRAIN', herkunft, f'❌ SpeechBrain Enhancement fehlgeschlagen: {str(e)}')
            log_with_prefix(logger, 'error', 'SPEECHBRAIN', herkunft, f'Verarbeitung: ❌ Fehlgeschlagen: {str(e)}')
            raise AudioProcessingError(f"SpeechBrain Enhancement fehlgeschlagen: {str(e)}")

    def cleanup(self):
        """Cleanup mit Temp-Verzeichnis-Aufräumung"""
        herkunft = 'speechbrain_voice_enhancer.py'
        log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'SpeechBrain Enhancer Cleanup')
        if self._temp_model_dir and os.path.exists(self._temp_model_dir):
            try:
                import shutil
                shutil.rmtree(self._temp_model_dir)
                log_with_prefix(logger, 'info', 'SPEECHBRAIN', herkunft, 'Temp-Verzeichnis aufgeräumt')
            except Exception as e:
                log_with_prefix(logger, 'warning', 'SPEECHBRAIN', herkunft, 'Cleanup-Fehler: {str(e)}')
        self._temp_model_dir = None
        self._model = None

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass

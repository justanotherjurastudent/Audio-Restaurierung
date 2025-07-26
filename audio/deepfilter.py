"""DeepFilterNet3 KI-Rauschreduzierung"""

from typing import Dict, Any
import os

from .base import AudioProcessor  # ← GEÄNDERT: Import von base.py
from core.exceptions import DeepFilterNetError

# Global verfügbar prüfen
try:
    from df.enhance import enhance, init_df, load_audio, save_audio
    from df.model import ModelParams
    DEEPFILTERNET_AVAILABLE = True
    print("✅ DeepFilterNet3 verfügbar")
except ImportError:
    DEEPFILTERNET_AVAILABLE = False
    print("❌ DeepFilterNet3 nicht verfügbar")

class DeepFilterProcessor(AudioProcessor):
    """DeepFilterNet3 KI-Rauschreduzierung"""
    
    def __init__(self):
        super().__init__("DeepFilterNet3")
        self._model = None
        self._df_state = None
        self._initialized = False
    
    def is_available(self) -> bool:
        """Prüft DeepFilterNet3 Verfügbarkeit"""
        return DEEPFILTERNET_AVAILABLE
    
    def _initialize_model(self) -> None:
        """Initialisiert das DeepFilterNet3-Model (Lazy Loading)"""
        if not DEEPFILTERNET_AVAILABLE:
            raise DeepFilterNetError("DeepFilterNet3 nicht verfügbar")
        
        if not self._initialized:
            try:
                print("🤖 Initialisiere DeepFilterNet3-Model...")
                self._model, self._df_state, _ = init_df()
                self._initialized = True
                print("✅ DeepFilterNet3-Model bereit")
            except Exception as e:
                raise DeepFilterNetError(f"Model-Initialisierung fehlgeschlagen: {e}")
    
    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """
        Verarbeitet Audio mit DeepFilterNet3
        
        Args:
            input_wav: Eingabe-WAV-Datei
            output_wav: Ausgabe-WAV-Datei  
            params: Parameter-Dict mit 'attenuation_limit'
        """
        if not self.is_available():
            raise DeepFilterNetError("DeepFilterNet3 nicht verfügbar")
        
        # Model initialisieren falls nötig
        self._initialize_model()
        
        if not os.path.exists(input_wav):
            raise DeepFilterNetError(f"Eingabe-Datei existiert nicht: {input_wav}")
        
        try:
            # Parameter extrahieren
            attenuation_limit = params.get('attenuation_limit', 80.0)
            
            print(f"🤖 DeepFilterNet3: Verarbeite mit {attenuation_limit} dB Dämpfung")
            
            # Audio laden
            audio, meta = load_audio(input_wav, sr=self._df_state.sr())
            
            if audio is None or len(audio) == 0:
                raise DeepFilterNetError("Audio konnte nicht geladen werden")
            
            # Enhancement durchführen
            enhanced_audio = enhance(
                self._model, 
                self._df_state, 
                audio, 
                atten_lim_db=attenuation_limit
            )
            
            if enhanced_audio is None:
                raise DeepFilterNetError("Enhancement lieferte kein Ergebnis")
            
            # Ergebnis speichern
            save_audio(output_wav, enhanced_audio, self._df_state.sr())
            
            if not os.path.exists(output_wav):
                raise DeepFilterNetError("Ausgabe-Datei wurde nicht erstellt")
            
            print(f"✅ DeepFilterNet3: Verarbeitung abgeschlossen")
            
        except Exception as e:
            error_msg = f"DeepFilterNet3-Verarbeitung fehlgeschlagen: {str(e)}"
            print(f"❌ {error_msg}")
            raise DeepFilterNetError(error_msg)
    
    def get_default_params(self) -> Dict[str, Any]:
        """Gibt Standard-Parameter zurück"""
        return {
            'attenuation_limit': 80.0
        }
    
    def get_param_ranges(self) -> Dict[str, tuple]:
        """Gibt Parameterbereiche zurück"""
        return {
            'attenuation_limit': (20.0, 100.0)
        }
    
    def cleanup(self) -> None:
        """Bereinigt Ressourcen"""
        if self._initialized:
            # DeepFilterNet3 Model freigeben falls möglich
            self._model = None
            self._df_state = None
            self._initialized = False
            print("🤖 DeepFilterNet3-Model freigegeben")

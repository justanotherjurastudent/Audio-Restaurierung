"""Abstrakte Basisklassen für Audio-Prozessoren"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class AudioProcessor(ABC):
    """Abstrakte Basis-Klasse für Audio-Prozessoren"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def process(self, input_wav: str, output_wav: str, params: Dict[str, Any]) -> None:
        """Verarbeitet eine Audio-Datei"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Prüft ob der Prozessor verfügbar ist"""
        pass

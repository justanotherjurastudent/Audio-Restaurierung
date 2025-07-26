"""Custom Exception-Klassen für das Audio-Restaurationstool"""

class AudioRestorerException(Exception):
    """Basis-Exception für das Audio-Restaurationstool"""
    pass

class FFmpegNotFoundError(AudioRestorerException):
    """FFmpeg ist nicht verfügbar"""
    pass

class AudioProcessingError(AudioRestorerException):
    """Fehler bei der Audio-Verarbeitung"""
    pass

class DeepFilterNetError(AudioProcessingError):
    """Fehler bei DeepFilterNet3"""
    pass

class AudacityError(AudioProcessingError):
    """Fehler bei Audacity-Verarbeitung"""
    pass

class FileOperationError(AudioRestorerException):
    """Fehler bei Datei-Operationen"""
    pass

class ProcessingCancelledException(AudioRestorerException):
    """Verarbeitung wurde abgebrochen"""
    pass

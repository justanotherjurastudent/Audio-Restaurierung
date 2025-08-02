"""Anleitung für das Audio-Restaurationstool"""
from utils.validators import get_supported_formats
instructions = [
    ("heading", "Willkommen zum Audio-Restaurationstool!\n\n"),
    ("normal", "Diese App hilft dir, das Audio in Videos oder Audiodateien zu verbessern: Rauschen reduzieren, Lautstärke normalisieren und Stimme klarer machen.\n\nWenn du eine Videodatei verarbeiten lässt, dann wird nur das Originalaudio mit dem verbesserten Audio ausgetauscht - das Video selbst wird nicht neu kodiert. Das spart sehr viel Zeit.\n\nFolge diesen Schritten:\n\n"),
    
    ("subheading", "1. Dateien auswählen\n"),
    ("normal", "Klicke auf "),
    ("bold", '"Dateien auswählen" '),
    ("normal", "und wähle deine Videos oder Audios. Unterstützte Formate: "),
    ("normal", ", ".join(get_supported_formats())),
    ("normal", "\n"),
    ("bullet", "• Tipp: Wähle mehrere Dateien auf einmal.\n"),
    ("bullet", "• Die Dateien erscheinen in der Liste rechts.\n\n"),
    
    ("subheading", "2. Einstellungen konfigurieren\n"),
    ("normal", "Passe die Parameter an:\n"),
    ("bullet", "• Lautstärke-Normalisierung: Stelle den Ziel-LUFS-Wert ein (z. B. -20 LUFS für normale Lautstärke).\n"),
    ("bullet", "• Rauschreduzierungs-Methode: Wähle DeepFilterNet3 (KI) für beste Ergebnisse oder Audacity für manuelle Kontrolle.\n"),
    ("bullet", "• Stimmverbesserung: Aktiviere für klarere Stimmen (klassisch oder SpeechBrain AI). Die Qualität der Ausgabe von SpeechBrainAI hängt stark von der Qualität der Eingabedateien ab. Hier sollte daher vorher bei aktivierter Sprachverbesserung eine Audiovorschau unternommen werden.\n"),
    ("normal", "Verwende die Slider in den Tabs der Parameter-Einstellungen für Feinabstimmungen.\n\n"),
    
    ("subheading", "3. Audiovorschau\n"),
    ("normal", "Bevor du die Verarbeitung startest, kannst du eine Vorschau des Audios hören:\n"),
    ("bullet", "• Klicke links im Fenster auf eine Datei und klicke auf den Verarbeiten-Button. Dabei wird eine 30-sekündige 'Vorschau' erstellt, um das Audio mit den aktivierten Einstellungen anzuhören.\n"),
    ("bullet", "• Du kannst die Einstellungen für die Vorschau nach Belieben wieder ändern und eine neue Vorschau erstellen lassen.\n\n"),

    ("subheading", "4. Verarbeitung starten\n"),
    ("normal", "Klicke auf "),
    ("bold", '"Verarbeitung starten" '),
    ("normal", ". Die App verarbeitet die Dateien im Hintergrund.\n"),
    ("bullet", "• Fortschritt siehst du in der Statusleiste und der Dateiliste.\n"),
    ("bullet", "• Abbrechen: Klicke auf 'Abbrechen'.\n"),
    ("normal", "Erneuter Hinweis: Wenn du eine Videodatei verarbeiten lässt, dann wird nur das Originalaudio mit dem verbesserten Audio ausgetauscht - das Video selbst wird nicht neu kodiert. Das spart sehr viel Zeit. \n\n"),
    
    ("subheading", "5. Ergebnisse prüfen\n"),
    ("normal", "Die restaurierten Dateien werden gespeichert (mit Suffix oder im Originalnamen).\n"),
    ("bullet", "• Überprüfe die Vorschau in der App.\n"),
    ("bullet", "• Logs findest du im 'logs'-Ordner bei Fehlern.\n\n"),
    
    ("warning", "Warnung: "),
    ("normal", "Wenn du nicht die Exe-Version benutzt, stelle sicher, dass FFmpeg installiert und im PATH verfügbar ist.\n\n"),
    
    ("italic", "Falls Probleme auftreten, aktiviere den Debug-Modus oder kontaktiere den Entwickler.")
]

# 🎵 Audio-Restaurationstool v1.0.0

Ein Tool zur KI-gestützten Audio-Restauration von Audio- und Videodateien mit deutscher Benutzeroberfläche.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## 📖 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Features](#-features)
- [Screenshots](#-screenshots)
- [Installation](#-installation)
- [Erste Schritte](#-erste-schritte)
- [Detaillierte Anleitung](#-detaillierte-anleitung)
- [Voice Enhancement](#-voice-enhancement)
- [Systemanforderungen](#-systemanforderungen)
- [Häufige Fragen](#-häufige-fragen)
- [Fehlerbehebung](#-fehlerbehebung)
- [Lizenz](#-lizenz)

## 🎯 Überblick

Das **Audio-Restaurationstool** ist ein benutzerfreundliches Python-Programm, das die Tonqualität von Audio- und Videodateien durch moderne KI-Algorithmen und bewährte Audacity-Techniken verbessert. Audio aus Videos wird durch die verbesserte Audiospur ersetzt, ohne das ganze Video neu zu kodieren. Dadurch kann effizient die Tonqualität von Videos auch im Batch-Prozess verarbeitet werden. Es eignet sich perfekt für:

- **Content Creator** die ihre Videos professioneller klingen lassen möchten
- **Podcaster** zur Verbesserung der Aufnahmequalität  
- **Archivare** zur Restauration alter Videoaufnahmen
- **Alle Anwender** die störendes Hintergrund-Rauschen entfernen möchten

### 🔥 Highlights

- 🤖 **Moderne KI-Technologie** (DeepFilterNet3 und SpeechBrain) für beste Ergebnisse
- 🎛️ **Bewährte Audacity-Algorithmen** als zuverlässige Alternative  
- 🎙️ **Professionelle Stimmverbesserung** mit klassischen und KI-basierten Methoden
- 🔊 **Professionelle LUFS-Normalisierung** für einheitliche Lautstärke
- 📊 **Batch-Verarbeitung** - Bearbeiten Sie dutzende Videos automatisch
- 🇩🇪 **Deutsche Benutzeroberfläche** - Alles auf Deutsch erklärt
- ⏹️ **Abbrechen jederzeit möglich** - Volle Kontrolle über den Prozess

## ✨ Features

### 🎯 Rauschreduzierungsmethoden

| Methode | Beschreibung | Qualität | Geschwindigkeit | Empfehlung |
|---------|-------------|----------|----------------|------------|
| **DeepFilterNet3** | Modernste KI-Rauschreduzierung | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Beste Ergebnisse |
| **Audacity** | Bewährte spektrale Methode | ⭐⭐⭐ | ⭐⭐⭐⭐ | Zuverlässig & schnell |
| **FFmpeg-Fallback** | Basis-Filterung | ⭐ | ⭐⭐⭐⭐⭐ | Nur als Notfall |

### 🎙️ Voice Enhancement (Stimmverbesserung)

| Methode | Beschreibung | Qualität | Geschwindigkeit | Empfehlung |
|---------|-------------|----------|----------------|------------|
| **SpeechBrain AI** | KI-basierte spektrale Maskierung | ⭐⭐⭐⭐ | ⭐⭐⭐ | Modernste Technologie |
| **Klassisch** | EQ + Kompression + Harmonics | ⭐⭐ | ⭐⭐⭐⭐⭐ | Zuverlässig & konfigurierbar |

#### Klassische Voice Enhancement Parameter:
- **Clarity Boost**: Hebt 2-4 kHz für bessere Sprachverständlichkeit
- **Warmth Boost**: Betont 120-250 Hz für volleren, körperlichen Klang
- **Bandwidth Extension**: Stellt hohe Frequenzen wieder her
- **Harmonic Restoration**: Repariert Kompressionsartefakte
- **Compression**: Dynamikbearbeitung für gleichmäßigere Lautstärke

#### SpeechBrain AI Parameter:
- **Enhancement Strength**: Mischungsverhältnis Original/Enhanced (0.5-2.0)
- **Audio Normalization**: Automatische Pegelanpassung nach Enhancement

### 🔊 Lautstärke-Normalisierung

- **LUFS-Standard** für professionelle Audio-Produktion
- **Einstellbarer Bereich** von -23 LUFS (leise) bis -10 LUFS (laut)
- **Automatische Anpassung** an Broadcasting-Standards

### 📊 Benutzerfreundlichkeit

- **Live-Fortschrittsanzeige** für jede Datei
- **Visuelle Status-Icons** (🔄 Verarbeitung, ✅ Fertig, ❌ Fehler, ⏹️ Abgebrochen)
- **Flexible Dateinamen** - Suffix oder Original-Namen verwenden
- **Eigene Ausgabeordner** wählbar
- **Robustes Fallback-System** - Falls eine Methode fehlschlägt, wird automatisch die nächste versucht

## 🖼️ Screenshots

### Hauptfenster mit Voice Enhancement
<"<img width="1092" height="978" alt="image" src="https://github.com/user-attachments/assets/ff790cdc-1d47-452c-a8f0-34bdb777d68a" />

*Das Screenshot zeigt die neue Voice Enhancement Sektion mit Methodenauswahl und konfigurierbaren Parametern für beide Ansätze.*

## 🚀 Installation
Es gibt zwei Wege, das Programm zu benutzen.
1. Rechts auf dieser Seite findet man unter [Releases](https://github.com/justanotherjurastudent/Audio-Restaurierung/releases/) eine exe-Version, die auf Windows sofort gestartet werden kann. Dies ist die einfachste Möglichkeit.
2. Das Programm kann auch als Projekt heruntergeladen werden. Dazu verweise ich auf folgende Anleitung:

### Voraussetzungen

1. **Python 3.8 oder höher**
Python muss installiert sein. Die Version hiervon sollte 3.8 oder höher sein. Wenn man Python von der offiziellen Webseite herunterlädt, dann ist das der Fall. Ansonsten kann man die Version überprüfen im PowerShell-Fenster:
```ps
python --version
```

2. **FFmpeg** (essentiell für Video-Verarbeitung)
Damit die Audiospuren verarbeitet werden können, braucht es FFmpeg.

**Windows:**
- Laden Sie FFmpeg von https://ffmpeg.org/download.html herunter
- Entpacken Sie es nach `C:\ffmpeg`
- Fügen Sie `C:\ffmpeg\bin` zu Ihrem PATH hinzu

**macOS:**
brew install ffmpeg


**Linux (Ubuntu/Debian):**
sudo apt update
sudo apt install ffmpeg


### Programm installieren

1. **Repository herunterladen**
git clone https://github.com/justanotherjurastudent/audio_restauration_from_videos.git
cd audio_restauration_from_videos

2. **Python-Pakete installieren**
pip install -r requirements.txt

3. **Programm starten**
python main.py




## 🎬 Erste Schritte

### 1. Videos auswählen
- Klicken Sie auf **"📁 Videos auswählen"**
- Wählen Sie eine oder mehrere Video-Dateien aus
- Unterstützte Formate: MP4, MOV, MKV, AVI, M4V, WebM, FLV, WMV

### 2. Methode wählen
- **DeepFilterNet3 (empfohlen)**: Beste Qualität durch KI
- **Audacity**: Schnell und zuverlässig, mehr Einstellmöglichkeiten

### 3. Voice Enhancement aktivieren (optional)
- Aktivieren Sie **"Stimmverbesserung aktivieren"**
- Wählen Sie zwischen:
  - **🎛️ Klassisch**: EQ + Kompression (schnell, konfigurierbar)
  - **🤖 SpeechBrain AI**: Spektrale Maskierung (beste Qualität)

### 4. Lautstärke einstellen
- **-30 LUFS**: Für leise Umgebungen (Podcasts, Hörbücher)
- **-20 LUFS**: Standard
- **-10 LUFS**: Für laute Umgebungen

### 5. Verarbeitung starten
- Klicken Sie **"🚀 Verarbeitung starten"**
- Verfolgen Sie den Fortschritt in Echtzeit
- Bei Bedarf mit **"⏹️ Abbrechen"** stoppen

### 6. Ergebnisse finden
- Standardmäßig werden die verbesserten Videos neben den Originalen gespeichert
- Mit dem Suffix "_restauriert" (z.B. `mein_video_restauriert.mp4`)

## 📚 Detaillierte Anleitung

### 🎛️ Audacity-Parameter im Detail

#### Rauschunterdrückung (6-30 dB)
- **6-12 dB**: Leichte Verbesserung, natürlicher Klang
- **12-18 dB**: Standard-Einstellung für die meisten Videos  
- **18-30 dB**: Starke Rauschreduzierung, kann Stimme beeinträchtigen

#### Empfindlichkeit (0-20)
- **0-5**: Nur offensichtliches Rauschen wird entfernt
- **6-10**: Ausgewogene Einstellung (empfohlen)
- **10-20**: Sehr sensibel, kann gewünschte Töne entfernen

#### Frequenz-Glättung (0-10)
- **0**: Keine Glättung (schärfste Trennung)
- **1-3**: Reduziert "musikartige" Artefakte
- **4-10**: Starke Glättung für sehr verrauschte Aufnahmen

### 🔄 DeepFilterNet3-Parameter

#### Dämpfungsgrenze (20-100 dB)
- **20-50 dB**: Sehr starke Rauschreduzierung (Risiko: Verzerrungen)
- **70-85 dB**: Empfohlener Bereich für beste Ergebnisse
- **85-100 dB**: Sanfte Behandlung, weniger effektiv

### 📁 Dateinamen & Speicherorte

#### Dateinamen-Optionen
1. **Suffix verwenden** (Standard)
- Fügt einen Text vor die Dateiendung hinzu
- Beispiel: `video.mp4` → `video_restauriert.mp4`
- Anpassbar: "verbessert", "KI", "sauber", etc.

2. **Ursprüngliche Namen**
- Behält den Original-Dateinamen bei
- Automatische Nummerierung bei Konflikten
- Beispiel: `video.mp4` → `video(1).mp4`

#### Speicherorte
1. **Neben Original-Dateien** (Standard)
- Videos werden im gleichen Ordner gespeichert
- Einfach zu finden und zu vergleichen

2. **Eigener Ordner**
- Alle verarbeiteten Videos in einem separaten Ordner
- Übersichtlicher bei vielen Dateien

## 🎙️ Voice Enhancement

### 🎛️ Klassische Methode

Die klassische Voice Enhancement Methode verwendet bewährte Audio-Engineering-Techniken:

#### Parameter im Detail

**Clarity Boost (0.0-5.0)**
- Hebt den Frequenzbereich 2-4 kHz an
- **0-2**: Subtile Verbesserung der Sprachverständlichkeit
- **2-4**: Standard-Einstellung für die meisten Stimmen
- **4-5**: Starke Anhebung, kann bei manchen Stimmen zu scharf wirken

**Warmth Boost (0.0-5.0)**
- Betont den Bereich 120-250 Hz für mehr Körper
- **0-1**: Leichte Erwärmung
- **2-3**: Standard für dünne oder nasale Stimmen
- **3-5**: Starke Bassverstärkung

**Bandwidth Extension (0.0-5.0)**
- Rekonstruiert hohe Frequenzen (6-12 kHz)
- **0-1**: Subtile Aufhellung
- **1-3**: Standard für komprimierte Audio-Quellen
- **3-5**: Starke Wiederherstellung für stark komprimierte Aufnahmen

**Harmonic Restoration (0.0-5.0)**  
- Repariert Verzerrungen und Kompressionsartefakte
- **0-1**: Minimale harmonische Sättigung
- **1-2**: Ausgewogen für die meisten Anwendungen
- **2-5**: Starke Restauration für stark beschädigte Aufnahmen

**Compression Ratio (1.0-5.0)**
- Dynamikbearbeitung für gleichmäßigere Lautstärke
- **1.0**: Keine Kompression
- **2.0**: Leichte Kompression (empfohlen)
- **3.0-4.0**: Standard für Podcast/Broadcast
- **5.0**: Starke Kompression für sehr ungleichmäßige Aufnahmen

**Compression Threshold (-30.0 bis -10.0 dB)**
- Pegel ab dem die Kompression einsetzt
- **-30 dB**: Sehr niedrige Schwelle, komprimiert fast alles
- **-18 dB**: Standard-Einstellung
- **-10 dB**: Hohe Schwelle, komprimiert nur laute Passagen

### 🤖 SpeechBrain AI Methode

Die SpeechBrain AI Methode nutzt neuronale Netzwerke für spektrale Maskierung:

#### Parameter im Detail

**Enhancement Strength (0.5-2.0)**
- Bestimmt das Mischungsverhältnis zwischen Original und Enhanced Audio
- **0.5**: 50% Original + 50% Enhanced (subtil)
- **1.0**: 100% Enhanced (Standard)
- **1.5-2.0**: Verstärkte Enhancement-Effekte

**Audio Normalization (Ein/Aus)**
- Automatische Pegelanpassung nach dem Enhancement
- **Ein**: Optimiert die Lautstärke automatisch (empfohlen)
- **Aus**: Behält die Original-Lautstärke bei

#### Technische Details
- **Sample Rate**: Arbeitet intern mit 16 kHz, konvertiert automatisch
- **Latenz**: ~2-3x länger als klassische Methode
- **Speicherbedarf**: Benötigt zusätzlich ~500 MB RAM für das AI-Modell

### 🆚 Wann welche Methode verwenden?

| Anwendungsfall | Empfohlene Methode | Begründung |
|---------------|-------------------|------------|
| **Podcast-Aufnahmen** | SpeechBrain AI | Beste Sprachverständlichkeit |
| **YouTube-Videos** | Klassisch | Schneller, mehr Kontrolle |
| **Live-Streaming** | Klassisch | Geringere Latenz |
| **Professionelle Produktion** | SpeechBrain AI | Höchste Qualität |
| **Batch-Verarbeitung** | Klassisch | Deutlich schneller |
| **Alte/beschädigte Aufnahmen** | SpeechBrain AI + Klassisch | Kombinierte Anwendung |

### ⚡ Batch-Verarbeitung Tipps

1. **Große Mengen aufteilen**
- Verarbeiten Sie nicht mehr als 10-15 Videos gleichzeitig
- Bei Problemen ist so weniger verloren

2. **Speicherplatz prüfen**
- Planen Sie etwa die doppelte Dateigröße als freien Speicher ein
- Videos werden während der Verarbeitung temporär vergrößert

3. **Abbruch nutzen**
- Sie können jederzeit abbrechen
- Bereits fertige Videos bleiben erhalten
- Nur die aktuelle Verarbeitung wird gestoppt

## 💻 Systemanforderungen

### Mindestanforderungen
- **Betriebssystem**: Windows 10, macOS 10.14, Ubuntu 18.04 (oder neuer)
- **Python**: Version 3.8 oder höher
- **RAM**: 4 GB (8 GB empfohlen für DeepFilterNet3, 6 GB für SpeechBrain)
- **Speicher**: 10 GB freier Speicherplatz für temporäre Dateien
- **Prozessor**: Dual-Core (Quad-Core empfohlen)

### Empfohlene Konfiguration
- **RAM**: 16 GB oder mehr für große Video-Dateien und SpeechBrain AI
- **SSD**: Für schnellere Verarbeitung
- **Grafikkarte**: GPU-Beschleunigung wird automatisch genutzt (falls verfügbar)

### SpeechBrain-spezifische Anforderungen
- **Zusätzlicher RAM**: +2 GB für das AI-Modell
- **Internet**: Beim ersten Start zum Download des Modells (~500 MB)
- **PyTorch**: Wird automatisch mit den Dependencies installiert

### Unterstützte Video-Formate

| Format | Eingabe | Ausgabe | Anmerkungen |
|--------|---------|---------|-------------|
| MP4 | ✅ | ✅ | Empfohlenes Format |
| MOV | ✅ | ✅ | Apple-Standard |
| MKV | ✅ | ✅ | Open-Source-Format |
| AVI | ✅ | ✅ | Älteres Format |
| M4V | ✅ | ✅ | iTunes-Format |
| WebM | ✅ | ✅ | Web-optimiert |
| FLV | ✅ | ✅ | Flash-Video |
| WMV | ✅ | ✅ | Windows Media |

## ❓ Häufige Fragen

### 🤔 Welche Methode soll ich wählen?

**Für die beste Qualität:**
- Verwenden Sie **DeepFilterNet3** für Rauschreduzierung wenn verfügbar
- Kombinieren Sie mit **SpeechBrain AI** für Voice Enhancement
- Moderne KI liefert meist bessere Ergebnisse als traditionelle Methoden

**Für Geschwindigkeit:**
- **Audacity** ist deutlich schneller für Rauschreduzierung
- **Klassisches Voice Enhancement** ist 3x schneller als SpeechBrain
- Besonders bei älteren Computern oder vielen Dateien

**Für maximale Kontrolle:**
- **Audacity** + **Klassisches Voice Enhancement** bieten mehr Einstellungsmöglichkeiten
- Sie können das Ergebnis feiner abstimmen

### 🎙️ Was ist Voice Enhancement und brauche ich das?

**Voice Enhancement verbessert gezielt die Stimmqualität** durch:
- Klarere Aussprache (Clarity Boost)
- Volleren Klang (Warmth Boost)  
- Wiederherstellung verlorener Frequenzen
- Gleichmäßigere Lautstärke

**Sie brauchen es wenn:**
- ✅ Ihre Stimme dünn oder nasal klingt
- ✅ Das Audio komprimiert oder "flach" wirkt
- ✅ Sie professionellere Ergebnisse wollen
- ✅ Alte oder schlecht aufgenommene Videos bearbeiten

**Sie brauchen es nicht wenn:**
- ❌ Die Stimmqualität bereits sehr gut ist
- ❌ Sie nur Hintergrundgeräusche entfernen wollen
- ❌ Geschwindigkeit wichtiger als Qualität ist

### 🆚 SpeechBrain AI vs. Klassisches Voice Enhancement?

| Kriterium | SpeechBrain AI | Klassisch |
|-----------|---------------|-----------|
| **Qualität** | ⭐⭐⭐⭐ Beste | ⭐⭐ Sehr gut |
| **Geschwindigkeit** | ⭐⭐⭐ Langsamer | ⭐⭐⭐⭐⭐ Schnell |
| **Konfiguration** | ⭐⭐ Wenige Parameter | ⭐⭐⭐⭐⭐ Viele Parameter |
| **Speicherbedarf** | ⭐⭐ Hoch (~6 GB) | ⭐⭐⭐⭐ Normal (~4 GB) |
| **CPU-Last** | ⭐⭐ Hoch | ⭐⭐⭐⭐ Niedrig |

**Empfehlung**: Probieren Sie beide aus und vergleichen Sie das Ergebnis bei Ihren Aufnahmen.

### 🔧 Was bedeuten die verschiedenen LUFS-Werte?

**LUFS** (Loudness Units Full Scale) ist der professionelle Standard für Lautstärke-Messung:

- **-23 LUFS**: EBU R128 Standard für Rundfunk (sehr leise)
- **-18 LUFS**: Streaming-Dienste wie Spotify
- **-15 LUFS**: YouTube, Instagram (Standard-Einstellung)
- **-12 LUFS**: Podcast-Standard
- **-10 LUFS**: Sehr laut, für laute Umgebungen

### 🎯 Wie erkenne ich gute Ergebnisse?

**Positive Zeichen:**
- Hintergrund-Rauschen ist deutlich reduziert
- Stimme klingt klarer und natürlicher
- Keine "metallischen" oder "robotischen" Artefakte
- Bessere Sprachverständlichkeit
- Vollerer, professionellerer Klang

**Probleme:**
- Stimme klingt verzerrt oder "unterwasser"
- Neue, künstliche Geräusche sind entstanden
- Audio klingt "flach" oder leblos
- Übertrieben scharfer oder bassiger Klang

→ **Lösung**: Reduzieren Sie die Stärke der Parameter oder wechseln Sie die Methode

### 💾 Warum sind die Ausgabe-Dateien größer?

Das ist normal und hat mehrere Gründe:

1. **Höhere Audio-Qualität**: 48kHz statt ursprünglich niedrigerer Samplerate
2. **Unkomprimiertes Audio**: Während der Verarbeitung für beste Qualität
3. **Codec-Unterschiede**: Die finale MP4-Datei verwendet AAC mit 128kbit/s
4. **Voice Enhancement**: Zusätzliche Frequenz-Informationen

Die Dateigröße ist meist nur 10-30% größer als das Original.

## 🔧 Fehlerbehebung

### ❌ "FFmpeg nicht gefunden"

**Problem**: FFmpeg ist nicht installiert oder nicht im PATH verfügbar.

**Lösung**:
1. Laden Sie FFmpeg von https://ffmpeg.org/download.html herunter
2. Installieren Sie es system-weit
3. Starten Sie das Terminal/Kommandozeile neu
4. Testen Sie mit: `ffmpeg -version`

### ❌ "DeepFilterNet3 nicht verfügbar"

**Problem**: Die KI-Bibliothek konnte nicht geladen werden.

**Lösung**:

pip uninstall DeepFilterNet3
pip install DeepFilterNet3

Bei weiterhin Problemen verwenden Sie die **Audacity-Methode** - diese funktioniert immer.

### ❌ "SpeechBrain AI nicht verfügbar"

**Problem**: Die SpeechBrain-Bibliothek oder Abhängigkeiten fehlen.

**Lösung**:
pip install speechbrain torch torchaudio

Falls das nicht hilft:
- Verwenden Sie **Klassisches Voice Enhancement** - funktioniert ohne zusätzliche KI-Bibliotheken
- Prüfen Sie Ihre Python-Version (mindestens 3.8 erforderlich)

### ❌ "Audio zu kurz für Audacity-Methode"

**Problem**: Das Video ist kürzer als 0.5 Sekunden.

**Lösung**: 
- Verwenden Sie **DeepFilterNet3** für sehr kurze Clips
- Oder kombinieren Sie mehrere kurze Clips zu einem längeren Video

### 🐌 Verarbeitung ist sehr langsam

**Mögliche Ursachen und Lösungen**:

1. **Zu wenig RAM**: Schließen Sie andere Programme
2. **Große Video-Dateien**: Verarbeiten Sie kleinere Batches
3. **Alter Computer**: Verwenden Sie Audacity statt DeepFilterNet3
4. **Festplatte voll**: Schaffen Sie mehr freien Speicherplatz

### 🔄 Verarbeitung hängt oder stürzt ab

**Sofortmaßnahmen**:
1. Klicken Sie **"⏹️ Abbrechen"**
2. Warten Sie 10 Sekunden
3. Schließen Sie das Programm falls nötig

**Langfristige Lösungen**:
- Aktualisieren Sie Python und alle Pakete
- Verarbeiten Sie weniger Dateien gleichzeitig
- Prüfen Sie verfügbaren Speicherplatz

### 📱 Ergebnisse werden nicht gespeichert

**Überprüfen Sie**:
1. **Schreibrechte**: Haben Sie Berechtigung im Zielordner?
2. **Speicherplatz**: Ist genug Platz verfügbar?
3. **Dateiname**: Enthält er ungültige Zeichen?
4. **Antivirus**: Blockiert es die Erstellung neuer Dateien?

### 🎙️ Voice Enhancement funktioniert nicht

**Häufige Probleme**:
1. **SpeechBrain-Modell lädt nicht**: Internetverbindung prüfen (beim ersten Start)
2. **Keine hörbare Verbesserung**: Parameter zu niedrig eingestellt
3. **Verzerrungen**: Parameter zu hoch, reduzieren Sie die Werte
4. **Programm stürzt ab**: Zu wenig RAM, verwenden Sie klassische Methode

## 🎓 Tipps für beste Ergebnisse

### 🎤 Für Podcast & Sprache
Methode: DeepFilterNet3
LUFS: -18 bis -15
Audacity-Fallback: Rauschred. 15dB, Empfindlichkeit 8

### 🎬 Für Video-Content
Methode: DeepFilterNet3
LUFS: -15 (YouTube Standard)
Dämpfung: 75-80 dB

## 📝 Lizenz

Dieses Projekt steht unter der GNU General Public License v3.0. Siehe [LICENSE](LICENSE) für Details.

### Was bedeutet GPL-3.0?

- ✅ **Freie Nutzung**: Sie können das Programm kostenlos verwenden
- ✅ **Quellcode einsehen**: Der gesamte Code ist öffentlich verfügbar  
- ✅ **Änderungen erlaubt**: Sie dürfen den Code modifizieren
- ✅ **Weiterverteilung**: Sie dürfen das Programm weitergeben
- ⚠️ **Copyleft**: Änderungen müssen ebenfalls unter GPL-3.0 veröffentlicht werden
- ⚠️ **Keine Garantie**: Das Programm wird ohne Gewährleistung bereitgestellt

**Kurz gesagt**: Sie können alles damit machen, aber Verbesserungen müssen der Community zur Verfügung gestellt werden.

## Credits

**Schröter, H., Rosenkranz, T., Escalante-B., A. N., & Maier, A. (2023).**  
*DeepFilterNet: Perceptually Motivated Real-Time Speech Enhancement.*  
In *INTERSPEECH 2023*.  
[BibTeX](https://dblp.org/rec/conf/interspeech/SchroeterREM23.html?view=bibtex)

**Ravanelli, M., Parcollet, T., Moumen, A., de Langen, S., Subakan, C., Plantinga, P., Wang, Y., Mousavi, P., Della Libera, L., Ploujnikov, A., Paissan, F., Borra, D., Zaiem, S., Zhao, Z., Zhang, S., Karakasidis, G., Yeh, S.-L., Champion, P., Rouhe, A., Braun, R., Mai, F., Zuluaga-Gomez, J., Mousavi, S. M., Nautsch, A., Nguyen, H., Liu, X., Sagar, S., Duret, J., Mdhaffar, S., Laperrière, G., Rouvier, M., De Mori, R., & Estève, Y. (2024).**  
*Open-Source Conversational AI with SpeechBrain 1.0.*  
Journal of Machine Learning Research, 25(333).  
[Link zur Publikation](http://jmlr.org/papers/v25/24-0991.html)

**Ravanelli, M., Parcollet, T., Plantinga, P., Rouhe, A., Cornell, S., Lugosch, L., Subakan, C., Dawalatabad, N., Heba, A., Zhong, J., Chou, J.-C., Yeh, S.-L., Fu, S.-W., Liao, C.-F., Rastorgueva, E., Grondin, F., Aris, W., Na, H., Gao, Y., De Mori, R., & Bengio, Y. (2021).**  
*SpeechBrain: A General-Purpose Speech Toolkit.*  
arXiv:2106.04624.  
[Link zur arXiv-Version](https://arxiv.org/abs/2106.04624)


---

**Entwickelt mit ❤️ für bessere Audio-Qualität**

*Haben Sie Fragen oder Verbesserungsvorschläge? Erstellen Sie gerne ein Issue auf GitHub!*

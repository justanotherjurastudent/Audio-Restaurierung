# 🎵 Audio-Restaurationstool v1.0.0

Ein professionelles Tool zur KI-gestützten Audio-Restauration aus Videos mit deutscher Benutzeroberfläche.

![Version](https://img.shields.io/badge/version-0.6.8-blue.svg)
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
- [Systemanforderungen](#-systemanforderungen)
- [Häufige Fragen](#-häufige-fragen)
- [Fehlerbehebung](#-fehlerbehebung)
- [Lizenz](#-lizenz)

## 🎯 Überblick

Das **Audio-Restaurationstool** ist ein benutzerfreundliches Python-Programm, das die Tonqualität von Videos durch moderne KI-Algorithmen und bewährte Audacity-Techniken verbessert. Es eignet sich perfekt für:

- **Content Creator** die ihre Videos professioneller klingen lassen möchten
- **Podcaster** zur Verbesserung der Aufnahmequalität  
- **Archivare** zur Restauration alter Videoaufnahmen
- **Alle Anwender** die störendes Hintergrund-Rauschen entfernen möchten

### 🔥 Highlights

- 🤖 **Modernste KI-Technologie** (DeepFilterNet3) für beste Ergebnisse
- 🎛️ **Bewährte Audacity-Algorithmen** als zuverlässige Alternative  
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

### Hauptfenster
<img width="1101" height="884" alt="image" src="https://github.com/user-attachments/assets/94068edd-eb93-486f-a769-d5a47eb48711" />


## 🚀 Installation

### Voraussetzungen

1. **Python 3.8 oder höher**
python --version # Sollte Python 3.8+ anzeigen

2. **FFmpeg** (essentiell für Video-Verarbeitung)

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
python main.py  # ✅ Neu



## 🎬 Erste Schritte

### 1. Videos auswählen
- Klicken Sie auf **"📁 Videos auswählen"**
- Wählen Sie eine oder mehrere Video-Dateien aus
- Unterstützte Formate: MP4, MOV, MKV, AVI, M4V, WebM, FLV, WMV

### 2. Methode wählen
- **DeepFilterNet3 (empfohlen)**: Beste Qualität durch KI
- **Audacity**: Schnell und zuverlässig, mehr Einstellmöglichkeiten

### 3. Lautstärke einstellen
- **-23 LUFS**: Für leise Umgebungen (Podcasts, Hörbücher)
- **-15 LUFS**: Standard für YouTube, Social Media
- **-10 LUFS**: Für laute Umgebungen

### 4. Verarbeitung starten
- Klicken Sie **"🚀 Verarbeitung starten"**
- Verfolgen Sie den Fortschritt in Echtzeit
- Bei Bedarf mit **"⏹️ Abbrechen"** stoppen

### 5. Ergebnisse finden
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
- **RAM**: 4 GB (8 GB empfohlen für DeepFilterNet3)
- **Speicher**: 10 GB freier Speicherplatz für temporäre Dateien
- **Prozessor**: Dual-Core (Quad-Core empfohlen)

### Empfohlene Konfiguration
- **RAM**: 16 GB oder mehr für große Video-Dateien
- **SSD**: Für schnellere Verarbeitung
- **Grafikkarte**: GPU-Beschleunigung wird automatisch genutzt (falls verfügbar)

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
- Verwenden Sie **DeepFilterNet3** wenn verfügbar
- Moderne KI liefert meist bessere Ergebnisse als traditionelle Methoden

**Für Geschwindigkeit:**
- **Audacity** ist deutlich schneller
- Besonders bei älteren Computern oder vielen Dateien

**Für maximale Kontrolle:**
- **Audacity** bietet mehr Einstellungsmöglichkeiten
- Sie können das Ergebnis feiner abstimmen

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

**Probleme:**
- Stimme klingt verzerrt oder "unterwasser"
- Neue, künstliche Geräusche sind entstanden
- Audio klingt "flach" oder leblos

→ **Lösung**: Reduzieren Sie die Stärke der Rauschreduzierung

### 💾 Warum sind die Ausgabe-Dateien größer?

Das ist normal und hat mehrere Gründe:

1. **Höhere Audio-Qualität**: 48kHz statt ursprünglich niedrigerer Samplerate
2. **Unkomprimiertes Audio**: Während der Verarbeitung für beste Qualität
3. **Codec-Unterschiede**: Die finale MP4-Datei verwendet AAC mit 128kbit/s

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

---

**Entwickelt mit ❤️ für bessere Audio-Qualität**

*Haben Sie Fragen oder Verbesserungsvorschläge? Erstellen Sie gerne ein Issue auf GitHub!*

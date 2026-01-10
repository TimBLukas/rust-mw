# Diagramme für Edu-Ransomware Präsentation

Dieses Verzeichnis enthält Mermaid-Diagramme (.mmd), die die Architektur und Abläufe des Projekts visualisieren.

## Diagramm-Übersicht

| Datei | Beschreibung | Empfohlene Größe |
|-------|--------------|------------------|
| `01_gesamtarchitektur.mmd` | Komplette Systemarchitektur mit allen Komponenten | 1920x1080 |
| `02_rust_agent_architektur.mmd` | Detaillierte Rust Agent Modul-Struktur | 1600x1200 |
| `03_drive_by_download.mmd` | Sequenzdiagramm: DbD Ablauf | 1200x900 |
| `04_pdf_phishing.mmd` | PDF Phishing Prozess & Social Engineering | 1400x1000 |
| `05_verschluesselung_atomic.mmd` | AES-256-CTR Atomic Encryption Sequenz | 1400x1200 |
| `06_c2_kommunikation.mmd` | C2 Reverse Shell Kommunikation | 1600x1400 |
| `07_attack_kill_chain.mmd` | Angriffsphasen (Kill Chain) | 1920x600 |
| `08_projektstruktur.mmd` | Repository Struktur | 1400x1200 |

## Export zu PNG/SVG

### Option 1: Mermaid Live Editor (Empfohlen)
1. Öffne https://mermaid.live
2. Kopiere den Inhalt der .mmd Datei
3. Klicke auf "Export" → PNG oder SVG
4. Speichere im `images/` Ordner

### Option 2: Mermaid CLI
```bash
# Installation
npm install -g @mermaid-js/mermaid-cli

# Export als PNG
mmdc -i 01_gesamtarchitektur.mmd -o ../images/gesamtarchitektur.png -w 1920 -H 1080 -b white

# Export als SVG
mmdc -i 01_gesamtarchitektur.mmd -o ../images/gesamtarchitektur.svg -b white
```

### Option 3: VS Code Extension
1. Installiere "Markdown Preview Mermaid Support" oder "Mermaid Markdown Syntax Highlighting"
2. Öffne die .mmd Datei
3. Rechtsklick → "Export Mermaid Diagram"

## Integration in LaTeX

Nach dem Export die Bilder in `presentation.tex` einbinden:

```latex
\begin{frame}{Gesamtarchitektur}
  \centering
  \includegraphics[width=0.95\textwidth]{images/gesamtarchitektur.png}
\end{frame}
```

## Diagramm-Inhalte im Detail

### 01_gesamtarchitektur.mmd
- **Delivery Phase**: PDF Phishing → DbD Server → Payloads
- **Victim System**: Rust Agent mit allen Modulen, Dateien
- **Tunnel**: Pinggy.io TCP Tunnel
- **Attacker**: C2 Server, Loot Ordner, Operator Console
- Zeigt kompletten Datenfluss und Kommunikationspfade

### 02_rust_agent_architektur.mmd
- Entry Point (main.rs) mit Daemonization
- Evasion Checks: RAM (≥3GB), CPU (≥3), Disk (≥60GB)
- Persistence: Windows Registry, Linux systemd, macOS LaunchAgent
- Network: TCP Loop, Command Parsing, Exfiltration
- Crypto: Key Generation, AES-256-CTR, Atomic Operations
- Extortion: Ransom Note, Wallpaper, Browser

### 03_drive_by_download.mmd
- Sequenzdiagramm Opfer ↔ DbD Server
- Phase 1: Initial Access (GET /game, /security, /prize)
- Phase 2: Payload Delivery mit User-Agent Analyse
- Phase 3: Execution auf Victim System
- OS-spezifische Payload-Auswahl

### 04_pdf_phishing.mmd
- Generator: Pillow + FPDF
- Erstellungsprozess: Fake-Rechnung → Blur → Overlay → Link
- Social Engineering: Neugier, Dringlichkeit, Vertrauen, Angst
- Opfer-Reaktion: Öffnen → Sehen → Klicken → Download

### 05_verschluesselung_atomic.mmd
- Key Generation (32 Byte Random)
- File Discovery mit WalkDir
- Atomic Encryption: Temp-Datei → Rename → Original löschen
- Stream Processing mit 4KB Chunks
- Decryption nach "Zahlung"

### 06_c2_kommunikation.mmd
- Tunnel Setup (Attacker-Side)
- Reverse Shell Connection durch NAT/Firewall
- Command & Control: shell, exfil, encrypt, decrypt
- Vollständiger Kommunikationsablauf

### 07_attack_kill_chain.mmd
- 8 Phasen: Delivery → Execution → Evasion → Persistence → C2 → Exfiltration → Encryption → Extortion
- Detaillierte Schritte pro Phase
- Abbruchpfad bei fehlgeschlagener Evasion

### 08_projektstruktur.mmd
- Komplette Repository-Struktur
- malware_agent/src/ mit allen Rust-Modulen
- c2_server/ Python Server
- delivery/ mit DbD-Site und pdf_phishing
- Datenfluss-Verbindungen

# Ablaufplan: Ransomware Präsentation & Demo

**Datum:** **\*\*\*\***\_\_\_**\*\*\*\***
**Gesamtdauer:** ca. 25-30 Min (inkl. Demo)

---

## Folien-Übersicht & Zuweisung

|  Nr.   | Folientitel / Thema                         | Sprecher | Status | Notizen / To-Do                                       |
| :----: | :------------------------------------------ | :------: | :----: | :---------------------------------------------------- |
| **1**  | **Titelfolie**                              |    Shiao     |  [ ]   |                                                       |
| **2**  | **Agenda**                                  |    Shiao     |  [ ]   |                                                       |
| **3**  | **Finanzielle Auswirkungen**                |    Shiao      |  [ ]   | Fokus: Anstieg der Schadenssummen                     |
| **4**  | **ENISA Threat Landscape 2024**             |    Shiao      |  [ ]   | Ransomware als Top-EU-Bedrohung                       |
| **5**  | **Motivation der Angreifer**                |    Dome      |  [ ]   | Geld, Sabotage, Geopolitik                            |
| **6**  | **Die Ökonomie**                            |    Dome      |  [ ]   | RaaS Geschäftsmodell erklären                         |
| **7**  | **Personalisierungsgrad: Beispiel LockBit** |    Dome      |  [ ]   |                                                       |
| **9**  | **Grundlegende Typen**                      |    Dome      |  [ ]   | Crypto vs. Locker                                     |
| **10** | **Case Study**                              |    Nick      |  [ ]   | **Übergang:** Vorstellung eigenes Projekt             |
| **11** | **Projektübersicht**                        |    Nick      |  [ ]   | Ziel: Bildungssimulation                              |
| **12** | **Systemarchitektur & Tech Stack**          |    Nick      |  [ ]   | Diagramm zeigen (Rust/Python/Bash)                    |
| **13** | **Phasen eines Angriffs**                   |    Nick      |  [ ]   | Kill-Chain Überblick                                  |
| **14** | **Phase 1: Distribution u. Infektion**      |    Nick      |  [ ]   | Theorie: Wie kommt Malware rein?                      |
| **15** | **Phase 1 Drive-by-Download**               |    Denis      |  [ ]   | **🔴 LIVE:** Fake-Webseite zeigen (`/game`)           |
| **16** | **Phase 1: Pdf-Phishing**                   |    Denis      |  [ ]   | **🔴 LIVE:** PDF öffnen, Link klicken, `.deb` Install |
| **17** | **Phase 2: Execution u. Evasion**           |    Denis      |  [ ]   | Theorie: Ausführung & Verstecken                      |
| **18** | **Phase 2: Agent Architektur**              |    Tim      |  [ ]   | Code-Blick: `evasion.rs` (RAM/CPU Check)              |
| **19** | **Phase 3: C2 u. Exfiltration**             |    Tim      |  [ ]   | Theorie: Kommunikation zum Angreifer                  |
| **20** | **C2-Kommunikation**                        |    Tim      |  [ ]   | **🔴 LIVE:** Python Shell zeigen, `exfil` ausführen   |
| **21** | **Phase 4: Encryption (Impact)**            |    Tim      |  [ ]   | Theorie: AES-Verschlüsselung                          |
| **22** | **Phase 4: Verschlüsselungsprozess**        |    Denis      |  [ ]   | **🔴 LIVE:** Wallpaper-Change & Panic-Browser         |
| **23** | **Phase 5: Decryption**                     |    Tim      |  [ ]   | **🔴 LIVE:** `decrypt` Befehl, Restore zeigen         |
| **24** | **Prävention u. Detektion**                 |     Max     |  [ ]   | Backups, EDR                                          |
| **25** | **Detektion u. Reaktion**                   |     Max     |  [ ]   | Netzwerk-Analyse                                      |
| **26** | **Incident Response**                       |     Max     |  [ ]   | Isolation & Bereinigung                               |
| **27** | **Zusammenfasssung**                        |     Max     |  [ ]   | Key Takeaways                                         |
| **28** | **Zukünftige Herausforderungen**            |     Max     |  [ ]   | KI, Quantencomputing                                  |

---

## Allgemeine Notizen & Skripte

### Vorbereitung für die Live-Demo (Checkliste)

- [ ] Laptop 1 (Angreifer) und Laptop 2 (Opfer) 
- [ ] IP-Adresse in `malware_agent/src/main.rs` aktualisiert?
- [ ] `./scripts/start_demo.sh` (oder `start_all.sh`) ausgeführt?
- [ ] Ist der `loot` Ordner auf dem C2-Server leer (für den Beweis)?
- [ ] Windows Defender auf Opfer-VM deaktiviert (falls Windows)?

## Mögliche Fragen

### Architektur & Agent-Design (Rust)

- Warum haben Sie sich für eine modulare Struktur im Rust-Agenten entschieden?

  > Antwort: Wartbarkeit und Trennung der Verantwortlichkeiten (Separation of Concerns). evasion.rs kümmert sich nur um den Selbstschutz, crypto.rs nur um den Schaden. Das erleichtert das Testen und Erweitern.

- Sie nutzen statisches Linken für Windows (-static). Welche Vor- und Nachteile hat das?

  > Antwort: Vorteil: Die Malware läuft auf jedem Windows-PC sofort ("Standalone"), ohne dass der User DLLs (wie libgcc) installieren muss. Nachteil: Die Dateigröße wächst (von wenigen KB auf einige MB).

- Wie stellen Sie sicher, dass bei einem Absturz während der Verschlüsselung keine Daten verloren gehen?

  > Antwort: Durch atomare Dateioperationen in crypto.rs. Wir schreiben erst in eine .enc_temp Datei. Erst wenn das erfolgreich war, benennen wir sie um (rename) und löschen das Original. So gibt es nie den Zustand "Datei halb verschlüsselt und kaputt".

- Warum nutzen Sie AES-256-CTR (Stream Cipher) und nicht CBC oder GCM?

  > Antwort: CTR (Counter Mode) macht aus der Blockchiffre eine Stromchiffre. Das ist extrem schnell und erlaubt wahlfreien Zugriff (Random Access). Zudem ist Encryption und Decryption mathematisch identisch (XOR), was den Code vereinfacht.

- Das "Panic Mode" Feature (Browser/Wallpaper) läuft parallel. Wie verhindern Sie, dass es die Verschlüsselung blockiert?
  > Antwort: Rusts Threading-Modell. Der Panic-Loop läuft in einem separaten std::thread::spawn, während der Hauptthread weiter Dateien verschlüsselt.

### Netzwerk & C2-Kommunikation (Python/Protokoll)

- Warum nutzen Sie rohe TCP-Sockets statt HTTP/REST für den C2-Server?

  > Antwort: Um "unter dem Radar" zu bleiben und Overhead zu vermeiden. HTTP erzeugt viel Header-Datenverkehr und Logs. Rohes TCP ist schlanker und wir haben volle Kontrolle über das Protokoll.

- Wie funktioniert die Daten-Exfiltration technisch in Ihrem Protokoll?

  > Antwort: Wir lesen die Datei binär, kodieren sie in Base64 (um sie über das textbasierte TCP-Protokoll zu senden) und schicken sie als String EXFIL_DATA:<filename>:<base64>. Der Server parst diesen String und dekodiert ihn zurück.

- Was passiert, wenn die Verbindung zum C2-Server abbricht?

  > Antwort: Der Agent besitzt eine Retry-Loop in network.rs. Er versucht in Abständen (z.B. alle 5 Sekunden), die Verbindung wiederherzustellen. Die Malware beendet sich nicht einfach.

- Ist die Kommunikation zwischen Agent und C2 verschlüsselt?
  > Antwort: Ehrlich sein: "In dieser Demo-Version senden wir Klartext über TCP. In einer echten Umgebung würde man TLS nutzen oder die TCP-Pakete selbst nochmal verschlüsseln (z.B. AES), um Network-Monitoring zu entgehen."

### Evasion & Infektionswege

- Ihre Evasion-Technik prüft RAM und CPU. Können Analysten das nicht einfach fälschen?

  > Antwort: Ja, das ist ein Katz-und-Maus-Spiel. Deshalb haben wir zusätzlich einen Timing-Check eingebaut. Wir messen die reale Zeit eines sleep()-Befehls. Wenn die Sandbox die Zeit "vorspult" (Fast-Forward), erkennen wir die Diskrepanz und beenden uns.

- Warum nutzen Sie ein .deb Paket für Linux statt einer einfachen Binary?

  > Antwort: Weil Linux heruntergeladene Binaries standardmäßig das "Ausführen"-Recht entzieht (chmod -x). Ein .deb Paket wirkt vertrauenswürdig (Social Engineering), nutzt den grafischen Installer und kann über das postinst-Skript Befehle (sogar als Root) ausführen.

- Wie unterscheidet der "Smart Endpoint" zwischen den Betriebssystemen?

  > Antwort: Der Python-Webserver analysiert den User-Agent Header des HTTP-Requests. Enthält er "Windows", liefern wir die .exe. Enthält er "Linux" oder "X11", liefern wir das .deb.

- Der Agent liegt als security-update getarnt vor. Wie verhindert man, dass der Nutzer den Prozess im Task-Manager findet?
  > Antwort: Unter Linux nutzen wir daemonize (Double Fork), um uns vom Terminal zu lösen. Unter Windows nutzen wir #![windows_subsystem = "windows"], um kein Fenster zu zeigen. Um im Task-Manager unsichtbar zu sein, bräuchte man Rootkit-Techniken (Process Hollowing), was den Rahmen dieser Demo sprengt.

### Infrastruktur & Deployment

- Sie nutzen Pinggy/Localtunnel. Warum zwei verschiedene Tunnel-Dienste?

  > Antwort: Wegen Protokoll-Unterschieden. Localtunnel ist für HTTP optimiert (Delivery Server, PDF-Download). Für den C2-Server brauchten wir aber rohes TCP, was Pinggy (im TCP-Modus) besser unterstützt, ohne den Datenstrom zu verändern.

- Das start_demo.sh Skript wirkt komplex. Was genau automatisiert es?

  > Antwort: Es ist ein Orchestrator. Es startet die Tunnel, parst die dynamischen URLs, injiziert diese URLs direkt in den Source Code (Rust & Python), kompiliert die Malware neu und startet die Server. Das eliminiert menschliche Fehler bei der Live-Demo.

- Wo wird der kryptographische Schlüssel (rescue.key) gespeichert?
  > Antwort: Er wird lokal neben der Malware generiert und gespeichert. In einem echten Angriff würde man den Key nur im Speicher halten und an den C2 senden (und dann lokal löschen). Für Bildungszwecke speichern wir ihn lokal, um im Fehlerfall die Daten retten zu können.

### Sicherheit & Gegenmaßnahmen

- Würde ein modernes EDR (Endpoint Detection & Response) System diese Malware erkennen?

  > Antwort: Wahrscheinlich ja, aber nicht durch Signaturen (da selbst kompiliert), sondern durch Verhaltensanalyse. Das gleichzeitige Öffnen hunderter Dateien (encrypt) und das Ändern des Wallpapers sind typische "Heuristic Flags" für Ransomware.

- Wie könnte man das "Phishing PDF" technisch erkennen?

  > Antwort: Durch Analyse der Links im PDF. Der Link zeigt auf eine dynamische Tunnel-Domain (pinggy.io / loca.lt), was in Firmennetzwerken oft geblockt ist. Außerdem passt der Link nicht zum Absender der angeblichen Rechnung.

- Warum funktioniert die Demo auch ohne Administrator-Rechte (unter Windows)?
  > Antwort: Weil Ransomware meistens nur die User-Daten (Dokumente, Bilder) verschlüsseln will. Dafür braucht man keine Admin-Rechte, da der User Schreibzugriff auf seine eigenen Dateien hat. Das macht Ransomware so gefährlich.

---

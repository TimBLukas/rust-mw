I. Einführung und Definition

- Definition: Ransomware ist eine Untergruppe von Malware, die entwickelt wurde, um den Zugriff des Benutzers auf sein System oder seine Daten zu beschränken oder zu verwehren, bis ein gefordertes Lösegeld gezahlt wird

​	Quellen: Age of Ransomware, presentation.pdf



- Historie und Entwicklung

​	Erster Auftritt: 1989 (AIDS Trojan) Quellen: Age of Ransomware, presentation.pdf

​	Wiederaufleben 2005, angetrieben durch die Verbreitung des INternets und Kryptowährungen, die 	anonyme Zahlungen ermöglichen

​	2017 Wanna Cry Ausbruch lenkte die Aufmerksamkeit stark auf die die Gefahr und Rentabilität von 	Ransomware



- Finanzielle Auswirkungen: Geschätzten weltweiten Schäden durch Ransomware stiegen von 5 Milliarden in 2017 auf voraussichtlich 42 Milliarden in 2024

​	Quelle: Age of Ransomware



- Aktuelle BEdrohungslandschaft (ENISA 2024)

​	Ransomware ist eine der Hauptbedrohungen (Prime Threats)

​	Vorfälle stabilisieren sich auf hohem Volumen (über 1000 Forderungen pro Quartal)



II. Taxonomie und Arten von Ransomware 

1. Kryptografische Ransomware (crypto-Ransomware): Verschlüsselt Benutzerdateien (Dokumente, Bilder), ohne die grundlegenden Computerfunktionen zu stören. Verschlüsselungen wie AES oder RSA machen eine Wiederherstellung oft irreversibel

​	Quelle: Age of Ransomware

2. Sperr-Ransomware (Locker-Ransomware): Sperrt Benutzer aus ihren Systemen aus (z.B. Bildschirmsperre)

   Quelle: Age of Ransomware, presentation



Moderne Erpressungsformen:

- Leakware / Doxware: Droht mit der Veröffentlichung sensibler Benutzerdaten, falls das Lösegeld nicht gezahlt wird.
  - Quellen: Age of Ransomware
- Double und Triple Extortion: KOmbination aus Verschlüsselung, Datenexfiltration und der Drohung die Daten zu veröffentlichen, um den zahlungsdruck zu erhöhen
  - Quellen: ENISA, presentation
- Ransomware-as-a-Service (RaaS): Vertriebsmodell, das Cyberkriminellen die Miete von Ransomware-Angriffen (bzw. Software) ermöglicht, selbst wenn sie keine Fähigkeiten zur Entwicklung haben
  - Wichtige Varianten: LockBit (dominiert global und EU-weit, bekannt für schnelle Verschlüsselung), Maze (führt Double Extortion ein), Ryuk.
  - Quellen: presentation, ENISA, Age of Ransomware



III. Angriffsphasen

1. Distribution: Verbreitung der Malware auf das Zielsystem (z.B. PC, Mobilgerät)
   - Quellen: Age of Ransomware, presentation
2. Infection (Infektion): Installation und Start das Ransomware-Prozesses
   - Quellen: Age of Ransomware
3. Staging: Etabliert Persistenz und beginnt die Kommunikation mit dem Command and Control (C&C oder C2 Server)
   - Quellen: Age of Ransomware
4. Scanning: Durchsucht lokale Laufwerke, Netzwerkfreigaben und Cloud Speicher nach Daten, die verschlüsselt werden können.
   - Quellen: Age of Ransomware
5. Encryption (Verschlüsselung): Verschlüsselt die Dateien, oft unter Verwendung starker Algorithmen wie AES und RSA.
   - Quellen: Age of Ransomware
6. Payment (Zahlung): Lösegeldforderung wird angezeigt, Ziel ist die Erpressung
   - Quellen: Age of Ransomware, presentation



IV Angriffsvektoren und Ziele

- Häufigste Vektoren:
  - Phishing-E-Mails: Bleiben der am häufigst genutzte Infektionsvektor, oft mit bösartien Anhängen oder Links.
    - Quellen: Age of Ransomare, presentation
  - Remote Desktop Protocol (RDP)
    - Quellen: Age of Ransomware
  - Software-Schwachstellen: Ausnutzung von ungepatchten Sicherheitslücken.
    - Quellen: Age of Ransomware, presentation
- Ziele (Sektoren):
  - Industrie und Fertigung (Manufacturing): Am häufigsten Angegriffen (21.78% der Vorfälle in einem untersuchten Datensatz)
    - Quelle: ENISA
  - Transportsektor: Das zweithäufigste Ziel in den ENISA Daten (21,05%)
    - Quelle ENISA
  - kritische Infrastrukturen: Zunemendes Targeting von Transport- und Energiesektoren
    - Quellen ENISA, Presentation
  - Öffentliche Verwaltung (PUblic Admin), Gesunheitswesen (Health), Bankwesen/Finanzen (Banking/Finance): Gehören ebenfalls zu den am stärksten betroffenene Sektoren
    - Quellen: Enisa, presentation
- Moderne Entwicklungen
  - AI-Einsatz: Einsatz von KI-Tools durch Cyberkriminelle für Phishing Kampagnen und das Umgehen von Detektionsmechanismen
    - Quelle ENISA
  - Rootkit Fashion: Verwendung von Rootkit-Technologien, um sich zu verstecken und die Ausführung zu verzögern.
    - Quelle: presentation



V Gegenmaßnahmen und Forschung

- Forschungslandschaft:
  - Großteil der akademischen Forschung konzentriert sich auf die Detektion von Ransomware (72,8%der Studien).
    - Quelle Age of Ransomwaree
  - Die meisten Detektionssysteme verwenden Machine Learning Ansätze (ML),da diese eine hohe Genauigkeit bieten und unbekannte Varianten erkennen können.
    - Quelle: Age of Ransomware, presentation
  - Häufig genutze Analysemerkmale sind API-Aufrufe, Datei-/Verzeichnisaktivitäten und Netzwerkverkehr
    - Age of Ransomware, presentation
  - Analyseansätze:
    - Statistische Analyse: Untersuchung der Binärdatei ohne Ausführung
      - Quelle: Age of Ransomware, presentation
    - Dynamische Analyse: Beobachtung der Verhaltens in einer isolierten Umgebung (Sandbox)
      - Quelle: Age of Ransomware, presentation
  - Präventions- und Minderungsstrategien (Prevention and Mitigation):
    - Echtzeit-Schutz: Entwicklung von Systemen mit Echtzeit Schutzfähigkeiten und Identifizierung von Zero-Day-Ransomware ist eine entscheidende zukünftige Forschungsrichtung
      - Quelle: Age of Ransomware
    - Abwehr: Techniken umfassen die Erzwingung von Dateizugriffsrichtlinien und die Anwendung der Moving Target Defense (MTD)
      - Quelle: Age of Ransomware, presentation
    - Wiederherstellung: Nutzung von key-Escrow-Mechanismen zur Erfassung der Verschlüsselungsschlüssel oder Wiederherstellung der daten über Cloud Backups oder spezielle SSD-Funktionen
      - Quelle: Age of Ransomware, presentation
    - Netzwerkbasierte Detektion
      - Ein Ansatz der Früherkennung basiert auf der Analyse des Netzwerk-Traffic (z.B. SMB-Protokoll) zu freigegebenen Netzwerklaufweren
        - Quelle: Ransomware_early_detection
      - REDFISH: erkennt Ransomware durch das Monitoring von Verhaltensmustern, wie schnelles Lesen, Schreiben und Löschen von Dateien.
        - Quelle: Ransomware Early detection
      - Das System kann 99% der Fälle erkennen, bevor 10 Dateien verloren gehen, und die verlorenen Dateien können oft aus dem aufgezeichneten Netzwerk Traffic wiederhergestellt werden (near 0 loss szenario)
        - Quelle: Ransomware early detection


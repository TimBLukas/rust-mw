# Deployment

1. Server Starten (`c2_server/server.py`)
2. ssh -p 443 -o PubkeyAuthentication=no -R0:localhost:4444 <tcp@a.pinggy.io>
3. Um den prozess wieder zu löschen: `pgrep -a rust` und dann `pkill -f rust`

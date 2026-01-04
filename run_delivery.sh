#!/bin/bash

# ==========================================
#  1. DELIVERY SERVER & TUNNEL (SSH Version)
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DELIVERY_DIR="$ROOT_DIR/delivery/DbD-Site"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }

if [ ! -d "$DELIVERY_DIR" ]; then
  echo -e "${RED}[!] Verzeichnis nicht gefunden: $DELIVERY_DIR${NC}"
  exit 1
fi

cd "$DELIVERY_DIR" || exit

cleanup() {
  echo ""
  print_status "Beende Delivery Server..."
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null
  fi
  exit
}
trap cleanup SIGINT

# 1. Python Server starten
print_status "Starte Python Delivery Server (Port 3000)..."
python3 server.py &
SERVER_PID=$!

sleep 2

# 2. SSH Tunnel starten (localhost.run)
print_success "Server läuft (PID: $SERVER_PID)."
print_status "Starte Tunnel via localhost.run..."
print_status "Kopiere die URL unten (https://....localhost.run) für das PDF!"
echo "---------------------------------------------------"

# StrictHostKeyChecking=no verhindert die "Are you sure?" Frage bei SSH
ssh -o StrictHostKeyChecking=no -R 80:localhost:3000 nokey@localhost.run

cleanup

#!/bin/bash

# ==========================================
#  2. C2 SERVER START
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C2_DIR="$ROOT_DIR/c2_server"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }

if [ ! -d "$C2_DIR" ]; then
  echo -e "${RED}[!] Verzeichnis nicht gefunden: $C2_DIR${NC}"
  exit 1
fi

cd "$C2_DIR" || exit

print_status "Starte C2 Server (Attacker Control)..."
print_status "Stelle sicher, dass deine IP in der Rust-Config korrekt ist!"
echo "---------------------------------------------------"

# Ggf. Requirements installieren (optional, auskommentiert)
# if [ -f "requirements.txt" ]; then pip install -r requirements.txt; fi

python3 server.py

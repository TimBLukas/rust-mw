# ==========================================
#  RUST-MW Docker Build Environment
# ==========================================

FROM rust:1.85-bookworm

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    openssh-client \
    mingw-w64 \
    gcc-mingw-w64-x86-64 \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Windows Cross-Compile Target
RUN rustup target add x86_64-pc-windows-gnu

# Arbeitsverzeichnis
WORKDIR /app

# Python Dependencies (für C2 und Delivery Server)
COPY c2_server/requirements.txt /tmp/c2_requirements.txt
COPY delivery/pdf_phishing/requirements.txt /tmp/pdf_requirements.txt

RUN pip3 install --break-system-packages -r /tmp/c2_requirements.txt || true
RUN pip3 install --break-system-packages -r /tmp/pdf_requirements.txt || true

# Startup Script
COPY scripts/docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ports
EXPOSE 4444 8080

ENTRYPOINT ["/entrypoint.sh"]

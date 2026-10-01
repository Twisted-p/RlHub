"""RL Hub desktop host: one local origin for the UI and Tracker service."""
from __future__ import annotations

import ctypes
import logging
import json
from io import BytesIO
import mimetypes
import os
import time
from pathlib import Path
import sys
from threading import Thread
from http.server import ThreadingHTTPServer
from urllib.parse import unquote, urlparse
from uuid import uuid4

from tracker_proxy import TrackerProxyHandler
from mmr_provider import fetch_rank_profile
from performance_service import PerformanceService
from overlay_service import OverlayService
from native_overlay import NativeOverlay, render_card

# The default origin stays stable; smoke tests can isolate their local service.
APP_PORT = int(os.environ.get("RL_HUB_PORT", "18765"))
ASSET_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
UI_FILES = {
    "index.html", "dashboard.html", "garage.html", "training.html", "profile.html",
    "script.js", "styles.css", "desktop-runtime.js", "App Logo.png", "performance.html", "performance.js",
    "assets/rlhub-intro.mp4",
    "overlay.html", "overlay-settings.js",
}


class DesktopHandler(TrackerProxyHandler):
    source_name = "MMR-tjenesten"

    def fetch_profile(self, platform: str, gamertag: str, player_id: str = "") -> dict:
        profile = fetch_rank_profile(platform, gamertag, player_id)
        overlay = getattr(self.server, "overlay", None)
        if overlay:
            overlay.set_profile(profile, {"platform": platform, "gamertag": gamertag})
        return profile

    def end_headers(self) -> None:
        # The standalone UI and API share an origin; do not enable wildcard CORS.
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        super(TrackerProxyHandler, self).end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond_json(200, {"status": "ok", "app": "rl-hub-desktop"})
            return
        if parsed.path == "/api/profile":
            super().do_GET()
            return
        if parsed.path == "/api/overlay":
            overlay = getattr(self.server, "overlay", None)
            self.respond_json(200 if overlay else 503, overlay.view() if overlay else {"error": "Overlayet er ikke startet."})
            return
        if parsed.path == "/api/overlay/frame":
            overlay = getattr(self.server, "overlay", None)
            if not overlay:
                self.respond_json(503, {"error": "Overlayet er ikke startet."})
                return
            from PIL import Image
            overlay.gamebar_seen_at = time.monotonic()
            view = overlay.view()
            shown = view["settings"].get("renderer") == "gamebar" and (view["preview"] or (view["settings"]["enabled"] and view["phase"] != "hidden"))
            frame = render_card(view, ASSET_ROOT / "App Logo.png") if shown else Image.new("RGBA", (440, 250))
            buffer = BytesIO()
            frame.save(buffer, format="PNG")
            content = buffer.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if parsed.path == "/api/performance":
            service = getattr(self.server, "performance", None)
            if service:
                self.respond_json(200, service.snapshot())
            else:
                self.respond_json(503, {"error": "Kampoppsummeringer er ikke startet."})
            return
        name = unquote(parsed.path).lstrip("/") or "index.html"
        if name not in UI_FILES:
            self.respond_json(404, {"error": "Fant ikke siden."})
            return
        try:
            content = (ASSET_ROOT / name).read_bytes()
        except OSError:
            self.respond_json(404, {"error": "Fant ikke filen."})
            return
        if name.endswith(".html"):
            content = content.replace(
                b'<script src="./script.js"></script>',
                b'<script src="./desktop-runtime.js"></script>\n'
                b'    <script src="./script.js"></script>',
            )
        if name == "desktop-runtime.js":
            content = (
                f'window.RL_HUB_SESSION = "{self.server.session_id}";\n'.encode()
                + content
            )
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if name.endswith(".js"):
            content_type = "text/javascript"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        try:
            self.wfile.write(content)
        except ConnectionError:
            # A skipped intro or page navigation may cancel an asset download.
            pass

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in ("/api/performance/setup", "/api/overlay/settings", "/api/overlay/preview", "/api/overlay/profile", "/api/overlay/reset"):
            self.respond_json(404, {"error": "Fant ikke endepunktet."})
            return
        expected_origin = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Origin") != expected_origin:
            self.respond_json(403, {"error": "Endringer må gjøres fra RL Hub."})
            return
        if path.startswith("/api/overlay/"):
            overlay = getattr(self.server, "overlay", None)
            if overlay is None:
                self.respond_json(503, {"error": "Overlayet er ikke startet."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= 32768:
                    raise ValueError("Ugyldig forespørsel.")
                payload = json.loads(self.rfile.read(length)) if length else {}
                if not isinstance(payload, dict):
                    raise ValueError("Ugyldig forespørsel.")
                if path.endswith("/settings"):
                    overlay.configure(payload)
                elif path.endswith("/profile"):
                    overlay.set_profile(payload.get("profile"), payload.get("lookup"))
                elif path.endswith("/preview"):
                    overlay.preview()
                else:
                    overlay.reset_session()
                self.respond_json(200, overlay.view())
            except (ValueError, TypeError):
                self.respond_json(400, {"error": "Kunne ikke lagre overlay-innstillingene."})
            return
        service = getattr(self.server, "performance", None)
        if service is None:
            self.respond_json(503, {"error": "Kampoppsummeringer er ikke startet."})
            return
        try:
            self.respond_json(200, service.setup())
        except (OSError, ValueError):
            self.respond_json(400, {"error": "Kunne ikke aktivere kampoppsummeringer. Start Rocket League én gang, lukk spillet, og prøv igjen. Kontroller at appen kan skrive til spillets innstillinger."})


def start_server(port: int = APP_PORT, performance: PerformanceService | None = None, overlay: OverlayService | None = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), DesktopHandler)
    server.daemon_threads = True
    server.session_id = uuid4().hex
    server.performance = performance
    server.overlay = overlay
    Thread(target=server.serve_forever, name="rl-hub-service", daemon=True).start()
    return server


def main() -> None:
    data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "RL Hub"
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(data_dir / "desktop.log"), level=logging.WARNING)
    server = None
    performance = None
    native_overlay = None
    try:
        import webview

        performance = PerformanceService(data_dir)
        overlay = OverlayService(data_dir, performance)
        server = start_server(performance=performance, overlay=overlay)
        performance.start()
        native_overlay = NativeOverlay(overlay, ASSET_ROOT / "App Logo.png")
        native_overlay.start()
        webview.create_window(
            os.environ.get("RL_HUB_WINDOW_TITLE", "RL Hub"), f"http://127.0.0.1:{APP_PORT}/index.html",
            width=1180, height=820, min_size=(980, 680),
            background_color="#10131d",
        )
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(data_dir / "WebView"))
    except Exception as error:
        logging.exception("RL Hub kunne ikke starte")
        if isinstance(error, OSError) and getattr(error, "winerror", None) == 10048:
            message = "RL Hub kjører allerede, eller appens lokale port er opptatt."
        else:
            message = "RL Hub kunne ikke starte. Se desktop.log i %LOCALAPPDATA%\\RL Hub.\n\n" + str(error)
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, message, "RL Hub", 0x10)
        else:
            print(message, file=sys.stderr)
    finally:
        if native_overlay is not None:
            native_overlay.stop()
        if performance is not None:
            performance.stop()
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()

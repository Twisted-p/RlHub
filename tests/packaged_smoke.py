"""Check the shipped executable using an isolated user-data directory."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import socket
from uuid import uuid4
from urllib.request import urlopen

from PIL import ImageGrab

root = Path(__file__).resolve().parents[1]
executable = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "dist" / "RL Hub.exe"
user32 = ctypes.windll.user32
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

with tempfile.TemporaryDirectory(prefix="rl-hub-packaged-", ignore_cleanup_errors=True) as storage:
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    title = "RL Hub packaged test " + uuid4().hex
    environment = dict(os.environ, LOCALAPPDATA=storage, RL_HUB_PORT=str(port), RL_HUB_WINDOW_TITLE=title)
    process = subprocess.Popen([str(executable)], env=environment,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    handle = None
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            handle = user32.FindWindowW(None, title)
            if handle:
                with urlopen(origin + "/health", timeout=2) as response:
                    assert json.load(response)["app"] == "rl-hub-desktop"
                break
            assert process.poll() is None, "Executable exited before showing its window"
            time.sleep(0.25)
        else:
            raise AssertionError("Packaged app did not show its window")
        time.sleep(2)
        rect = wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.byref(rect))
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(root / "build" / "desktop-intro-preview.png")
        time.sleep(5)  # Wait for the intro to finish and the first page paint.
        assert process.poll() is None
        for page in ["index", "dashboard", "garage", "training", "profile", "performance"]:
            with urlopen(f"{origin}/{page}.html", timeout=2) as response:
                assert b"desktop-runtime.js" in response.read()
        with urlopen(origin + "/api/performance", timeout=2) as response:
            assert isinstance(json.load(response)["matches"], list)
        with urlopen(origin + "/assets/rlhub-intro.mp4", timeout=2) as response:
            assert response.headers.get("Content-Type") == "video/mp4"
            assert b"ftyp" in response.read(32)
        rect = wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.byref(rect))
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(root / "build" / "desktop-preview.png")
        user32.PostMessageW(handle, 0x0010, 0, 0)  # Normal window close.
        process.wait(timeout=15)
        assert process.returncode == 0
        try:
            urlopen(origin + "/health", timeout=1)
        except OSError:
            pass
        else:
            raise AssertionError("Local service remained running after close")
        print("Packaged executable: window, assets, service, shutdown OK")
    finally:
        if process.poll() is None:
            if handle:
                user32.PostMessageW(handle, 0x0010, 0, 0)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)

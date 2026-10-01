"""Test settings, native window and synthetic live match data in isolated storage."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from desktop_app import start_server
from performance_service import PerformanceService
from overlay_service import OverlayService
from native_overlay import NativeOverlay
from test_performance import STATE, END, PLAYER
import webview

root = Path(__file__).resolve().parents[1]
storage = tempfile.TemporaryDirectory(prefix="rlhub-overlay-ui-", ignore_cleanup_errors=True)
performance = PerformanceService(Path(storage.name), root=Path(storage.name), local_player={"name": "Player A", "playerId": PLAYER})
service = OverlayService(Path(storage.name), performance)
native = NativeOverlay(service, root / "App Logo.png")
server = start_server(0, performance, service)
window = webview.create_window("RL Hub Overlay UI test", f"http://127.0.0.1:{server.server_port}/overlay.html", width=1180, height=820)
failures = []

def wait_for(expression):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            if window.evaluate_js(expression):
                return
        except Exception:
            pass
        time.sleep(.1)
    raise AssertionError(expression)

def exercise():
    try:
        native.start()
        assert service.native_ready, service.native_error
        wait_for("overlayFieldsLoaded")
        assert window.evaluate_js("document.querySelectorAll('.nav-link.active').length") == 1
        assert window.evaluate_js("document.querySelector('.nav-link.active').textContent") == "Overlay"
        assert not window.evaluate_js("overlayFields.showInMatch.checked")
        window.evaluate_js("overlayFields.showInMatch.checked=true; overlayFields.position.value='top-right'; overlayForm.requestSubmit()")
        wait_for("overlayFeedback.textContent.includes('lagret')")
        assert service.settings["showInMatch"]
        assert service.settings["position"] == "top-right"
        window.evaluate_js("document.getElementById('overlay-preview').click()")
        wait_for("overlayFeedback.textContent.includes('20 sekunder')")
        deadline = time.monotonic() + 5
        while not service.visible and time.monotonic() < deadline:
            time.sleep(.1)
        assert service.visible, service.native_error
        user = c.WinDLL("user32")
        user.GetForegroundWindow.restype = w.HWND
        assert user.GetForegroundWindow() != native.hwnd
        user.GetWindowLongPtrW.argtypes = [w.HWND, c.c_int]
        user.GetWindowLongPtrW.restype = c.c_ssize_t
        style = user.GetWindowLongPtrW(native.hwnd, -20)
        assert style & 0x20 and style & 0x80000 and style & 0x8000000 and style & 0x8
        (root / "build").mkdir(exist_ok=True)
        user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
        rect = w.RECT()
        user.GetWindowRect(native.hwnd, c.byref(rect))
        time.sleep(.5)
        screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), include_layered_windows=True)
        screenshot.save(root / "build/overlay-native-ui-preview.png")
        red, green, blue = screenshot.getpixel((screenshot.width // 2, 1))[:3]
        assert green > red + 40, "The native card's teal border was not rendered on screen"
        performance.ingest(STATE)
        assert service.view()["phase"] == "match"
        assert service.view()["player"]["goals"] == 2
        service.configure({"showInMatch": False})
        assert service.view()["phase"] == "hidden"
        performance.ingest(END)
        assert service.view()["phase"] == "post-match"
        assert service.view()["result"] == "Seier"
        user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        enabled = service.settings["enabled"]
        user.PostMessageW(native.hwnd, 0x0312, 1, 0)
        deadline = time.monotonic() + 3
        while service.settings["enabled"] == enabled and time.monotonic() < deadline:
            time.sleep(.1)
        assert service.settings["enabled"] != enabled
        print("Overlay UI and native window: settings, preview, click-through, no focus, match toggle, completed match and hotkey OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(error, file=sys.stderr, flush=True)
    finally:
        native.stop()
        window.destroy()

try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(storage.name) / "webview"))
finally:
    native.stop()
    server.shutdown()
    server.server_close()
    storage.cleanup()
sys.exit(1 if failures else 0)

"""Verify Performance in WebView2 with simulated official Stats API events."""
import ctypes
from ctypes import wintypes
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
from performance_service import PerformanceService
from test_performance import STATE, END, PLAYER
from PIL import ImageGrab
import webview

root = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory(prefix="rl-hub-performance-test-", ignore_cleanup_errors=True)
storage = Path(temporary.name)
config = storage / "game/TAGame/Config/DefaultStatsAPI.ini"
config.parent.mkdir(parents=True)
config.write_text("[TAGame.MatchStatsExporter_TA]\nPort=49123\nWebPort=49124\nPacketSendRate=0\n")
service = PerformanceService(storage / "data", root=storage / "game", local_player={"name": "Player A", "playerId": PLAYER})
server = start_server(0, performance=service)
window = webview.create_window("RL Hub Performance test", f"http://127.0.0.1:{server.server_port}/performance.html", width=1180, height=820)
failures = []


def wait_for(expression):
    deadline = time.monotonic() + 20
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
        wait_for("typeof performanceData !== 'undefined' && performanceData !== null")
        assert window.evaluate_js("performanceDetail.innerText.includes('Ingen kamper lagret')")
        assert window.evaluate_js("document.querySelector('.nav-link.active').textContent") == "Performance"
        window.evaluate_js("performanceEnable.click()")
        wait_for("performanceSetup.hidden && performanceStatus.innerText.includes('Start Rocket League på nytt')")
        service.ingest({"Event": "MatchCreated", "Data": {"MatchGuid": "test-match"}})
        service.ingest(STATE)
        service.ingest(END)
        wait_for("document.querySelectorAll('.performance-metrics .profile-stat').length === 6")
        assert window.evaluate_js("performanceDetail.innerText.includes('Seier')")
        assert window.evaluate_js("performanceDetail.innerText.includes('40%')")
        assert window.evaluate_js("document.querySelectorAll('.performance-table tbody tr').length") == 2
        assert window.evaluate_js("document.querySelectorAll('[data-match-id]').length") == 1
        time.sleep(1)
        user32 = ctypes.windll.user32
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND
        handle = user32.FindWindowW(None, "RL Hub Performance test")
        rect = wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.byref(rect))
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(root / "build/performance-preview.png")
        print("Performance UI: setup, completed match, personal stats, history and scoreboard OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(storage / "webview"))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

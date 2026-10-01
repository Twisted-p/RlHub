"""Exercise the splash with real WebView2 video playback in isolated storage."""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
import webview

temporary = tempfile.TemporaryDirectory(prefix="rlhub-splash-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub splash check", origin, width=1180, height=820)
failures = []

def wait_for(expression, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if window.evaluate_js(expression):
                return
        except Exception:
            pass
        time.sleep(.05)
    raise AssertionError(expression)

def exercise():
    try:
        wait_for("typeof initSplash === 'function'")
        print(window.evaluate_js("({motion:matchMedia('(prefers-reduced-motion: reduce)').matches,session:sessionStorage.getItem('rlhub-intro-shown'),video:!!document.querySelector('.splash-video'),ready:document.body.classList.contains('app-ready')})"), flush=True)
        wait_for("!!document.querySelector('.splash-video')")
        wait_for("document.querySelector('.splash-video').currentTime > .1")
        assert window.evaluate_js("document.querySelector('.splash-video').muted")
        duration = window.evaluate_js("document.querySelector('.splash-video').duration")
        assert 0 < duration <= 7, duration
        wait_for("document.body.classList.contains('app-ready')", 8)
        assert window.evaluate_js("document.querySelector('.splash-overlay').inert")
        window.evaluate_js("location.href='./index.html'")
        wait_for("document.querySelector('.splash-overlay').hidden && document.body.classList.contains('app-ready')")
        window.evaluate_js("window.RL_HUB_SESSION='new-app-launch'; splashOverlay.hidden=false; splashOverlay.inert=false; splashOverlay.classList.remove('is-exiting'); document.body.classList.remove('app-ready'); initSplash()")
        wait_for("!!document.querySelector('.splash-skip')")
        window.evaluate_js("document.querySelector('.splash-skip').click()")
        wait_for("document.body.classList.contains('app-ready')")
        window.evaluate_js("sessionStorage.removeItem('rlhub-intro-shown'); splashOverlay.inert=false; splashOverlay.classList.remove('is-exiting'); document.body.classList.remove('app-ready'); initSplash()")
        wait_for("!!document.querySelector('.splash-video')")
        window.evaluate_js("document.querySelector('.splash-video').src='./missing.mp4'; document.querySelector('.splash-video').load()")
        wait_for("document.body.classList.contains('app-ready')")
        print(f"WebView2: unmodified startup ({duration:.2f}s), normal finish, navigation, new app session, skip and missing-video recovery OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(error, file=sys.stderr, flush=True)
    finally:
        window.destroy()

try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=temporary.name)
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

"""Exercise the actual WebView2 UI; run twice to check persisted storage."""
import argparse
import json
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import APP_PORT, start_server
import webview

parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=["write", "read"])
parser.add_argument("storage")
args = parser.parse_args()
server = start_server()
origin = f"http://127.0.0.1:{APP_PORT}"
window = webview.create_window("RL Hub test", origin + "/index.html", hidden=True, width=1180, height=820)
failures = []


def wait_for(expression):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if window.evaluate_js(expression):
                return
        except Exception:
            pass
        time.sleep(0.1)
    raise AssertionError(f"Timed out: {expression}")


def exercise():
    try:
        wait_for("typeof IS_STANDALONE !== 'undefined' && IS_STANDALONE")
        assert window.evaluate_js("document.querySelector('.nav-link').target") == ""
        if args.phase == "read":
            assert window.evaluate_js("localStorage.getItem('rlhub:smoke')") == "saved"
        else:
            window.evaluate_js("localStorage.setItem('rlhub:smoke', 'saved')")
        for page in ["dashboard", "garage", "training", "profile"]:
            window.load_url(origin + f"/{page}.html")
            wait_for(f"document.body.dataset.page === '{page}' && typeof IS_STANDALONE !== 'undefined' && IS_STANDALONE")
            assert window.evaluate_js("document.body.innerText.includes('Overwolf')") is False
            assert window.evaluate_js("state.overwolf.available") is False
            if page == "training" and args.phase == "write":
                window.evaluate_js("document.getElementById('timer-toggle').click()")
                time.sleep(1.2)
                window.evaluate_js("document.getElementById('timer-toggle').click()")
                assert window.evaluate_js("state.training.elapsedSeconds") >= 1
                window.evaluate_js("document.querySelector('.routine-item').click()")
            if page == "training" and args.phase == "read":
                assert window.evaluate_js("state.training.elapsedSeconds") >= 1
                assert window.evaluate_js("state.completedDrills.size") == 1
        wait_for("document.getElementById('profile-status').classList.contains('is-success')")
        assert window.evaluate_js("document.querySelectorAll('.rank-tile').length") == 0
        print(json.dumps({"phase": args.phase, "navigation": "ok", "tracker_service": "ok", "storage": "ok"}), flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


watchdog = threading.Timer(80, window.destroy)
watchdog.daemon = True
watchdog.start()
try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=args.storage)
finally:
    watchdog.cancel()
    server.shutdown()
    server.server_close()
sys.exit(1 if failures else 0)

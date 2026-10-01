"""Verify the access-denied UI without contacting Tracker or opening a browser."""
import sys
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
from tracker_proxy import TrackerUnavailableError
import webview

server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub error test", origin + "/profile.html", hidden=True)
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
    raise AssertionError(expression)


def exercise():
    try:
        wait_for("typeof IS_STANDALONE !== 'undefined' && IS_STANDALONE")
        assert window.evaluate_js("document.getElementById('tracker-profile-link').hidden")
        window.evaluate_js("profileGamertag.value = 'Twisted_p'; profileForm.requestSubmit()")
        wait_for("!profileSubmit.disabled && profileStatus.classList.contains('is-error')")
        assert window.evaluate_js("profileStatus.innerText.includes('kontoen')")
        assert window.evaluate_js("trackerProfileLink.hidden") is True
        assert window.evaluate_js("document.getElementById('player-id-field') === null")
        assert window.evaluate_js("state.profile.ranks.length") == 0
        window.evaluate_js("profileGamertag.value = ''; profileGamertag.dispatchEvent(new Event('input'))")
        assert window.evaluate_js("trackerProfileLink.hidden")
        print("Lookup UI: friendly error, no editable player-ID or TRN link OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    # WebView2 may keep cache files locked briefly after its window closes.
    with tempfile.TemporaryDirectory(prefix="rl-hub-error-test-", ignore_cleanup_errors=True) as storage:
        with patch("desktop_app.fetch_rank_profile", side_effect=TrackerUnavailableError("Fant ikke kontoen på denne maskinen.", "player_id_required")):
            webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=storage)
finally:
    server.shutdown()
    server.server_close()
sys.exit(1 if failures else 0)

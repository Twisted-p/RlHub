"""End-to-end rank lookup in the actual desktop UI, with isolated storage."""
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
import webview

gamertag = sys.argv[1]
server = start_server(0)
window = webview.create_window("RL Hub rank test", f"http://127.0.0.1:{server.server_port}/profile.html", hidden=True)
failures = []


def wait_for(expression, seconds=30):
    deadline = time.monotonic() + seconds
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
        import json
        wait_for("typeof IS_STANDALONE !== 'undefined' && IS_STANDALONE")
        window.evaluate_js(f"profileGamertag.value = {json.dumps(gamertag)}; profileForm.requestSubmit()")
        wait_for("!profileSubmit.disabled && state.profile.provider === 'kmdw'")
        ranks = window.evaluate_js("state.profile.ranks")
        assert len(ranks) == 3
        assert window.evaluate_js("document.querySelectorAll('.rank-tile').length") == 3
        assert window.evaluate_js("profileStatus.classList.contains('is-success')")
        assert window.evaluate_js("trackerProfileLink.hidden")
        assert window.evaluate_js("JSON.parse(localStorage.getItem('rlhub:lastProfileQuery')).playerId === state.profile.playerId")
        assert window.evaluate_js("document.getElementById('profile-player-id') === null")
        assert all(isinstance(rank["mmr"], int) for rank in ranks)
        print(json.dumps({"lookup": "live", "ranks": ranks, "saved_id": True, "TRN_opened": False}), flush=True)
    except Exception as error:
        failures.append(str(error))
        print(error, file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    with tempfile.TemporaryDirectory(prefix="rl-hub-rank-test-", ignore_cleanup_errors=True) as storage:
        webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=storage)
finally:
    server.shutdown()
    server.server_close()
sys.exit(1 if failures else 0)

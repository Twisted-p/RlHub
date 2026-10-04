"""Exercise the real profile form against an isolated, mocked rank provider."""
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_app import start_server
from mmr_provider import build_rank_profile
from overlay_service import OverlayService
import webview

temporary = tempfile.TemporaryDirectory(prefix='rl-hub-profile-', ignore_cleanup_errors=True)
overlay = OverlayService(temporary.name, None)
profile = build_rank_profile('epic', 'Audit Tester', 'test-profile',
    {'playlists': [{'id': 11, 'tier': 13, 'division': 2, 'mmr': 960}]})
server = start_server(0, overlay=overlay)
origin = f'http://127.0.0.1:{server.server_port}'
window = webview.create_window('RL Hub profile test', origin + '/profile.html', width=1180, height=820)
failures = []

def exercise():
    try:
        deadline = time.monotonic() + 20
        while not window.evaluate_js("document.querySelector('#profile-form') !== null"):
            assert time.monotonic() < deadline
            time.sleep(.1)
        with patch('desktop_app.fetch_rank_profile', return_value=profile) as lookup:
            window.evaluate_js("document.querySelector('#profile-gamertag').value='Audit Tester'; document.querySelector('#profile-form').requestSubmit()")
            while not window.evaluate_js("document.querySelector('#profile-status').textContent.includes('Viser rank og MMR for Audit Tester')"):
                assert time.monotonic() < deadline
                time.sleep(.1)
            lookup.assert_called_once_with('epic', 'Audit Tester', '')
        assert overlay.profile['name'] == 'Audit Tester'
        assert OverlayService(temporary.name, None).profile['ranks'][0]['mmr'] == 960
        print('Profile UI: same-origin POST, fetched rank rendering and persisted profile OK', flush=True)
    except Exception as error:
        failures.append(repr(error))
        print(repr(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()

try:
    webview.start(exercise, gui='edgechromium', private_mode=False, storage_path=str(Path(temporary.name)/'webview'))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

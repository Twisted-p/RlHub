"""Exercise coaching controls in real WebView2 with isolated session data."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
from test_readiness import CoachingTests
import webview

root = Path(__file__).resolve().parents[1]
fixture = CoachingTests()
fixture.setUp()
fixture.service.tick()
fixture.step(300)
for win in (True, False, True, False, True):
    fixture.add_match(win)
fixture.profile(912)
fixture.lobby()
server = start_server(0, performance=fixture.feed, overlay=fixture.overlay, readiness=fixture.service)
window = webview.create_window('RL Hub Readiness test', f'http://127.0.0.1:{server.server_port}/dashboard.html', width=1180, height=980)
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
        wait_for("document.getElementById('session-results').textContent.includes('3 seiere')")
        assert window.evaluate_js("document.getElementById('session-mmr').textContent.includes('+12 MMR')")
        assert window.evaluate_js("document.getElementById('session-training').textContent") == '5:00'
        assert window.evaluate_js("document.getElementById('session-coach-title').textContent") == '5 min pause, så 5 min trening'
        assert window.evaluate_js("document.querySelectorAll('#session-result-dots span').length") == 5
        assert window.evaluate_js("document.querySelectorAll('#session-stats .profile-stat').length") == 5
        window.evaluate_js("document.getElementById('session-break').click()")
        wait_for("document.getElementById('session-break').textContent === 'Pause pågår'")
        fixture.step(300)
        wait_for("document.getElementById('session-coach-title').textContent.includes('tren i 5 minutter')")
        fixture.feed.data.update(live={'training': True}, liveAge=0)
        fixture.step()
        fixture.step(300)
        wait_for("document.getElementById('session-coach-title').textContent === 'Én blokk om gangen'")
        fixture.lobby()
        for win in (False, False, False, True, False):
            fixture.add_match(win)
        wait_for("document.getElementById('session-coach-title').textContent === 'Ta 15 minutter pause'")
        # CSS custom readiness must follow the actual service score, not the old static ring.
        expected = fixture.service.tick()['readiness']
        assert window.evaluate_js("document.getElementById('session-ring').style.getPropertyValue('--readiness')") == f'{expected}%'
        # Capture the WebView surface independently of any fullscreen game.
        from System import Action
        tasks = {}
        def capture():
            tasks['capture'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Page.captureScreenshot', '{"format":"png","captureBeyondViewport":true}')
        window.native.webview.Invoke(Action(capture))
        deadline = time.monotonic() + 10
        while not tasks['capture'].IsCompleted and time.monotonic() < deadline:
            time.sleep(.1)
        (root / 'build/readiness-preview.png').write_bytes(base64.b64decode(json.loads(str(tasks['capture'].Result))['data']))
        window.evaluate_js("document.getElementById('session-reset').click()")
        wait_for("document.getElementById('session-results').textContent === 'Ingen kamper ennå'")
        assert window.evaluate_js("document.getElementById('session-score').textContent") == '—'
        assert window.evaluate_js("document.getElementById('session-focus-clock').textContent") == '90:00'
        print('Readiness UI: real training/MMR, last five, win/loss advice, pause/warmup and reset OK', flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui='edgechromium', private_mode=False, storage_path=str(fixture.path / 'webview'))
finally:
    server.shutdown()
    server.server_close()
    fixture.tearDown()
sys.exit(1 if failures else 0)

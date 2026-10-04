"""Verify Goals selections and persisted estimates in real WebView2."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
from test_goals import GoalsTests
import webview

root = Path(__file__).resolve().parents[1]
fixture = GoalsTests()
fixture.setUp()
server = start_server(0, overlay=fixture.overlay, goals=fixture.goals)
window = webview.create_window('RL Hub Goals test', f'http://127.0.0.1:{server.server_port}/goals.html', width=1380, height=980)
failures = []
webview_storage = tempfile.TemporaryDirectory(prefix='rl-hub-goals-webview-', ignore_cleanup_errors=True)


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
        wait_for("document.querySelectorAll('.goal-card').length === 3")
        wait_for("document.querySelectorAll('.goal-star-border .border-gradient-bottom').length === 3")
        from System import Action
        baseline = {}
        def enable_motion():
            baseline['task'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Emulation.setEmulatedMedia', '{"features":[{"name":"prefers-reduced-motion","value":"no-preference"}]}')
        window.native.webview.Invoke(Action(enable_motion))
        deadline = time.monotonic()+10
        while not baseline['task'].IsCompleted and time.monotonic()<deadline: time.sleep(.1)
        wait_for("getComputedStyle(document.querySelector('.border-gradient-bottom')).animationName === 'star-movement-bottom'")
        assert window.evaluate_js("getComputedStyle(document.querySelector('.border-gradient-bottom')).animationName") == 'star-movement-bottom'
        assert window.evaluate_js("document.querySelector('.nav-link.active').textContent") == 'Goals'
        assert window.evaluate_js("document.querySelectorAll('a[href=\"./goals.html\"]').length") == 1
        assert window.evaluate_js("document.querySelectorAll('#goal-2v2 option').length") == 23
        for mode in ('1v1', '2v2', '3v3'):
            window.evaluate_js(f"document.getElementById('goal-{mode}').value='16'; document.getElementById('goal-{mode}').dispatchEvent(new Event('change'))")
            wait_for(f"document.getElementById('goals-status').textContent === 'Målet for {mode} er lagret.'")
        assert window.evaluate_js("document.querySelector('[data-mode=\"1v1\"] .goal-metrics strong:last-of-type').textContent") == '95'
        assert window.evaluate_js("document.querySelector('[data-mode=\"2v2\"] .goal-message').textContent.includes('20 seiere')")
        fixture.profile('a', 1080)
        wait_for("document.querySelectorAll('.goal-reached').length === 3")
        window.load_url(f'http://127.0.0.1:{server.server_port}/goals.html?reopen=1')
        wait_for("document.getElementById('goal-2v2') && document.getElementById('goal-2v2').value === '16'")
        fixture.profile('a', 900)
        wait_for("document.querySelector('[data-mode=\"2v2\"] .goal-message').textContent.includes('20 seiere')")
        # Native dropdowns are not rebuilt by polling; keyboard focus survives refresh.
        window.evaluate_js("document.getElementById('goal-2v2').focus()")
        time.sleep(4.5)
        assert window.evaluate_js("document.activeElement.id") == 'goal-2v2'
        from System import Action
        window.evaluate_js("document.getElementById('goals-player').closest('article').scrollIntoView({block:'start'})")
        window.evaluate_js("document.querySelectorAll('.border-gradient-top,.border-gradient-bottom').forEach(el=>{const animation=el.getAnimations()[0];if(animation)animation.currentTime=2500})")
        time.sleep(.4)
        tasks = {}
        def capture():
            tasks['capture'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Page.captureScreenshot', '{"format":"png","captureBeyondViewport":true}')
        window.native.webview.Invoke(Action(capture))
        deadline = time.monotonic() + 10
        while not tasks['capture'].IsCompleted and time.monotonic() < deadline:
            time.sleep(.1)
        (root / 'build/goals-preview.png').write_bytes(base64.b64decode(json.loads(str(tasks['capture'].Result))['data']))
        media = {}
        def reduced_motion():
            media['task'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Emulation.setEmulatedMedia', '{"features":[{"name":"prefers-reduced-motion","value":"reduce"}]}')
        window.native.webview.Invoke(Action(reduced_motion))
        deadline = time.monotonic()+10
        while not media['task'].IsCompleted and time.monotonic()<deadline: time.sleep(.1)
        wait_for("getComputedStyle(document.querySelector('.border-gradient-bottom')).animationName === 'none'")
        window.resize(800,980)
        time.sleep(.4)
        assert window.evaluate_js("Array.from(document.querySelectorAll('.goal-star-border .inner-content')).every(el=>el.scrollWidth<=el.clientWidth)")
        fixture.overlay.profile = None
        wait_for("document.querySelector('[data-mode=\"2v2\"] .module-note').textContent.includes('Ingen MMR')")
        assert window.evaluate_js("document.querySelector('[data-mode=\"2v2\"] .goal-metrics strong').textContent") == '—'
        print('Goals UI: three modes, saved targets, win estimates, fresh ranks, reached/missing data and focus OK', flush=True)
    except Exception as error:
        import traceback
        failures.append(repr(error)); traceback.print_exc()
    finally:
        window.destroy()


try:
    webview.start(exercise, gui='edgechromium', private_mode=False, storage_path=webview_storage.name)
finally:
    server.shutdown(); server.server_close(); fixture.tearDown()
    webview_storage.cleanup()
sys.exit(1 if failures else 0)

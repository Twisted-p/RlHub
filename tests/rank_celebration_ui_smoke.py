"""Real WebView card delivery, dismissal, navigation and responsive rendering."""
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_app import start_server
from overlay_service import OverlayService
import webview

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-celebration-", ignore_cleanup_errors=True)
overlay = OverlayService(temporary.name, SimpleNamespace(snapshot=lambda: {"matches": []}))
now = datetime.now(timezone.utc)
def update(rank, seconds, mode="2v2"):
    overlay.set_profile({"playerId":"test-celebration", "name":"Test player", "fetchedAt":(now+timedelta(seconds=seconds)).isoformat(),
        "ranks":[{"playlist":mode, "rank":rank, "mmr":1082}]})
update("Diamond III Division IV", -20)
update("Champion I Division I", -10)
server = start_server(0, overlay=overlay)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub Rank Celebration test", origin+"/settings.html", width=1180, height=820)
failures = []
def js(expression):
    return window.evaluate_js(expression)
def wait_for(expression):
    deadline = time.monotonic()+20
    while time.monotonic()<deadline:
        try:
            if js(expression): return
        except Exception: pass
        time.sleep(.1)
    raise AssertionError(expression)
def cdp(method, arguments):
    from System import Action
    tasks = {}
    def call():
        tasks['task'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync(method,json.dumps(arguments))
    window.native.webview.Invoke(Action(call))
    deadline = time.monotonic()+10
    while not tasks['task'].IsCompleted and time.monotonic()<deadline: time.sleep(.1)
    return json.loads(str(tasks['task'].Result))
def capture(name):
    (ROOT/'build').mkdir(exist_ok=True)
    (ROOT/'build'/name).write_bytes(base64.b64decode(cdp('Page.captureScreenshot', {'format':'png'})['data']))
def exercise():
    try:
        wait_for("document.querySelector('.rank-celebration')?.open")
        wait_for("document.querySelector('#milestone-icon').naturalWidth > 0")
        time.sleep(1)
        assert js("document.querySelector('#milestone-family').textContent") == 'Champion 1 · DIV 1'
        assert js("document.querySelector('#milestone-name').textContent") == 'Test player'
        assert js("document.querySelector('#milestone-mmr').textContent") == '1082'
        assert js("document.activeElement.className") == 'milestone-dismiss'
        capture('rank-celebration-preview.png')
        window.resize(440,780)
        time.sleep(.6)
        assert js("document.querySelector('.rank-celebration').scrollWidth <= document.querySelector('.rank-celebration').clientWidth")
        assert js("document.querySelector('.milestone-footer').getBoundingClientRect().bottom <= document.querySelector('.milestone-card').getBoundingClientRect().bottom")
        capture('rank-celebration-mobile.png')
        cdp('Emulation.setEmulatedMedia', {'features':[{'name':'prefers-reduced-motion','value':'reduce'}]})
        assert js("getComputedStyle(document.querySelector('.milestone-stage')).animationName") == 'none'
        with patch.object(overlay.promotions, '_save', side_effect=PermissionError('Test disk failure')):
            js("document.querySelector('.milestone-dismiss').click()")
            wait_for("document.querySelector('.milestone-stat-note[role=status]').textContent.includes('Prøv igjen')")
            assert js("document.querySelector('.rank-celebration').open")
            assert overlay.promotions.pending(overlay.profile)
        js("document.querySelector('.rank-celebration').dispatchEvent(new Event('cancel',{cancelable:true}))")
        wait_for("!document.querySelector('.rank-celebration').open")
        deadline = time.monotonic()+5
        while overlay.promotions.pending(overlay.profile) and time.monotonic()<deadline: time.sleep(.1)
        assert overlay.promotions.pending(overlay.profile) == []
        window.load_url(origin+'/dashboard.html')
        wait_for("document.querySelector('.rank-celebration') !== null")
        time.sleep(3)
        assert js("document.querySelector('.rank-celebration').open") is False
        update('Grand Champion I Division I', 0)
        wait_for("document.querySelector('.rank-celebration').open && document.querySelector('#milestone-family').textContent === 'Grand Champion 1 · DIV 1'")
        js("document.querySelector('.milestone-dismiss').click()")
        wait_for("!document.querySelector('.rank-celebration').open")
        print('Rank celebration UI: real event, icon, values, focus, reduced motion, narrow layout, Escape, persisted dismissal and cross-page delivery OK',flush=True)
    except Exception as error:
        failures.append(repr(error));print(repr(error),file=sys.stderr,flush=True)
    finally: window.destroy()
try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(temporary.name)/'webview'))
finally:
    server.shutdown();server.server_close();temporary.cleanup()
sys.exit(1 if failures else 0)

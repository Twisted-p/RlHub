"""Exercise real Dashboard Progression navigation and copy flows in isolated WebView2 storage."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_app import start_server
import webview

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-progress-test-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
from datetime import datetime, timedelta, timezone
from performance_service import PerformanceService
from overlay_service import OverlayService
performance = PerformanceService(Path(temporary.name), root=Path(temporary.name))
overlay = OverlayService(Path(temporary.name), performance)
server.overlay = overlay
now = datetime.now(timezone.utc)
ratings = [910,895,918,923,941,957,930,917,925,901,903,939,964,960]
for index, mmr in enumerate(ratings):
    profile = {'name':'Test player','playerId':'test-account','fetchedAt':(now-timedelta(days=(len(ratings)-1-index)*3)).isoformat(),
      'ranks':[{'playlist':'2v2','rank':'Diamond II Division III','mmr':mmr},{'playlist':'1v1','rank':'Gold III Division I','mmr':620}]}
    overlay.set_profile(profile)
window = webview.create_window("RL Hub Dashboard Progression test", origin + "/dashboard.html", width=1180, height=820)
failures = []


def js(expression):
    return window.evaluate_js(expression)


def wait_for(expression):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if js(expression):
                return
        except Exception:
            pass
        time.sleep(.1)
    raise AssertionError(expression)


def mock_clipboard():
    js("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedText=text}}})")


def capture(name):
    from System import Action
    tasks = {}
    js("window.scrollTo(0,0)")
    def take():
        tasks["image"] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync("Page.captureScreenshot", '{"format":"png"}')
    window.native.webview.Invoke(Action(take))
    deadline = time.monotonic() + 10
    while not tasks["image"].IsCompleted and time.monotonic() < deadline:
        time.sleep(.1)
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / name).write_bytes(base64.b64decode(json.loads(str(tasks["image"].Result))["data"]))


def exercise():
    try:
        wait_for("document.querySelectorAll('#progress-chart circle').length === 14")
        assert js("document.getElementById('progress-mmr').textContent") == '960'
        assert js("document.getElementById('progress-delta').textContent") == '+50 MMR'
        assert js("document.querySelectorAll('#progress-chart rect').length > 1")
        assert js("document.querySelector('#progress-chart polyline').getAttribute('points').split(' ').length") == 14
        assert js("document.querySelector('#progress-chart circle').getAttribute('aria-label').includes('910 MMR')")
        assert js("document.querySelector('#progress-tip-title').textContent.length > 0")
        js("document.getElementById('progress-title').scrollIntoView({block:'start'})")
        time.sleep(.8)
        # Capture the graph, not the opening hero.
        from System import Action
        tasks = {}
        def take():
            tasks['image'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Page.captureScreenshot', '{"format":"png"}')
        window.native.webview.Invoke(Action(take))
        while not tasks['image'].IsCompleted:time.sleep(.1)
        (ROOT/'build'/'dashboard-progression-preview.png').write_bytes(base64.b64decode(json.loads(str(tasks['image'].Result))['data']))
        js("document.getElementById('progress-period').value='30';document.getElementById('progress-period').dispatchEvent(new Event('change'))")
        wait_for("document.querySelectorAll('#progress-chart circle').length === 10")
        js("document.getElementById('progress-mode').value='1v1';document.getElementById('progress-mode').dispatchEvent(new Event('change'))")
        wait_for("document.getElementById('progress-mmr').textContent === '620'")
        wait_for("document.querySelector('.rank-mode button').getAttribute('aria-pressed') === 'true'")
        js("document.querySelectorAll('.rank-mode button')[2].click()")
        wait_for("document.getElementById('progress-mode').value === '3v3' && document.getElementById('progress-mmr').textContent === '—'")
        assert js("document.getElementById('progress-empty').hidden") == False
        assert js("document.querySelectorAll('#progress-chart circle').length") == 0
        js("document.getElementById('progress-mode').value='2v2';document.getElementById('progress-mode').dispatchEvent(new Event('change'))")
        wait_for("document.getElementById('progress-mmr').textContent === '960'")
        window.resize(800,820);time.sleep(.5)
        assert js("document.documentElement.scrollWidth <= innerWidth")
        print('Dashboard Progression UI: real observations, rank bands, date range, mode sync, tooltip labels, missing rank and responsive layout OK',flush=True)
    except Exception as error:
        failures.append(repr(error));print(repr(error),file=sys.stderr,flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(temporary.name) / "webview"))
finally:
    server.shutdown()
    server.server_close()
    performance.stop()
    temporary.cleanup()
sys.exit(1 if failures else 0)

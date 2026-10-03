"""Exercise real Training Packs navigation and copy flows in isolated WebView2 storage."""
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

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-packs-test-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub Training Packs test", origin + "/training-packs.html", width=1180, height=820)
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
        wait_for("document.querySelectorAll('.pack-card').length === 3")
        assert js("document.querySelectorAll('.nav-link.active').length") == 1
        assert js("document.querySelector('.nav-link.active').textContent") == "Training Packs"
        mock_clipboard()
        js("document.querySelector('.pack-card button').click()")
        wait_for("typeof copiedText === 'string'")
        assert js("copiedText") == js("document.querySelector('.pack-card code').textContent")
        js("window.originalNow=Date.now; window.fakeNow=900000*1000+899999; Date.now=()=>fakeNow; window.dispatchEvent(new Event('focus'))")
        assert js("document.getElementById('packs-countdown').textContent") == '00:01'
        before = js("Array.from(document.querySelectorAll('.pack-card code'), e=>e.textContent)")
        js("window.fakeNow+=1; window.dispatchEvent(new Event('focus'))")
        assert js("document.getElementById('packs-countdown').textContent") == '15:00'
        after = js("Array.from(document.querySelectorAll('.pack-card code'), e=>e.textContent)")
        assert len(set(after)) == 3 and not set(before).intersection(after)
        js("window.fakeNow+=900000*23; document.dispatchEvent(new Event('visibilitychange'))")
        assert js("JSON.stringify(Array.from(document.querySelectorAll('.pack-card code'), e=>e.textContent))===JSON.stringify(RLTrainingRotation.rotation(RLTrainingPacks).packs.map(p=>p.code))")
        js("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('denied')}}}); document.querySelector('.pack-card button').click()")
        wait_for("document.getElementById('packs-copy-dialog').open")
        assert js("document.getElementById('packs-copy-text').value") == js("document.querySelector('.pack-card code').textContent")
        assert js("document.getElementById('packs-copy-text').selectionEnd") == 19
        js("document.getElementById('packs-close-dialog').click(); Date.now=originalNow; window.dispatchEvent(new Event('focus'))")
        assert js("document.documentElement.scrollWidth <= innerWidth")
        time.sleep(.8)
        capture('training-packs-preview.png')
        window.resize(800, 820)
        time.sleep(.8)
        assert js("document.documentElement.scrollWidth <= innerWidth")
        assert js("Array.from(document.querySelectorAll('.pack-card code')).every(e=>e.scrollWidth<=e.clientWidth)")
        capture('training-packs-narrow.png')
        window.load_url(origin + '/training.html')
        wait_for("document.querySelectorAll('.nav a[href=\"./training-packs.html\"]').length === 1")
        js("document.querySelector('.nav a[href=\"./training-packs.html\"]').click()")
        wait_for("document.querySelectorAll('.pack-card').length === 3")
        assert js("document.querySelectorAll('.nav-link.active').length") == 1
        print('Training Packs UI: navigation, three cards, quarter-hour switch, sleep catch-up, copy, manual fallback and responsive layout OK', flush=True)
    except Exception as error:
        failures.append(repr(error))
        print(repr(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(temporary.name) / "webview"))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

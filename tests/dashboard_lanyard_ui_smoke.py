"""Exercise real Dashboard Rank navigation and copy flows in isolated WebView2 storage."""
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

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-rank-test-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub Dashboard Rank test", origin + "/dashboard.html", width=1180, height=820)
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
        wait_for("document.querySelector('#dashboard-rank-lanyard .rank-mode')")
        js("localStorage.setItem('rlhub:trackerProfile',JSON.stringify({name:'Test player',ranks:[{playlist:'1v1',rank:'Diamond II Division I',mmr:945},{playlist:'2v2',rank:'Champion I Division II',mmr:1234}]})); window.dispatchEvent(new Event('storage'))")
        wait_for("document.getElementById('dashboard-rank-lanyard').dataset.tier === '16'")
        wait_for("document.querySelector('#dashboard-rank-lanyard canvas')")
        time.sleep(5)
        capture('dashboard-lanyard-preview.png')
        assert js("document.documentElement.scrollWidth <= innerWidth"), str(js("[document.documentElement.scrollWidth,innerWidth]"))
        js("document.querySelector('.rank-mode button').click()")
        wait_for("document.getElementById('dashboard-rank-lanyard').dataset.tier === '14'")
        js("document.querySelectorAll('.rank-mode button')[2].click()")
        wait_for("document.querySelector('.rank-caption a')")
        assert js("document.getElementById('dashboard-rank-lanyard').dataset.rank") == 'Hent rank i Profile'
        js("document.querySelectorAll('.rank-mode button')[1].click();location.reload()")
        wait_for("document.getElementById('dashboard-rank-lanyard').dataset.tier === '16'")
        window.resize(800,820)
        time.sleep(1)
        assert js("document.documentElement.scrollWidth <= innerWidth"), str(js("[document.documentElement.scrollWidth,innerWidth]"))
        capture('dashboard-lanyard-narrow.png')
        from System import Action
        tasks = {}
        def motion():
            tasks['motion'] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Emulation.setEmulatedMedia', '{"features":[{"name":"prefers-reduced-motion","value":"reduce"}]}')
        window.native.webview.Invoke(Action(motion))
        while not tasks['motion'].IsCompleted: time.sleep(.1)
        wait_for("!document.querySelector('#dashboard-rank-lanyard canvas') && document.querySelector('.rank-card-static')")
        assert js("document.getElementById('dashboard-rank-lanyard').dataset.tier") == '16'
        print('Dashboard Lanyard: real WebGL, rank icon selection, unknown rank, saved mode, navigation and narrow layout OK',flush=True)
    except Exception as error:
        failures.append(repr(error));print(repr(error),file=sys.stderr,flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(temporary.name) / "webview"))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

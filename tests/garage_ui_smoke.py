"""Exercise Garage in WebView2 with isolated storage and a temporary server."""
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

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-garage-test-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub Garage test", origin + "/garage.html", width=1180, height=820)
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


def js(expression):
    return window.evaluate_js(expression)


def capture(name):
    from System import Action
    tasks = {}
    js("window.scrollTo(0,0)")
    def take():
        tasks["image"] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync(
            "Page.captureScreenshot", '{"format":"png"}')
    window.native.webview.Invoke(Action(take))
    deadline = time.monotonic() + 10
    while not tasks["image"].IsCompleted and time.monotonic() < deadline:
        time.sleep(.1)
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / name).write_bytes(base64.b64decode(json.loads(str(tasks["image"].Result))["data"]))


def exercise():
    try:
        for asset in ["garage.js", "garage.css", "garage-presets.js", "assets/garage/zen.jpeg", "assets/garage/jstn.png", "assets/garage/squishy.jpeg", "assets/garage/retals.jpeg"]:
            with urlopen(origin + "/" + asset) as response:
                assert response.status == 200 and len(response.read()) > 100, asset
        wait_for("document.querySelectorAll('.garage-card').length === 4")
        wait_for("[...document.querySelectorAll('.garage-card img')].every(i => i.complete && i.naturalWidth > 0)")
        assert js("document.querySelector('.nav-link.active').textContent.trim()") == "Garage"
        legacy = js("presets.map(p => ({...p}))")
        legacy[0]["name"] = "Behold mitt gamle preset"
        js("localStorage.setItem(GARAGE_PRESETS_STORAGE_KEY," + json.dumps(json.dumps(legacy)) + "); location.reload()")
        wait_for("document.getElementById('garage-active-name').textContent === 'Behold mitt gamle preset'")
        assert js("presets.length") == len(legacy)
        js("document.querySelector('[data-car=Octane]').click()")
        assert js("document.querySelectorAll('.garage-card').length") == 1
        js("document.querySelector('[data-car=all]').click(); document.getElementById('garage-search').value='zen'; document.getElementById('garage-search').dispatchEvent(new Event('input'))")
        assert js("document.querySelectorAll('.garage-card').length") == 1
        js("document.getElementById('garage-search').value='no match'; document.getElementById('garage-search').dispatchEvent(new Event('input'))")
        assert js("!!document.querySelector('.garage-empty')")
        js("document.getElementById('garage-search').value=''; document.getElementById('garage-search').dispatchEvent(new Event('input')); document.querySelector('.garage-card [data-favorite]').click(); location.reload()")
        wait_for("document.getElementById('garage-favorite-count').textContent === '1'")
        js("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedList=text}}}); document.querySelector('[data-action=copy]').click()")
        wait_for("typeof copiedList === 'string' && copiedList.includes('Cristiano') && copiedList.includes('https://bakkesplugins.com/cars/3448')")
        js("document.querySelector('[data-view=favorites]').click()")
        assert js("document.querySelectorAll('.garage-card').length") == 1
        js("document.querySelector('[data-view=discover]').click(); document.querySelector('[data-action=zoom]').click()")
        assert js("document.getElementById('garage-image-dialog').open")
        js("document.getElementById('garage-close-image').click(); document.querySelector('[data-action=save]').click()")
        assert js("presets.length") == len(legacy) + 1
        assert js("document.getElementById('garage-active-name').textContent") == legacy[0]["name"]
        js("document.querySelector('[data-view=discover]').click(); document.querySelector('[data-open=\"pro:zen-ombre\"]').click(); document.querySelector('[data-action=save]').click()")
        assert js("presets.length") == len(legacy) + 1, "Duplicate catalog save"
        js("document.querySelector('[data-action=activate]').click(); location.reload()")
        wait_for("document.getElementById('garage-active-name').textContent === 'Ombre Fennec'")
        assert js("presets[state.selectedPreset].referenceId") == "zen-ombre"
        js("document.querySelector('[data-view=mine]').click(); document.querySelector('[data-open=\"mine:' + presets[state.selectedPreset].id + '\"]').click(); document.querySelector('[data-action=edit]').click()")
        assert js("document.getElementById('garage-editor').open")
        js("const f=document.getElementById('garage-custom-form'); f.elements.name.value='<img src=x onerror=alert(1)>'; f.elements.car.value='Octane'; f.requestSubmit()")
        assert js("document.querySelector('.garage-feature h2').textContent") == "<img src=x onerror=alert(1)>"
        assert js("document.querySelector('.garage-parts dd').textContent") == "Octane"
        assert js("document.querySelector('.garage-feature h2 img') === null")
        js("document.getElementById('garage-new').click(); document.getElementById('garage-custom-form').elements.name.value='Ny egen bil'; document.getElementById('garage-custom-form').requestSubmit()")
        assert js("presets.length") == len(legacy) + 2
        js("document.querySelector('[data-action=activate]').click(); document.querySelector('[data-action=delete]').click()")
        assert js("presets.length") == len(legacy) + 1
        assert js("state.selectedPreset >= 0 && state.selectedPreset < presets.length")
        js("document.querySelector('[data-view=discover]').click(); document.querySelector('[data-open=\"pro:retals-anodized\"]').click()")
        assert js("document.querySelector('.garage-feature').getBoundingClientRect().height < 650"), "Tall photo expands feature"
        assert js("document.documentElement.scrollWidth <= innerWidth"), "Horizontal overflow"
        js("document.querySelector('[data-open=\"pro:zen-ombre\"]').click()")
        js("localStorage.clear(); location.reload()")
        wait_for("document.querySelectorAll('.garage-card').length === 4 && document.getElementById('garage-favorite-count').textContent === '0'")
        time.sleep(1)
        capture("garage-preview.png")
        window.resize(800, 820)
        time.sleep(1)
        assert js("document.documentElement.scrollWidth <= innerWidth"), "Narrow layout overflow"
        assert js("document.querySelector('.sidebar').getBoundingClientRect().height < 180"), "Navigation dominates narrow layout"
        capture("garage-preview-narrow.png")
        print("Garage UI: local assets, legacy preservation, filters, favorite persistence, image zoom, deduplication, active preset, safe editing, deletion and responsive layout OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(Path(temporary.name) / "webview"))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

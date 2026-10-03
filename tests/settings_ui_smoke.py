"""Exercise real Settings navigation and copy flows in isolated WebView2 storage."""
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

temporary = tempfile.TemporaryDirectory(prefix="rl-hub-settings-test-", ignore_cleanup_errors=True)
server = start_server(0)
origin = f"http://127.0.0.1:{server.server_port}"
window = webview.create_window("RL Hub Settings test", origin + "/settings.html", width=1180, height=820)
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
        for asset in ["settings.html", "settings.js", "settings.css", "pro-settings-data.js"]:
            with urlopen(origin + "/" + asset) as response:
                assert response.status == 200 and len(response.read()) > 100, asset
        wait_for("document.querySelectorAll('[data-player]').length === 5")
        assert js("document.querySelectorAll('.nav-link.active').length") == 1
        assert js("document.querySelector('.nav-link.active').textContent") == "Settings"
        assert js("document.querySelectorAll('.nav a[href=\"./settings.html\"]').length") == 1
        mock_clipboard()
        # Source-backed spot checks: camera, sensitivity and distinct directional bindings.
        expected_fov = {"zen":"110", "vatira":"110", "monkeymoon":"110", "daniel":"110", "beastmode":"109"}
        for player, fov in expected_fov.items():
            js(f"document.querySelector('[data-player={player}]').click(); document.querySelector('[data-section=camera]').click(); document.querySelector('[data-copy=section]').click()")
            wait_for("typeof copiedText === 'string'")
            copied = js("copiedText")
            assert "FOV: " + fov in copied
            assert "Kilde: https://liquipedia.net/rocketleague/" in copied
            assert "dato ikke oppgitt" in copied
            js("document.querySelector('[data-section=controls]').click(); document.querySelector('[data-copy=section]').click()")
            assert "Controller Deadzone:" in js("copiedText")
        js("document.querySelector('[data-player=zen]').click(); document.querySelector('[data-section=controls]').click()")
        assert js("document.querySelectorAll('#settings-values .settings-value').length") == 9
        assert js("document.querySelector('[data-copy=\"controls:1\"]').previousElementSibling.textContent") == "R1"
        assert js("document.querySelector('[data-copy=\"controls:2\"]').previousElementSibling.textContent") == "L2"
        assert js("document.querySelector('[data-copy=\"controls:3\"]').previousElementSibling.textContent") == "Ikke bundet"
        js("document.getElementById('settings-controller').value='xbox'; document.getElementById('settings-controller').dispatchEvent(new Event('change')); document.querySelector('[data-copy=section]').click()")
        assert "Air Roll: RB\nAir Roll Left: LT\nAir Roll Right: Ikke bundet" in js("copiedText")
        assert "Boost: B\nJump: A\nBall Cam: Y\nBrake: LT\nThrottle: RT" in js("copiedText")
        js("document.querySelector('[data-copy=\"controls:0\"]').click()")
        assert js("copiedText") == "X", "Xbox X is mapped from PS Square, not PS Cross"
        js("document.querySelector('[data-player=monkeymoon]').click(); document.querySelector('[data-copy=\"deadzone:3\"]').click()")
        assert js("copiedText") == "2.93"
        js("location.reload()")
        wait_for("document.getElementById('settings-player-name').textContent === 'M0nkey M00n'")
        assert js("document.getElementById('settings-controller').value") == "xbox"
        mock_clipboard()
        js("document.querySelector('[data-copy=section]').click()")
        assert "FOV: 110" in js("copiedText") and "Boost:" not in js("copiedText")
        js("document.querySelector('[data-section=camera]').dispatchEvent(new KeyboardEvent('keydown',{key:'End',bubbles:true}))")
        assert js("document.getElementById('settings-tab-controls').getAttribute('aria-selected')") == "true"
        js("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('denied')}}}); document.querySelector('[data-copy=section]').click()")
        wait_for("document.getElementById('settings-copy-dialog').open")
        assert js("document.getElementById('settings-copy-text').value.includes('M0nkey M00n')")
        assert js("document.getElementById('settings-copy-text').selectionEnd") == js("document.getElementById('settings-copy-text').value.length")
        js("document.getElementById('settings-close-dialog').click()")
        # Shared navigation must expose the new page on old pages, without duplicates.
        window.load_url(origin + "/garage.html")
        wait_for("document.querySelectorAll('.garage-card').length === 4")
        assert js("document.querySelectorAll('.nav a[href=\"./settings.html\"]').length") == 1
        js("document.querySelector('.nav a[href=\"./settings.html\"]').click()")
        wait_for("document.getElementById('settings-player-name')?.textContent === 'M0nkey M00n'")
        js("localStorage.setItem('rlhub:proSettings','invalid json'); location.reload()")
        wait_for("document.getElementById('settings-player-name')?.textContent === 'zen'")
        assert js("document.getElementById('settings-controller').value") == "ps"
        assert js("document.documentElement.scrollWidth <= innerWidth")
        time.sleep(.8)
        capture("settings-preview.png")
        js("document.querySelector('[data-section=controls]').click()")
        capture("settings-controls-preview.png")
        window.resize(800, 820)
        time.sleep(.8)
        assert js("document.documentElement.scrollWidth <= innerWidth"), "Narrow layout overflow"
        assert js("document.querySelector('.sidebar').getBoundingClientRect().height < 180")
        capture("settings-preview-narrow.png")
        print("Settings UI: five profiles, source-backed values, PS/Xbox mapping, copy scopes, individual values, persistence, keyboard tabs, manual fallback, navigation and narrow layout OK", flush=True)
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

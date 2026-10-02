"""Verify Performance in WebView2 with simulated official Stats API events."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import time
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import start_server
from performance_service import PerformanceService
from test_performance import STATE, END, PLAYER
import webview

root = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory(prefix="rl-hub-performance-test-", ignore_cleanup_errors=True)
storage = Path(temporary.name)
config = storage / "game/TAGame/Config/DefaultStatsAPI.ini"
config.parent.mkdir(parents=True)
config.write_text("[TAGame.MatchStatsExporter_TA]\nPort=49123\nWebPort=49124\nPacketSendRate=0\n")
service = PerformanceService(storage / "data", root=storage / "game", local_player={"name": "Player A", "playerId": PLAYER})
service._ensure_setup()
server = start_server(0, performance=service)
window = webview.create_window("RL Hub Performance test", f"http://127.0.0.1:{server.server_port}/performance.html", width=1180, height=820)
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
        wait_for("typeof performanceData !== 'undefined' && performanceData !== null")
        assert window.evaluate_js("performanceDetail.innerText.includes('Ingen kamper lagret')")
        assert window.evaluate_js("document.querySelector('.nav-link.active').textContent") == "Performance"
        wait_for("performanceSetup.hidden && performanceStatus.innerText.includes('aktivert automatisk')")
        service.ingest({"Event": "MatchCreated", "Data": {"MatchGuid": "test-match"}})
        service.ingest(STATE)
        service.ingest(END)
        wait_for("document.querySelectorAll('.performance-metrics .profile-stat').length === 6")
        assert window.evaluate_js("performanceDetail.innerText.includes('Seier')")
        assert window.evaluate_js("performanceDetail.innerText.includes('40%')")
        assert window.evaluate_js("document.querySelectorAll('.performance-table tbody tr').length") == 2
        assert window.evaluate_js("document.querySelectorAll('[data-match-id]').length") == 1
        base = deepcopy(service.snapshot()["matches"][0])
        history = []
        for index in range(25):
            match = deepcopy(base)
            match.update(id=f"analytics-{index}", endedAt=f"2026-10-01T10:{index:02}:00+00:00", playlist=11 if index < 15 else 13, mode="Ranked 2v2" if index < 15 else "Ranked 3v3", winnerTeam=index % 2)
            match["players"][0].update(shots=index, goals=index % 3, saves=index % 5, score=100 + index)
            history.append(match)
        with service.lock:
            service.history = list(reversed(history))
        wait_for("performanceData.matches.length === 25")
        window.evaluate_js("modeFilter.value='11'; modeFilter.dispatchEvent(new Event('change'))")
        assert window.evaluate_js("document.querySelectorAll('[data-match-id]').length") == 15
        window.evaluate_js("sortFilter.value='shots'; sortFilter.dispatchEvent(new Event('change'))")
        assert window.evaluate_js("document.querySelector('[data-match-id]').dataset.matchId") == "analytics-14"
        window.evaluate_js("document.getElementById('performance-tab-trends').click(); rangeFilter.value='5'; rangeFilter.dispatchEvent(new Event('change'))")
        assert window.evaluate_js("document.querySelectorAll('.performance-chart svg').length") == 4
        assert window.evaluate_js("document.querySelectorAll('[data-open-match]').length") == 5
        assert window.evaluate_js("document.querySelector('[data-open-match]').dataset.openMatch") == "analytics-10"
        assert window.evaluate_js("document.getElementById('performance-trend-metrics').innerText.includes('12 per kamp')")
        window.evaluate_js("rangeFilter.value='20'; rangeFilter.dispatchEvent(new Event('change'))")
        assert window.evaluate_js("document.querySelectorAll('[data-open-match]').length") == 15
        window.evaluate_js("resultFilter.value='win'; resultFilter.dispatchEvent(new Event('change'))")
        assert window.evaluate_js("document.querySelectorAll('[data-open-match]').length") == 8
        window.evaluate_js("document.querySelector('[data-open-match]').click()")
        assert window.evaluate_js("performanceView") == "matches"
        assert window.evaluate_js("selectedMatchId") == "analytics-0"
        window.evaluate_js("modeFilter.value='13'; resultFilter.value='loss'; renderPerformance()")
        assert window.evaluate_js("document.querySelectorAll('[data-match-id]').length") == 5
        window.evaluate_js("modeFilter.innerHTML += '<option value=\"999\">Empty mode</option>'; modeFilter.value='999'; renderPerformance(); document.getElementById('performance-tab-trends').click()")
        assert window.evaluate_js("document.querySelectorAll('.performance-chart svg').length") == 0
        assert window.evaluate_js("document.getElementById('performance-trends-summary').innerText.includes('Ingen kamper')")
        window.evaluate_js("document.getElementById('performance-reset-filters').click(); rangeFilter.value='20'; renderPerformance()")
        assert window.evaluate_js("document.querySelectorAll('[data-open-match]').length") == 20
        time.sleep(1)
        # Capture WebView's own surface even when a fullscreen game covers the desktop.
        from System import Action
        tasks = {}
        window.evaluate_js("window.scrollTo(0,0)")
        def capture():
            tasks["capture"] = window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync("Page.captureScreenshot", '{"format":"png","captureBeyondViewport":true}')
        window.native.webview.Invoke(Action(capture))
        deadline = time.monotonic() + 10
        while not tasks["capture"].IsCompleted and time.monotonic() < deadline:
            time.sleep(.1)
        image = json.loads(str(tasks["capture"].Result))["data"]
        (root / "build/performance-preview.png").write_bytes(base64.b64decode(image))
        print("Performance UI: collection, mode/result filters, sorting, 5/10/20 windows, charts, drilldown and empty state OK", flush=True)
    except Exception as error:
        failures.append(str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        window.destroy()


try:
    webview.start(exercise, gui="edgechromium", private_mode=False, storage_path=str(storage / "webview"))
finally:
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

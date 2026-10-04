"""Real WebView2 minimize/restore, navigation and GPU/CSS pause lifecycle."""
from copy import deepcopy
import ctypes
from ctypes import wintypes
from pathlib import Path
import sys
import os
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_app import start_server
from game_window import GameWindowController
from performance_service import PerformanceService
from overlay_service import OverlayService
from goals_service import GoalsService
from test_performance import STATE, END, PLAYER
import webview

temporary = tempfile.TemporaryDirectory(prefix='rl-hub-game-window-', ignore_cleanup_errors=True)
performance = PerformanceService(Path(temporary.name), root=Path(temporary.name))
performance.connected = True
overlay = OverlayService(temporary.name, performance)
overlay.set_profile({'playerId':PLAYER,'name':'Test player','ranks':[{'playlist':'2v2','rank':'Diamond II Division III','mmr':950}]})
server = start_server(0, performance=performance, overlay=overlay, goals=GoalsService(temporary.name, overlay))
origin = f'http://127.0.0.1:{server.server_port}'
window = webview.create_window('RL Hub game window test', origin+'/dashboard.html', width=1180, height=820)
controller = GameWindowController(window, performance)
server.game_window = controller
failures = []
user32 = ctypes.windll.user32
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL

def js(expression):
    return window.evaluate_js(expression)

def iconic():
    return bool(user32.IsIconic(int(window.native.Handle.ToInt64())))

def wait(condition):
    deadline = time.monotonic()+20
    while time.monotonic()<deadline:
        if condition(): return
        time.sleep(.1)
    raise AssertionError('Condition did not become true; rank scene: ' + str(js("({scene:document.querySelector('#dashboard-rank-lanyard')?.dataset.scene,rank:document.querySelector('#dashboard-rank-lanyard')?.dataset.rank,hidden:document.hidden,paused:window.RL_HUB_MOTION_PAUSED,static:!!document.querySelector('.rank-card-static')})")))

def rank_card_ready():
    if js("document.querySelector('#dashboard-rank-lanyard canvas') !== null"):
        return True
    if os.environ.get('RL_HUB_UI_ALLOW_STATIC') == '1':
        return js("(document.querySelector('#dashboard-rank-lanyard').dataset.scene === 'fallback' || matchMedia('(prefers-reduced-motion: reduce)').matches) && document.querySelector('.rank-card-static img')?.naturalWidth > 0 && document.querySelector('.rank-caption strong')?.textContent === 'Diamond II Division III'")
    return False

def exercise():
    try:
        wait(lambda: controller.ready.is_set() and js("typeof RL_HUB_SET_GAME_ACTIVITY === 'function'"))
        wait(rank_card_ready)
        print('Rank renderer:', '3D' if js("!!document.querySelector('#dashboard-rank-lanyard canvas')") else 'verified static fallback', flush=True)
        controller.tick()
        assert not iconic()
        training = deepcopy(STATE)
        training['Data']['Players'] = training['Data']['Players'][:1]
        training['Data']['Game']['Teams'] = []
        performance.ingest(training)
        controller.tick()
        wait(iconic)
        wait(lambda: js("RL_HUB_MOTION_PAUSED && document.querySelectorAll('canvas').length === 0"))
        performance.ingest({'Event':'MatchCreated','Data':{}})
        performance.ingest(STATE)
        performance.ingest(END)
        controller.tick()
        assert iconic() and controller.busy
        # A navigation while playing must inherit the pause before React mounts.
        window.load_url(origin+'/garage.html')
        wait(lambda: js("document.body.dataset.page === 'garage' && document.querySelectorAll('.garage-card-image img').length >= 4"))
        controller.tick()
        assert js("RL_HUB_MOTION_PAUSED && document.querySelectorAll('.tilted-card-figure').length === 0")
        window.load_url(origin+'/goals.html')
        wait(lambda: js("document.querySelectorAll('.goal-star-border').length === 3"))
        controller.tick()
        assert js("getComputedStyle(document.querySelector('.border-gradient-top')).animationPlayState === 'paused'")
        assert js("Array.from(document.querySelectorAll('.reveal')).every(el => getComputedStyle(el).opacity === '1' && getComputedStyle(el).transform === 'none')")
        window.restore()
        wait(lambda: not iconic())
        assert js("RL_HUB_MOTION_PAUSED && Array.from(document.querySelectorAll('.reveal')).every(el => getComputedStyle(el).opacity === '1')")
        window.minimize()
        wait(iconic)
        performance.connected = False
        controller.tick()
        assert iconic()  # A lost feed must not be mistaken for a lobby.
        performance.connected = True
        performance.ingest({'Event':'MatchDestroyed','Data':{}})
        controller.tick()
        assert iconic()
        time.sleep(1.6)
        controller.tick()
        wait(lambda: not iconic())
        wait(lambda: js("!RL_HUB_MOTION_PAUSED && getComputedStyle(document.querySelector('.border-gradient-top')).animationPlayState === 'running'"))
        window.load_url(origin+'/dashboard.html')
        wait(lambda: js("document.body.dataset.page === 'dashboard'") and rank_card_ready())
        controller.tick()
        assert not controller.busy
        print('Game window UI: actual minimize/restore, result-screen hold, GPU release/resume, paused navigation, CSS pause and connection-loss handling OK', flush=True)
    except Exception:
        failures.append(traceback.format_exc())
        print(failures[-1], file=sys.stderr, flush=True)
    finally:
        window.destroy()

try:
    webview.start(exercise, gui='edgechromium', private_mode=False, storage_path=str(Path(temporary.name)/'webview'))
finally:
    controller.stop()
    server.shutdown()
    server.server_close()
    temporary.cleanup()
sys.exit(1 if failures else 0)

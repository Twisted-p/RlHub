"""Actual React Bits rendering, pause/resume and dynamic page collections."""
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop_app import start_server
from overlay_service import OverlayService
import webview

temporary=tempfile.TemporaryDirectory(prefix='rl-hub-polish-',ignore_cleanup_errors=True)
overlay=OverlayService(temporary.name,SimpleNamespace(snapshot=lambda:{'matches':[]}))
now=datetime.now(timezone.utc)
def profile(mmr,seconds=0):
    overlay.set_profile({'playerId':'test','name':'Test player','fetchedAt':(now+timedelta(seconds=seconds)).isoformat(),
        'ranks':[{'playlist':'2v2','rank':'Diamond II Division III','mmr':mmr}]})
profile(950)
server=start_server(0,overlay=overlay)
origin=f'http://127.0.0.1:{server.server_port}'
window=webview.create_window('RL Hub React Bits test',origin+'/dashboard.html',width=1180,height=820)
failures=[]
def js(expression):return window.evaluate_js(expression)
def wait(expression):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        try:
            if js(expression):return
        except Exception:pass
        time.sleep(.1)
    raise AssertionError(expression)
def cdp(method,args):
    from System import Action
    tasks={}
    def call():tasks['task']=window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync(method,json.dumps(args))
    window.native.webview.Invoke(Action(call))
    deadline=time.monotonic()+10
    while not tasks['task'].IsCompleted and time.monotonic()<deadline:time.sleep(.1)
    return json.loads(str(tasks['task'].Result))
def media(value):cdp('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':value}]})
def capture(name):
    (ROOT/'build').mkdir(exist_ok=True)
    (ROOT/'build'/name).write_bytes(base64.b64decode(cdp('Page.captureScreenshot',{'format':'png'})['data']))
def exercise():
    try:
        wait("document.querySelector('.polish-aurora') !== null")
        media('no-preference')
        js("window.scrollTo(0,0);window.dispatchEvent(new Event('focus'))")
        wait("document.querySelector('.polish-aurora canvas') !== null")
        time.sleep(2)  # Allow the shader and rank-card entrance to finish painting.
        capture('app-polish-dashboard.png')
        js("window.dispatchEvent(new Event('blur'))")
        wait("document.querySelector('.polish-aurora').dataset.state === 'paused' && document.querySelector('.polish-aurora canvas') === null")
        js("window.dispatchEvent(new Event('focus'))")
        wait("document.querySelector('.polish-aurora canvas') !== null")
        js("document.querySelector('.page-header').scrollIntoView();window.scrollTo(0,document.body.scrollHeight)")
        wait("document.querySelector('.polish-aurora canvas') === null")
        js("window.scrollTo(0,0);window.dispatchEvent(new Event('focus'))")
        wait("document.querySelector('.polish-aurora canvas') !== null")
        media('reduce')
        wait("document.querySelector('.polish-aurora canvas') === null")
        # Original text stays authoritative and accessible; animated layer is aria-hidden.
        wait("document.querySelector('#progress-mmr').textContent === '950'")
        js("document.getElementById('progress-mmr').textContent='960';document.getElementById('session-training').textContent='1:30';document.getElementById('session-results').textContent='3 seiere · 2 tap (5/5 kamper)'")
        wait("document.querySelector('#progress-mmr').nextElementSibling.textContent === '960'")
        assert js("document.querySelector('#progress-mmr').nextElementSibling.getAttribute('aria-hidden')")=='true'
        media('no-preference')
        js("document.getElementById('progress-mmr').textContent='970'")
        wait("document.querySelector('#progress-mmr').nextElementSibling.textContent === '970'")
        assert js("getComputedStyle(document.querySelector('#progress-mmr').nextElementSibling).color !== 'rgba(0, 0, 0, 0)'")
        assert js("getComputedStyle(document.querySelector('#progress-mmr').nextElementSibling.querySelector('span')).fontSize") == '14px'
        assert js("getComputedStyle(document.querySelector('#session-training').nextElementSibling.querySelector('span')).fontSize") == '16px'
        assert js("getComputedStyle(document.querySelector('#session-results').nextElementSibling.querySelector('span')).display") == 'inline'
        js("document.querySelector('#session-training').scrollIntoView({block:'center'})")
        capture('app-polish-session.png')
        window.load_url(origin+'/training-packs.html')
        wait("document.querySelectorAll('.pack-card .card-spotlight').length === 3")
        assert js("getComputedStyle(document.querySelector('.pack-card .polish-spotlight-content')).flexDirection") == 'column'
        js("const c=document.querySelector('.card-spotlight');const r=c.getBoundingClientRect();c.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,clientX:r.left+30,clientY:r.top+40}))")
        wait("document.querySelector('.card-spotlight').style.getPropertyValue('--mouse-x') !== ''")
        capture('app-polish-packs.png')
        window.load_url(origin+'/settings.html')
        wait("document.querySelectorAll('#settings-values .card-spotlight').length === 9")
        js("document.querySelector('[data-section=controls]').click()")
        wait("document.querySelectorAll('#settings-values .card-spotlight').length === 9 && document.querySelectorAll('#settings-deadzone-values .card-spotlight').length === 4")
        window.load_url(origin+'/garage.html')
        wait("document.querySelectorAll('.tilted-card-figure').length >= 4")
        js("const c=document.querySelector('.tilted-card-figure');const r=c.getBoundingClientRect();c.dispatchEvent(new MouseEvent('mouseover',{bubbles:true,clientX:r.right-20,clientY:r.top+20}));c.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,clientX:r.right-20,clientY:r.top+20}))")
        wait("document.querySelector('.tilted-card-inner').style.transform.includes('rotate')")
        capture('app-polish-garage.png')
        media('reduce')
        wait("document.querySelectorAll('.tilted-card-figure').length === 0")
        assert js("document.querySelectorAll('.garage-card-image img').length >= 4")
        print('React Bits UI: Aurora focus/offscreen/reduced-motion pause and resume; authoritative accessible CountUp updates; dynamic Spotlight collections; real tilt and static fallback OK',flush=True)
    except Exception as error:
        import traceback
        failures.append(repr(error));traceback.print_exc()
    finally:window.destroy()
try:webview.start(exercise,gui='edgechromium',private_mode=False,storage_path=str(Path(temporary.name)/'webview'))
finally:server.shutdown();server.server_close();temporary.cleanup()
sys.exit(1 if failures else 0)

"""Click-through, non-activating Win32 overlay. No game hooks or DLL injection."""
import ctypes as c
from ctypes import wintypes as w
import json
import logging
import os
from pathlib import Path
import sys
from threading import Event, Thread

from PIL import Image, ImageDraw, ImageFont


def render_card(view, logo_path):
    image = Image.new("RGBA", (440, 250))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, 439, 249), radius=19, fill=(6, 20, 35, 242), outline=(73, 222, 205, 220), width=1)
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"

    def text(x, y, value, size=15, color="#f2f7ff", bold=False, max_width=395):
        try:
            font = ImageFont.truetype(str(fonts / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)
        except OSError:
            font = ImageFont.load_default()
        value = str(value)
        while len(value) > 1 and draw.textlength(value, font=font) > max_width:
            value = value[:-2] + "…"
        draw.text((x, y), value, fill=color, font=font)

    try:
        with Image.open(logo_path) as source:
            logo = source.convert("RGBA")
            logo.thumbnail((65, 54), Image.Resampling.LANCZOS)
            image.alpha_composite(logo, (17, 15))
    except OSError:
        pass
    phase = view["phase"]
    preview = view["preview"]
    title = "FORHÅNDSVISNING" if preview else {"lobby": "LOBBY", "training": "FREEPLAY / TRENING", "post-match": "ETTER KAMP", "match": "I KAMP"}.get(phase, "RL HUB")
    text(94, 15, title, 11, "#59f0d4", True)
    name = view["result"] or view["name"]
    text(94, 32, name, 19, bold=True, max_width=310)
    me = view["player"]
    if preview:
        me = {"score": 425, "goals": 2, "assists": 1, "saves": 3, "shots": 5}
    text(18, 73, f"{view['playlist']}  ·  {view['rank']}", 13, "#a0b6cd")
    if phase == "training" and not preview:
        seconds = view["trainingSeconds"]
        text(18, 100, f"{seconds // 60:02}:{seconds % 60:02}", 40, bold=True)
        text(18, 164, "Tid i denne treningsøkten", 13, "#a0b6cd")
    else:
        stats = [("SCORE", me.get("score")), ("MÅL", me.get("goals")), ("SAVES", me.get("saves"))] if me and (preview or phase in ("match", "post-match")) else [("START MMR", view["startMmr"]), ("NÅVÆRENDE", view["mmr"]), ("ØKT MMR", f"{view['delta']:+}" if view["delta"] is not None else None)]
        for i, (label, value) in enumerate(stats):
            x = 17 + i * 138
            draw.rounded_rectangle((x, 101, x + 130, 165), radius=11, fill=(24, 42, 58, 235))
            text(x + 11, 109, label, 10, "#a0b6cd", True, 115)
            text(x + 11, 129, "—" if value is None else value, 23, bold=True, max_width=115)
        if me and phase in ("match", "post-match"):
            goals = " – ".join(str(t.get("score", 0)) for t in view["teams"][:2])
            text(18, 177, f"{goals}   ·   Assists {me.get('assists') if me.get('assists') is not None else '—'}   ·   Skudd {me.get('shots') if me.get('shots') is not None else '—'}", 13, "#a0b6cd")
        else:
            text(18, 177, f"{view['wins']}W / {view['losses']}L    ·    {view['streak']}", 13, "#a0b6cd")
        if phase == "post-match" and not preview:
            delta = f"{view['delta']:+} MMR" if view["delta"] is not None else "— MMR"
            text(18, 200, f"Økt: {delta}    ·    {view['wins']}W / {view['losses']}L", 12, "#a0b6cd")
        elif phase == "lobby" and view.get("nextRank") and not preview:
            text(18, 200, f"Neste rank (anslag): {view['nextRank']}", 12, "#a0b6cd")
    note = "Eksempeldata · vises i 20 sekunder" if preview else "Ctrl + Shift + O · skjul/vis"
    if view["rankStatus"] == "updating" and not preview:
        note = "Oppdaterer rank og MMR…"
    elif view["rankStatus"] == "unavailable" and not preview:
        note = "MMR ikke oppdatert · viser sist hentet"
    text(18, 228, note, 10, "#91a7bd")
    return image


class NativeOverlay:
    def __init__(self, service, logo_path, target_provider=None):
        self.service = service
        self.logo = logo_path
        self.target_provider = target_provider
        self.ready = Event()
        self.stopping = Event()
        self.hwnd = None
        self.thread = None
        self.last_frame = None
        self.position = None

    def start(self):
        if sys.platform != "win32":
            self.service.native_error = "Overlayet krever Windows."
            return
        self.thread = Thread(target=self._run, name="rl-hub-native-overlay", daemon=True)
        self.thread.start()
        self.ready.wait(3)

    def stop(self):
        self.stopping.set()
        if self.hwnd:
            self.user.PostMessageW(self.hwnd, 0x0010, 0, 0)
        if self.thread:
            self.thread.join(timeout=4)

    def _bind(self):
        self.user = c.WinDLL("user32", use_last_error=True)
        self.gdi = c.WinDLL("gdi32", use_last_error=True)
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        prototypes = [
            (self.user, "GetForegroundWindow", [], w.HWND),
            (self.user, "GetWindowThreadProcessId", [w.HWND, c.POINTER(w.DWORD)], w.DWORD),
            (self.user, "GetClientRect", [w.HWND, c.POINTER(w.RECT)], w.BOOL),
            (self.user, "ClientToScreen", [w.HWND, c.POINTER(w.POINT)], w.BOOL),
            (self.user, "GetDpiForWindow", [w.HWND], w.UINT),
            (self.user, "ShowWindow", [w.HWND, c.c_int], w.BOOL),
            (self.user, "SetWindowPos", [w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT], w.BOOL),
            (self.user, "PostMessageW", [w.HWND, w.UINT, w.WPARAM, w.LPARAM], w.BOOL),
            (self.user, "DestroyWindow", [w.HWND], w.BOOL),
            (self.user, "DefWindowProcW", [w.HWND, w.UINT, w.WPARAM, w.LPARAM], c.c_ssize_t),
            (self.user, "CreateWindowExW", [w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, c.c_int, c.c_int, c.c_int, c.c_int, w.HWND, w.HMENU, w.HINSTANCE, c.c_void_p], w.HWND),
            (self.user, "GetDC", [w.HWND], w.HDC),
            (self.user, "ReleaseDC", [w.HWND, w.HDC], c.c_int),
            (self.gdi, "CreateCompatibleDC", [w.HDC], w.HDC),
            (self.gdi, "CreateDIBSection", [w.HDC, c.c_void_p, w.UINT, c.POINTER(c.c_void_p), w.HANDLE, w.DWORD], w.HBITMAP),
            (self.gdi, "SelectObject", [w.HDC, w.HANDLE], w.HANDLE),
            (self.gdi, "DeleteObject", [w.HANDLE], w.BOOL),
            (self.gdi, "DeleteDC", [w.HDC], w.BOOL),
            (self.kernel, "GetModuleHandleW", [w.LPCWSTR], w.HMODULE),
            (self.kernel, "OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            (self.kernel, "QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)], w.BOOL),
            (self.kernel, "CloseHandle", [w.HANDLE], w.BOOL),
        ]
        for library, name, args, result in prototypes:
            fn = getattr(library, name)
            fn.argtypes, fn.restype = args, result
        self.user.UpdateLayeredWindow.argtypes = [w.HWND, w.HDC, c.POINTER(w.POINT), c.POINTER(w.SIZE), w.HDC, c.POINTER(w.POINT), w.DWORD, c.c_void_p, w.DWORD]
        self.user.UpdateLayeredWindow.restype = w.BOOL
        self.user.RegisterHotKey.argtypes = [w.HWND, c.c_int, w.UINT, w.UINT]
        self.user.UnregisterHotKey.argtypes = [w.HWND, c.c_int]
        self.user.SetTimer.argtypes = [w.HWND, c.c_size_t, w.UINT, c.c_void_p]
        self.user.KillTimer.argtypes = [w.HWND, c.c_size_t]

    def _target(self, preview):
        if self.target_provider:
            return self.target_provider(preview)
        hwnd = self.user.GetForegroundWindow()
        if not hwnd:
            return None
        if not preview:
            pid = w.DWORD()
            self.user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            process = self.kernel.OpenProcess(0x1000, False, pid)
            if not process:
                return None
            try:
                name, length = c.create_unicode_buffer(1024), w.DWORD(1024)
                if not self.kernel.QueryFullProcessImageNameW(process, 0, name, c.byref(length)) or Path(name.value).name.casefold() != "rocketleague.exe":
                    return None
            finally:
                self.kernel.CloseHandle(process)
        rect, origin = w.RECT(), w.POINT()
        if not self.user.GetClientRect(hwnd, c.byref(rect)) or not self.user.ClientToScreen(hwnd, c.byref(origin)):
            return None
        return (origin.x, origin.y, rect.right, rect.bottom, self.user.GetDpiForWindow(hwnd) / 96 or 1)

    def _paint(self, image, x, y):
        class Header(c.Structure):
            _fields_ = [("size", w.DWORD), ("width", w.LONG), ("height", w.LONG), ("planes", w.WORD), ("bits", w.WORD), ("compression", w.DWORD), ("imageSize", w.DWORD), ("xppm", w.LONG), ("yppm", w.LONG), ("colors", w.DWORD), ("important", w.DWORD)]
        class Blend(c.Structure):
            _fields_ = [("op", c.c_ubyte), ("flags", c.c_ubyte), ("alpha", c.c_ubyte), ("format", c.c_ubyte)]
        screen = self.user.GetDC(None)
        dc = self.gdi.CreateCompatibleDC(screen)
        header = Header(c.sizeof(Header), image.width, -image.height, 1, 32, 0, 0, 0, 0, 0, 0)
        buffer = c.c_void_p()
        bitmap = self.gdi.CreateDIBSection(dc, c.byref(header), 0, c.byref(buffer), None, 0)
        if not bitmap:
            self.gdi.DeleteDC(dc)
            self.user.ReleaseDC(None, screen)
            raise c.WinError(c.get_last_error())
        previous = self.gdi.SelectObject(dc, bitmap)
        try:
            # RGBa is Pillow's premultiplied-alpha representation, required by Win32.
            raw = image.convert("RGBa").tobytes("raw", "BGRa")
            c.memmove(buffer, raw, len(raw))
            pos, size, source = w.POINT(x, y), w.SIZE(image.width, image.height), w.POINT(0, 0)
            blend = Blend(0, 0, 255, 1)
            if not self.user.UpdateLayeredWindow(self.hwnd, screen, c.byref(pos), c.byref(size), dc, c.byref(source), 0, c.byref(blend), 2):
                raise c.WinError(c.get_last_error())
        finally:
            self.gdi.SelectObject(dc, previous)
            self.gdi.DeleteObject(bitmap)
            self.gdi.DeleteDC(dc)
            self.user.ReleaseDC(None, screen)

    def _tick(self):
        view = self.service.view()
        target = self._target(view["preview"])
        visible = bool(target and (view["preview"] or view["settings"]["enabled"]) and (view["preview"] or view["phase"] != "hidden"))
        if not visible:
            if self.service.visible:
                self.user.ShowWindow(self.hwnd, 0)
            self.service.visible = False
            self.last_frame = None
            return
        left, top, width, height, dpi = target
        scale = min(dpi * view["settings"]["scale"] / 100, max(.25, width / 470), max(.25, height / 280))
        card_width, card_height = round(440 * scale), round(250 * scale)
        margin = round(18 * scale)
        position = view["settings"]["position"]
        x = left + (width - card_width - margin if position.endswith("right") else margin)
        y = top + (height - card_height - margin if position.startswith("bottom") else margin)
        # Native status flags change on show/hide and must not trigger frame redraws.
        key = json.dumps({k: v for k, v in view.items() if k not in ("visible", "nativeReady", "nativeError", "hotkey")}, sort_keys=True) + str((x, y, card_width, card_height))
        if not self.user.SetWindowPos(self.hwnd, w.HWND(-1), x, y, 0, 0, 0x0010 | 0x0001):
            raise c.WinError(c.get_last_error())
        if not self.service.visible:
            self.user.ShowWindow(self.hwnd, 4)
        if key != self.last_frame:
            image = render_card(view, self.logo)
            if image.size != (card_width, card_height):
                image = image.resize((card_width, card_height), Image.Resampling.LANCZOS)
            self._paint(image, x, y)
            self.last_frame = key
        self.service.visible = True
        self.service.native_error = ""

    def _run(self):
        atom = None
        try:
            self._bind()
            self.user.SetThreadDpiAwarenessContext.argtypes = [w.HANDLE]
            self.user.SetThreadDpiAwarenessContext.restype = w.HANDLE
            self.user.SetThreadDpiAwarenessContext(w.HANDLE(-4))
            proc_type = c.WINFUNCTYPE(c.c_ssize_t, w.HWND, w.UINT, w.WPARAM, w.LPARAM)
            def dispatch(hwnd, message, wp, lp):
                if message == 0x0113:
                    try:
                        self._tick()
                    except Exception:
                        self.service.native_error = "Overlayet kunne ikke oppdateres."
                        logging.exception("Could not update native overlay")
                    return 0
                if message == 0x0312:
                    self.service.configure({"enabled": not self.service.settings["enabled"]})
                    return 0
                if message == 0x0010:
                    self.user.DestroyWindow(hwnd)
                    return 0
                if message == 0x0002:
                    self.user.PostQuitMessage(0)
                    return 0
                return self.user.DefWindowProcW(hwnd, message, wp, lp)
            self.callback = proc_type(dispatch)
            class WindowClass(c.Structure):
                _fields_ = [("style", w.UINT), ("proc", proc_type), ("classExtra", c.c_int), ("windowExtra", c.c_int), ("instance", w.HINSTANCE), ("icon", w.HICON), ("cursor", w.HANDLE), ("background", w.HBRUSH), ("menu", w.LPCWSTR), ("name", w.LPCWSTR)]
            instance = self.kernel.GetModuleHandleW(None)
            class_name = "RLHubOverlay-" + str(id(self))
            wc = WindowClass(0, self.callback, 0, 0, instance, None, None, None, None, class_name)
            self.user.RegisterClassW.argtypes = [c.POINTER(WindowClass)]
            self.user.UnregisterClassW.argtypes = [w.LPCWSTR, w.HINSTANCE]
            atom = self.user.RegisterClassW(c.byref(wc))
            if not atom:
                raise c.WinError(c.get_last_error())
            styles = 0x00080000 | 0x00000020 | 0x08000000 | 0x00000080 | 0x00000008
            self.hwnd = self.user.CreateWindowExW(styles, class_name, "RL Hub Overlay", 0x80000000, 0, 0, 440, 226, None, None, instance, None)
            if not self.hwnd:
                raise c.WinError(c.get_last_error())
            self.service.hotkey = bool(self.user.RegisterHotKey(self.hwnd, 1, 0x4000 | 0x0002 | 0x0004, ord("O")))
            self.user.SetTimer(self.hwnd, 1, 250, None)
            self.service.native_ready = True
            self.ready.set()
            message = w.MSG()
            self.user.GetMessageW.argtypes = [c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
            self.user.TranslateMessage.argtypes = [c.POINTER(w.MSG)]
            self.user.DispatchMessageW.argtypes = [c.POINTER(w.MSG)]
            if self.stopping.is_set():
                self.user.PostMessageW(self.hwnd, 0x0010, 0, 0)
            while self.user.GetMessageW(c.byref(message), None, 0, 0) > 0:
                self.user.TranslateMessage(c.byref(message))
                self.user.DispatchMessageW(c.byref(message))
        except Exception:
            logging.exception("Could not start native overlay")
            self.service.native_error = "Windows-overlayet kunne ikke startes. Se desktop.log."
        finally:
            if self.hwnd:
                self.user.KillTimer(self.hwnd, 1)
                self.user.UnregisterHotKey(self.hwnd, 1)
                if self.service.native_ready:
                    self.user.DestroyWindow(self.hwnd)
            if atom:
                self.user.UnregisterClassW(class_name, instance)
            self.hwnd = None
            self.service.native_ready = False
            self.service.visible = False
            self.ready.set()

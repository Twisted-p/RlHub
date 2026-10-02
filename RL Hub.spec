# Build with: .venv\Scripts\python.exe -m PyInstaller --noconfirm "RL Hub.spec"
from pathlib import Path
from PIL import Image

root = Path(SPECPATH)
icon = root / "build" / "rl-hub.ico"
icon.parent.mkdir(exist_ok=True)
with Image.open(root / "App Logo.png") as image:
    image.save(icon, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

assets = [
    "index.html", "dashboard.html", "garage.html", "training.html", "profile.html",
    "script.js", "styles.css", "desktop-runtime.js", "App Logo.png", "performance.html", "performance.js",
    "assets/rlhub-intro.mp4",
    "overlay.html", "overlay-settings.js",
    "performance-analytics.js",
    "readiness.js",
    "goals.html", "goals.js",
    "garage.js", "garage.css", "garage-presets.js",
    "assets/garage/zen.jpeg", "assets/garage/jstn.png",
    "assets/garage/squishy.jpeg", "assets/garage/retals.jpeg",
]
a = Analysis(
    [str(root / "desktop_app.py")],
    pathex=[str(root)],
    datas=[(str(root / name), str(Path(name).parent)) for name in assets],
    binaries=[], hiddenimports=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "gtk", "gi"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="RL Hub", debug=False, strip=False, upx=False, console=False,
    icon=str(icon),
)

"""Build a complete Windows x64 ZIP from verified prerequisite payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(destination, webview, widget_zip, release_version, executable=None):
    destination.mkdir(parents=True, exist_ok=True)
    package = destination / 'RL Hub Complete'
    package.mkdir(exist_ok=True)
    assert webview.stat().st_size > 100_000_000, 'Expected full offline installer, not a bootstrapper'
    executable = executable or ROOT / 'dist/RL Hub.exe'
    shutil.copy2(executable, destination / 'RL Hub.exe')
    shutil.copy2(executable, package / 'RL Hub.exe')
    dependency = package / 'Dependencies/WebView2/MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
    dependency.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(webview, dependency)
    for name in ('Start RL Hub.cmd', 'Start-RLHub.ps1', 'RuntimeSetup.psm1', 'Install Fullscreen Overlay.cmd', 'Install-Fullscreen.ps1', 'READ ME FIRST.txt'):
        shutil.copy2(ROOT / 'distribution' / name, package / name)
    (package / 'gamebar').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'gamebar/Install-Widget.ps1', package / 'gamebar/Install-Widget.ps1')
    with zipfile.ZipFile(widget_zip) as source:
        assert source.testzip() is None
        for name in source.namelist():
            if name.startswith('dist/gamebar/') and not name.endswith('/'):
                target = (package / name).resolve()
                assert target.is_relative_to(package.resolve()), 'Unsafe archive path'
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read(name))
    msix = list((package / 'dist/gamebar').rglob('RLHubGameBar*.msix'))
    assert len(msix) == 1
    ns = {'a':'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}
    with zipfile.ZipFile(msix[0]) as archive:
        manifest = ET.fromstring(archive.read('AppxManifest.xml'))
    dependencies = {}
    for path in msix[0].parent.joinpath('Dependencies/x64').glob('*.appx'):
        with zipfile.ZipFile(path) as archive:
            identity = ET.fromstring(archive.read('AppxManifest.xml')).find('a:Identity', ns)
            assert identity.attrib['ProcessorArchitecture'].lower() == 'x64'
            dependencies[identity.attrib['Name']] = identity.attrib['Version']
    for expected in manifest.findall('a:Dependencies/a:PackageDependency', ns):
        name, version = expected.attrib['Name'], expected.attrib['MinVersion']
        assert name in dependencies, 'Missing widget dependency: ' + name
        assert tuple(map(int, dependencies[name].split('.'))) >= tuple(map(int, version.split('.'))), name
    for name in ('README.md', 'CODEX_HANDOFF.md', 'STANDALONE_SETUP.md', 'SETTINGS_SOURCES.md', 'RANK_CELEBRATION_HANDOFF.md'):
        shutil.copy2(ROOT / name, package / name)
    shutil.copy2(ROOT / 'frontend/lanyard/REACT_BITS_LICENSE.md', package / 'REACT_BITS_LICENSE.md')
    manifest_info = {'version':release_version, 'architecture':'x64', 'webview2':'offline Evergreen standalone installer',
        'webview2Source':'https://go.microsoft.com/fwlink/?LinkId=2124701',
        'widgetVersion':manifest.find('a:Identity',ns).attrib['Version'], 'widgetDependencies':dependencies,
        'gameBar':'Optional for fullscreen; Microsoft Store installation if absent'}
    (package / 'DEPENDENCIES.json').write_text(json.dumps(manifest_info, indent=2), encoding='utf-8')
    files = sorted(p for p in package.rglob('*') if p.is_file() and p.name != 'PACKAGE-SHA256SUMS.txt')
    (package / 'PACKAGE-SHA256SUMS.txt').write_text(''.join(f'{digest(p)}  {p.relative_to(package).as_posix()}\n' for p in files), encoding='utf-8')
    output = destination / 'RL Hub Complete.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(p for p in package.rglob('*') if p.is_file()):
            archive.write(path, path.relative_to(package).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for path in files:
            assert hashlib.sha256(archive.read(path.relative_to(package).as_posix())).hexdigest() == digest(path)
    (destination / 'SHA256SUMS.txt').write_text(''.join(f'{digest(destination / name)}  {name}\n' for name in ('RL Hub.exe','RL Hub Complete.zip')), encoding='utf-8')
    print(json.dumps({'zip':str(output),'bytes':output.stat().st_size,'files':len(files)+1,'widgetDependencies':dependencies}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--webview', type=Path, required=True)
    parser.add_argument('--widget-zip', type=Path, required=True)
    parser.add_argument('--exe', type=Path, help='Verified executable; defaults to dist/RL Hub.exe')
    args = parser.parse_args()
    build(args.output.resolve(), args.webview.resolve(), args.widget_zip.resolve(), args.version, args.exe.resolve() if args.exe else None)

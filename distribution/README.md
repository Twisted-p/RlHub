# Complete Windows release

Release asset: `RL Hub Complete.zip` (GitHub normalizes its asset name to
`RL.Hub.Complete.zip`). GitHub's automatic Source code ZIP is a developer archive,
not the runnable distribution.

The complete package ships:
- Tested `RL Hub.exe`, including Python, pywebview/CLR interop and app libraries.
- Bundled React/Three/Rapier/WASM, models, rank icons and other UI assets.
- Microsoft WebView2 Evergreen **offline x64 standalone installer**, not the online
  bootstrapper. Retrieved from https://go.microsoft.com/fwlink/?LinkId=2124701.
- RL Hub Game Bar widget 1.0.2.0 and its three x64 packages: VCLibs 14,
  .NET Native Framework 2.2 and .NET Native Runtime 2.2.
- Checked launch/setup scripts, English instructions and SHA-256 file manifests.

Use `Start RL Hub.cmd`; the launcher checks Microsoft's documented registry entries
and installs WebView2 only if missing. It validates the Microsoft signature before
executing the offline installer. Normal app use does not require Game Bar.
`Install Fullscreen Overlay.cmd` checks Windows 11 and Game Bar, installs the
unsigned development widget using the existing installer, and scopes loopback
access to the widget. If Game Bar itself is absent, it opens its official Store
page (https://apps.microsoft.com/detail/9nzkpstsnw4p). The Windows Store application
is not bundled as an offline payload. The standard supported Windows 11 x64 OS
supplies .NET Framework; a fresh Windows VM/offline installation has not been
tested on this development PC. No claim is made for modified Windows images.

Build the app with `RL Hub.spec`, test `tests/packaged_smoke.py`, then download the
Microsoft offline installer and verify its Authenticode signature is Valid and
its signer is Microsoft Corporation. Fetch the previous fullscreen ZIP from the
authenticated release API and verify its published SHA-256 digest. Then run:

```powershell
.\.venv\Scripts\python.exe distribution/build_release.py --version 0.6.0 --exe "dist/latest/RL Hub.exe" --output ../work/release-0.6.0 --webview ../work/MicrosoftEdgeWebView2RuntimeInstallerX64.exe --widget-zip ../work/fullscreen-0.3.0.zip
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/distribution_setup.test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '../work/release-0.6.0/RL Hub Complete/Start-RLHub.ps1' -CheckOnly
```

Use a new output directory for each release. The builder verifies all archive
bytes, the app digest, every widget dependency's identity/architecture/minimum
version, and rejects a small online bootstrapper instead of the offline installer.
Test extraction and run the packaged smoke test against the extracted executable.
The setup unit test simulates missing/already-present/untrusted runtimes without
uninstalling or changing the developer machine's shared Windows runtime.
Generated installers/ZIPs belong in ignored `work`, `dist` or GitHub release assets,
not source history. Do not package the user's LocalAppData or game logs.

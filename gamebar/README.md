# Fullscreen Game Bar renderer

The Windows Game Bar widget reads only RL Hub's `http://127.0.0.1:18765/api/overlay/frame` PNG endpoint. RL Hub remains responsible for player identity, live stats, session history and visibility toggles. Selecting `renderer=gamebar` disables the desktop card to prevent duplicates. Game Bar controls pinning, placement, size and mouse click-through. Desktop corner/scale settings apply only to the desktop renderer.

Windows 11 and Xbox Game Bar are required for the unsigned development package. The package has Microsoft's special unsigned identity OID and does not require trusting a signing certificate. `Install-Widget.ps1` needs Windows administrator elevation to install executable unsigned MSIX content and configure a loopback exemption scoped to this package. It does not modify the game, anti-cheat, fullscreen options or global compatibility flags. This is a development installation; public distribution should use a signed package or the Microsoft Store.

Build locally with Visual Studio 2022, UWP C# tools and Windows SDK 10.0.19041:

```powershell
msbuild gamebar/RLHubGameBar.csproj /restore /p:Configuration=Release /p:Platform=x64 /p:GenerateAppxPackageOnBuild=true /p:AppxBundle=Never /p:UapAppxPackageBuildMode=SideloadOnly
```

The `Build Game Bar overlay` GitHub Actions workflow provides the same package and x64 runtime dependencies as a downloadable artifact. Do not commit `bin`, `obj` or generated packages. Install the artifact under `dist/gamebar`, then run `gamebar/Install-Widget.ps1` from an elevated PowerShell window. Open Win+G, select RL Hub from Widgets and pin it. Enable Game Bar mouse click-through and close Win+G. Keep RL Hub running. Choose Fullscreen in its Overlay tab and save.

The widget clears its previous image on connection loss. The `gamebarConnected` status reports requests from the widget within the last three seconds; it is not proof of visible pixels or exclusive-fullscreen compatibility. Verify the actual widget over Rocket League with Fullscreen selected before claiming that the issue is fixed. Game Bar depends on the Windows graphics presentation path; no claim is made for all drivers or true exclusive presentation with fullscreen optimizations disabled.

Manifest activation and metadata registration are adapted from Microsoft's [XboxGameBarSamples](https://github.com/microsoft/XboxGameBarSamples). The original MIT license is included. The SDK is a NuGet dependency, not vendored source.

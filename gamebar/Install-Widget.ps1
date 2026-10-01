# Run in an elevated PowerShell window. No certificate or anti-cheat changes.
param([string]$PackageDirectory = "$PSScriptRoot\..\dist\gamebar")
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Get-PackageIdentity([string]$Path) {
    $archive = [IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $reader = [IO.StreamReader]::new($archive.GetEntry('AppxManifest.xml').Open())
        try { return ([xml]$reader.ReadToEnd()).Package.Identity }
        finally { $reader.Dispose() }
    } finally { $archive.Dispose() }
}
$package = Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File |
    Where-Object { $_.Name -like 'RLHubGameBar*' -and $_.Extension -in @('.msix', '.appx') } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $package) { throw 'Fant ikke RL Hub-widgetpakken. Bygg eller last ned den først.' }
$dependencies = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -Filter '*.appx' |
    Where-Object { $_.FullName -match '\\Dependencies\\x64\\' } | ForEach-Object {
        $identity = Get-PackageIdentity $_.FullName
        $existing = Get-AppxPackage -Name $identity.Name | Where-Object {
            $_.Architecture -eq 'X64' -and [version]$_.Version -ge [version]$identity.Version
        }
        # Reinstalling a shared runtime can require closing unrelated apps.
        # Leave an installed compatible runtime alone.
        if (-not $existing) { $_.FullName }
    })
if ($dependencies.Count) {
    Add-AppxPackage -Path $package.FullName -DependencyPath $dependencies -AllowUnsigned
} else {
    Add-AppxPackage -Path $package.FullName -AllowUnsigned
}
$installed = Get-AppxPackage -Name 'RLHub.GameBar'
if (-not $installed) { throw 'Windows bekreftet ikke installasjonen.' }
# A UWP widget needs access to RL Hub's localhost service. This exemption only
# applies to this package; it does not change the firewall or any other app.
& "$env:WINDIR\System32\CheckNetIsolation.exe" LoopbackExempt -a "-n=$($installed.PackageFamilyName)"
if ($LASTEXITCODE -ne 0) { throw 'Kunne ikke gi widgeten tilgang til den lokale RL Hub-appen.' }
Write-Output 'RL Hub-widgeten er klar. Velg Fullskjerm i RL Hub. Åpne Win + G, velg RL Hub og fest med tegnestiften.'

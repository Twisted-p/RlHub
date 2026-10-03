param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Denne pakken krever 64-bit Windows.' }
    Import-Module (Join-Path $PSScriptRoot 'RuntimeSetup.psm1') -Force
    if ($CheckOnly) {
        [pscustomobject]@{WebView2 = Get-WebView2Version; GameBar = [bool](Get-AppxPackage -Name Microsoft.XboxGamingOverlay); App = Test-Path -LiteralPath (Join-Path $PSScriptRoot 'RL Hub.exe')} | ConvertTo-Json
        exit 0
    }
    Install-WebView2IfMissing -PackageRoot $PSScriptRoot
    $app = Join-Path $PSScriptRoot 'RL Hub.exe'
    if (-not (Test-Path -LiteralPath $app)) { throw 'RL Hub.exe mangler. Pakk ut hele ZIP-filen.' }
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:18765/health' -TimeoutSec 2
        if ($health.app -eq 'rl-hub-desktop') { Write-Host 'RL Hub er allerede apen. Lukk den gamle appen for a bruke dette bygget.'; exit 0 }
    } catch { }
    Start-Process -FilePath $app -WorkingDirectory $PSScriptRoot
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

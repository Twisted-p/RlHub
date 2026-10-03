param([switch]$Elevated)
$ErrorActionPreference = 'Stop'
try {
    if ([Environment]::OSVersion.Version.Build -lt 22000) { throw 'Den medfolgende fullskjerm-widgeten krever Windows 11. Bruk kantlost vindu pa denne PC-en.' }
    if (-not (Get-AppxPackage -Name Microsoft.XboxGamingOverlay)) {
        Write-Host 'Xbox Game Bar mangler. Microsoft Store apnes. Installer Game Bar og kjor denne filen igjen.'
        Start-Process 'ms-windows-store://pdp/?ProductId=9NZKPSTSNW4P'
        exit 1
    }
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $admin) {
        if ($Elevated) { throw 'Installasjonen trenger administratortillatelse.' }
        $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Elevated'
        $child = Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs -Wait -PassThru -WindowStyle Hidden
        exit $child.ExitCode
    }
    & (Join-Path $PSScriptRoot 'gamebar\Install-Widget.ps1') -PackageDirectory (Join-Path $PSScriptRoot 'dist\gamebar')
    if ($LASTEXITCODE -ne 0) { throw 'Widgetoppsettet ble ikke fullfort.' }
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show('RL Hub-widgeten er klar. Velg Fullskjerm i Overlay, trykk Win+G, velg RL Hub under Widgets og fest den med tegnestiften.','RL Hub') | Out-Null
} catch {
    if ($Elevated) {
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.MessageBox]::Show($_.Exception.Message,'RL Hub-oppsett') | Out-Null
    } else { Write-Host $_.Exception.Message -ForegroundColor Red }
    exit 1
}

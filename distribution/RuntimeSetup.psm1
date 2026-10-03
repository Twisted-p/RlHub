# Offline prerequisite helpers. Only the release ZIP contains installer binaries.
Set-StrictMode -Version Latest
function Get-WebView2Version {
    $client = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    foreach ($path in @("HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$client", "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$client", "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$client")) {
        $item = Get-ItemProperty -LiteralPath $path -Name pv -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            $version = $null
            if ([version]::TryParse([string]$item.pv, [ref]$version) -and $version -gt [version]'0.0.0.0') { return $version.ToString() }
        }
    }
    return $null
}
function Install-WebView2IfMissing {
    param([Parameter(Mandatory)][string]$PackageRoot)
    $installed = Get-WebView2Version
    if ($installed) { Write-Host "WebView2 er allerede installert ($installed)."; return }
    $installer = Join-Path $PackageRoot 'Dependencies\WebView2\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
    if (-not (Test-Path -LiteralPath $installer)) { throw 'WebView2-installer mangler. Pakk ut hele RL Hub Complete.zip, ikke bare appen.' }
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') { throw 'Microsoft-signaturen til WebView2 kunne ikke bekreftes. Last ned pakken pa nytt.' }
    Write-Host 'Installerer WebView2 fra den medfolgende offline-installeren. Dette kan ta et par minutter.'
    $process = Start-Process -FilePath $installer -ArgumentList '/silent','/install' -Wait -PassThru -WindowStyle Hidden
    if (-not (Get-WebView2Version)) { throw "WebView2 ble ikke bekreftet etter installasjon (kode $($process.ExitCode)). Kjor installeren i Dependencies\WebView2 manuelt, eller kontakt IT hvis PC-en er administrert." }
    Write-Host 'WebView2 er klar.'
}
Export-ModuleMember -Function Get-WebView2Version, Install-WebView2IfMissing

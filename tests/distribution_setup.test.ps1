$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '..\distribution\RuntimeSetup.psm1'
$module = Import-Module $source -Force -PassThru
& $module {
    function Get-WebView2Version { '150.0.0.0' }
    function Start-Process { throw 'An installed runtime must not run an installer' }
    Install-WebView2IfMissing -PackageRoot 'C:\unused'
}
$module = Import-Module $source -Force -PassThru
& $module {
    $script:calls = 0
    function Get-WebView2Version { if ($script:calls) { '150.0.0.0' } else { $null } }
    function Test-Path { param($LiteralPath) $true }
    function Get-AuthenticodeSignature { param($LiteralPath) [pscustomobject]@{Status='Valid';SignerCertificate=[pscustomobject]@{Subject='CN=Microsoft Corporation, O=Microsoft Corporation'}} }
    function Start-Process { param($FilePath,$ArgumentList,[switch]$Wait,[switch]$PassThru,$WindowStyle)
        if (($ArgumentList -join ' ') -ne '/silent /install') { throw 'Incorrect installer arguments' }
        if ($FilePath -notlike '*Dependencies\WebView2\MicrosoftEdgeWebView2RuntimeInstallerX64.exe') { throw 'Not the bundled installer' }
        $script:calls++; [pscustomobject]@{ExitCode=0}
    }
    Install-WebView2IfMissing -PackageRoot 'C:\test package'
    if ($script:calls -ne 1) { throw 'Missing runtime was not installed once' }
}
$module = Import-Module $source -Force -PassThru
& $module {
    function Get-WebView2Version { $null }
    function Test-Path { param($LiteralPath) $true }
    function Get-AuthenticodeSignature { param($LiteralPath) [pscustomobject]@{Status='NotSigned';SignerCertificate=$null} }
    function Start-Process { throw 'Untrusted installer was executed' }
    $rejected = $false
    try { Install-WebView2IfMissing -PackageRoot 'C:\test' } catch { $rejected = $_.Exception.Message -like '*signaturen*' }
    if (-not $rejected) { throw 'Invalid signature was not rejected' }
}
Write-Output 'Distribution setup: installed runtime skipped; missing runtime uses bundled offline installer; untrusted installer rejected OK'

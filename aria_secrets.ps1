# aria_secrets.ps1 -- shared helpers for ARIA's encrypted secrets
#
# Secrets are stored encrypted with Windows DPAPI (the same protection
# Windows Credential Manager uses). Each one is a small file under:
#     %LOCALAPPDATA%\ARIA\secrets\<NAME>.dpapi
# It can only be decrypted by YOUR Windows account on THIS PC - copying
# the file to another user or machine makes it useless.
#
# This file is not run directly - the other scripts load it with:
#     . "$PSScriptRoot\aria_secrets.ps1"

$AriaSecretsDir = Join-Path $env:LOCALAPPDATA "ARIA\secrets"

# Every secret listed here is sent to the NAS by deploy.ps1 and loaded
# by run_local.ps1. Add a name here after storing it with set_secret.ps1.
$AriaSecretNames = @(
    "UNIFI_API_KEY"
)

function Get-AriaSecretPath([string]$Name) {
    return (Join-Path $AriaSecretsDir "$Name.dpapi")
}

# Decrypts a secret and returns it as a normal string, in memory only.
# Only call this right before the value is needed, and never print it.
function Get-AriaSecret([string]$Name) {
    $path = Get-AriaSecretPath $Name
    if (-not (Test-Path $path)) {
        throw "Secret '$Name' is not stored yet - run: .\set_secret.ps1 -Name $Name"
    }
    $secure = Get-Content -Path $path | ConvertTo-SecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        # Wipe the unencrypted copy from unmanaged memory straight away
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

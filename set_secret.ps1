# set_secret.ps1 -- store (or replace) an ARIA secret, encrypted with DPAPI
#
# Usage:
#     .\set_secret.ps1 -Name UNIFI_API_KEY
#
# You'll be asked to paste the value. Nothing is shown on screen, and the
# value is never written anywhere in plain text - it goes straight from a
# SecureString into an encrypted file (see aria_secrets.ps1).

param(
    [Parameter(Mandatory = $true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\aria_secrets.ps1"

$secure = Read-Host "Paste the value for $Name (input is hidden)" -AsSecureString
if ($secure.Length -eq 0) {
    Write-Host "Nothing entered - nothing was saved." -ForegroundColor Yellow
    exit 1
}

New-Item -ItemType Directory -Force -Path $AriaSecretsDir | Out-Null

# ConvertFrom-SecureString (without -Key) encrypts with DPAPI for the
# current Windows user - the output is ciphertext, not the secret.
$secure | ConvertFrom-SecureString | Set-Content -Path (Get-AriaSecretPath $Name)

Write-Host "$Name saved (encrypted) to $(Get-AriaSecretPath $Name)" -ForegroundColor Green
if ($AriaSecretNames -notcontains $Name) {
    Write-Host "Note: add '$Name' to `$AriaSecretNames in aria_secrets.ps1 so deploy.ps1 sends it to the NAS." -ForegroundColor Yellow
}

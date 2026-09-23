# run_local.ps1 -- run ARIA on this PC with secrets loaded from the vault
#
# Usage:
#     .\run_local.ps1
#
# Decrypts each secret into an environment variable that only exists for
# this PowerShell process, runs ARIA, then removes the variables again.
# Nothing is written to .env or any other file.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\aria_secrets.ps1"

try {
    foreach ($name in $AriaSecretNames) {
        Set-Item -Path "Env:$name" -Value (Get-AriaSecret $name)
    }
    python "$PSScriptRoot\main.py"
} finally {
    foreach ($name in $AriaSecretNames) {
        Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
    }
}

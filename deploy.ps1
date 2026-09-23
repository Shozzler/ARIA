# deploy.ps1 -- One-click redeploy for ARIA on the QNAP NAS
#
# What this does, in order:
#   1. Copies your local ARIA folder to the NAS (overwrites changed files)
#   2. Sends the encrypted secrets (see aria_secrets.ps1) to the NAS .env
#   3. Rebuilds the Docker image on the NAS over SSH
#   4. Reminds you to click "Recreate" in Container Station to finish up
#
# Run it from PowerShell with:  .\deploy.ps1

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\aria_secrets.ps1"

$LocalRoot  = "C:\Users\sford\Documents\ARIA"
$LocalPath  = "$LocalRoot\*"
$RemoteUser = "AriaSSH"
$RemoteHost = "10.20.40.23"
$RemotePort = "58997"
$RemotePath = "/share/CACHEDEV1_DATA/Container/ARIA/"
$ImageName  = "docker-compose-aria"

# Decrypt the secrets first, so a missing secret stops the deploy BEFORE
# anything on the NAS is touched (instead of leaving it half-updated).
$secretLines = foreach ($name in $AriaSecretNames) { "$name=$(Get-AriaSecret $name)" }

Write-Host "==> Step 1/3: Copying files to the NAS..." -ForegroundColor Cyan
# Note: scp's wildcard (*) follows Unix glob rules and does NOT match
# dotfiles like .env, so we copy those separately and explicitly.
scp -O -P $RemotePort -r $LocalPath "${RemoteUser}@${RemoteHost}:${RemotePath}"
scp -O -P $RemotePort "$LocalRoot\.env" "${RemoteUser}@${RemoteHost}:${RemotePath}.env"

Write-Host ""
Write-Host "==> Step 2/3: Sending secrets to the NAS..." -ForegroundColor Cyan
# The secrets are decrypted in memory only and piped through the (encrypted)
# SSH connection's stdin - never written to a file on this PC and never put
# on the command line, where they could show up in process lists or history.
# On the NAS they're appended to the .env that was just copied, and .env is
# locked to its owner (chmod 600). tr strips the Windows CR line endings.
$secretPayload = "`n" + ($secretLines -join "`n") + "`n"
$appendCommand = "cd $RemotePath && umask 077 && tr -d '\r' >> .env && chmod 600 .env"
$secretPayload | ssh "${RemoteUser}@${RemoteHost}" -p $RemotePort $appendCommand
Remove-Variable secretLines, secretPayload
if ($LASTEXITCODE -ne 0) { throw "Sending secrets to the NAS failed" }
Write-Host "    Sent: $($AriaSecretNames -join ', ')"

Write-Host ""
Write-Host "==> Step 3/3: Rebuilding the Docker image on the NAS..." -ForegroundColor Cyan
$buildCommand = "export PATH=`$PATH:/share/CACHEDEV1_DATA/.qpkg/container-station/bin; " +
                "export DOCKER_CONFIG=/tmp/docker-config; mkdir -p /tmp/docker-config; " +
                "cd /share/CACHEDEV1_DATA/Container/ARIA; " +
                "docker build -t $ImageName ."
ssh "${RemoteUser}@${RemoteHost}" -p $RemotePort $buildCommand

Write-Host ""
Write-Host "==> Done! Now go to Container Station and click 'Recreate' on the aria app." -ForegroundColor Green
Write-Host "==> Then check http://${RemoteHost}:5000 (hard refresh with Ctrl+F5)." -ForegroundColor Green

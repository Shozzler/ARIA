# deploy.ps1 -- One-click redeploy for ARIA on the QNAP NAS
#
# What this does, in order:
#   1. Copies your local ARIA folder to the NAS (overwrites changed files)
#   2. Rebuilds the Docker image on the NAS over SSH
#   3. Reminds you to click "Recreate" in Container Station to finish up
#
# Run it from PowerShell with:  .\deploy.ps1

$ErrorActionPreference = "Stop"

$LocalRoot  = "C:\Users\sford\Documents\ARIA"
$LocalPath  = "$LocalRoot\*"
$RemoteUser = "AriaSSH"
$RemoteHost = "10.20.40.23"
$RemotePort = "58997"
$RemotePath = "/share/CACHEDEV1_DATA/Container/ARIA/"
$ImageName  = "docker-compose-aria"

Write-Host "==> Step 1/2: Copying files to the NAS..." -ForegroundColor Cyan
# Note: scp's wildcard (*) follows Unix glob rules and does NOT match
# dotfiles like .env, so we copy those separately and explicitly.
scp -O -P $RemotePort -r $LocalPath "${RemoteUser}@${RemoteHost}:${RemotePath}"
scp -O -P $RemotePort "$LocalRoot\.env" "${RemoteUser}@${RemoteHost}:${RemotePath}.env"

Write-Host ""
Write-Host "==> Step 2/2: Rebuilding the Docker image on the NAS..." -ForegroundColor Cyan
$buildCommand = "export PATH=`$PATH:/share/CACHEDEV1_DATA/.qpkg/container-station/bin; " +
                "export DOCKER_CONFIG=/tmp/docker-config; mkdir -p /tmp/docker-config; " +
                "cd /share/CACHEDEV1_DATA/Container/ARIA; " +
                "docker build -t $ImageName ."
ssh "${RemoteUser}@${RemoteHost}" -p $RemotePort $buildCommand

Write-Host ""
Write-Host "==> Done! Now go to Container Station and click 'Recreate' on the aria app." -ForegroundColor Green
Write-Host "==> Then check http://${RemoteHost}:5000 (hard refresh with Ctrl+F5)." -ForegroundColor Green

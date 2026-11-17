# NYVERRA Alpha 0.60 - local server base-save backup. Read-only source.
# Run AFTER stopping the game/server so the copied SaveGame files are consistent.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (!(Test-Path -LiteralPath (Join-Path $root 'NYVERRA.uproject'))) {
    throw 'Run this script inside the NYVERRA project clone.'
}
$saveDir = Join-Path $root 'Saved\SaveGames'
if (!(Test-Path -LiteralPath $saveDir)) {
    Write-Host '[INFO] No Saved\SaveGames directory found: no bases to back up.'
    exit 0
}
$files = @(Get-ChildItem -LiteralPath $saveDir -Filter 'NYVERRA_Bases_v1_*.sav' -File)
if ($files.Count -eq 0) {
    Write-Host '[INFO] No NYVERRA BaseSave v1 slots found.'
    exit 0
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$target = Join-Path $root ('Saved\BaseBackups\' + $stamp)
New-Item -ItemType Directory -Path $target -Force | Out-Null
foreach ($file in $files) {
    $dest = Join-Path $target $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $dest -ErrorAction Stop
    $a = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
    if ($a -ne $b) { throw ('Backup checksum mismatch: ' + $file.Name) }
    Write-Host ('[OK] ' + $file.Name + ' SHA256 verified')
}
Write-Host ('[SUCCESS] ' + $files.Count + ' save slot(s) backed up to ' + $target)
Write-Host '[PRIVATE] Backups contain server game state and owner IDs. Never commit or share them.'

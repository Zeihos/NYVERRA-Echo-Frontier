# NYVERRA — safe offline backups of base AND player A/B SaveGame slots.
# Run ONLY after stopping Unreal Editor and the server (no live file writes).
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$project = Join-Path $root 'NYVERRA.uproject'
if (!(Test-Path -LiteralPath $project)) { throw 'Expected NYVERRA.uproject next to Tools.' }
$from = Join-Path $root 'Saved\SaveGames'
if (!(Test-Path -LiteralPath $from)) {
    Write-Host '[INFO] Saved\SaveGames directory does not exist yet.'
    exit 0
}
$selected = @(Get-ChildItem -LiteralPath $from -File |
    Where-Object { $_.Name -like 'NYVERRA_Bases_v1_*.sav' -or $_.Name -like 'NYVERRA_Player_v1_*.sav' } |
    Sort-Object Name)
if ($selected.Count -eq 0) {
    Write-Host '[INFO] No NYVERRA world or player v1 save files found.'
    exit 0
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$destination = Join-Path $root ('Saved\SnapshotBackups\' + $stamp)
if (Test-Path -LiteralPath $destination) { throw 'Backup directory collision; retry with a new timestamp.' }
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$written = 0
foreach ($file in $selected) {
    $target = Join-Path $destination $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $target -ErrorAction Stop
    $srcHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $dstHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($srcHash -ne $dstHash) { throw ('Hash mismatch for ' + $file.Name) }
    $written++
}
Write-Host ('[SUCCESS] Copied and SHA256-verified {0} save files.' -f $written)
Write-Host ('[PATH] ' + $destination)
Write-Host '[WARNING] This local backup is not off-machine protection; make an additional secure external copy.'
Write-Host '[PRIVATE] Do not upload saved worlds/player files, hashes or account metadata to public GitHub.'

# NYVERRA Alpha 0.61 — read-only inventory of local A/B SaveGame slots.
# Does not parse private Unreal .sav data, change, upload, or delete anything.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (!(Test-Path -LiteralPath (Join-Path $root 'NYVERRA.uproject'))) {
    throw 'Run this tool inside the correct NYVERRA project checkout.'
}
$saveRoot = Join-Path $root 'Saved\SaveGames'
if (!(Test-Path -LiteralPath $saveRoot)) {
    Write-Host '[INFO] No Saved\SaveGames directory exists in this checkout.'
    exit 0
}
$slots = @(Get-ChildItem -LiteralPath $saveRoot -File -Filter 'NYVERRA_Bases_v1_*.sav' |
    Sort-Object Name)
if ($slots.Count -eq 0) {
    Write-Host '[INFO] No NYVERRA BaseSave v1 files found.'
    exit 0
}
Write-Host '[NYVERRA] Found base save files (metadata only):'
foreach ($file in $slots) {
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    Write-Host ('  {0,-55} {1,9} bytes  {2:yyyy-MM-dd HH:mm:ss}  SHA256 {3}' -f
        $file.Name, $file.Length, $file.LastWriteTime, $hash.Substring(0,16))
}
Write-Host '[NOTE] The newest file timestamp does NOT prove it contains the newest valid revision.'
Write-Host '[NOTE] Unreal selects the newest VALID SaveRevision during server load.'
Write-Host '[PRIVATE] Never commit or upload Saved/SaveGames; these files may include owner identifiers.'

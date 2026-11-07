[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$MapFile
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$expected = 'https://github.com/Zeihos/NYVERRA-Echo-Frontier.git'
$expectedSSH = 'git@github.com:Zeihos/NYVERRA-Echo-Frontier.git'
$source = (Resolve-Path -LiteralPath $MapFile -ErrorAction Stop).Path

if ([IO.Path]::GetFileName($source) -ne 'TestWorld.umap') {
    throw "Expected the authored and saved TestWorld.umap; got $source"
}
if (!(Test-Path -LiteralPath (Join-Path $repo 'NYVERRA.uproject'))) {
    throw "Run this script from an extracted/checked-out NYVERRA repo containing NYVERRA.uproject"
}
if (!(Test-Path -LiteralPath (Join-Path $repo '.git'))) {
    throw "This NYVERRA directory is not a Git clone. Clone the private repo first."
}
$origin = (& git -C $repo remote get-url origin | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or ($origin -ne $expected -and $origin -ne $expectedSSH)) {
    throw "Remote origin does not match the NYVERRA private GitHub repository. Got: $origin"
}
$branch = (& git -C $repo branch --show-current | Out-String).Trim()
if ($branch -ne 'main') {
    throw "Expected branch main, got: $branch"
}
$dirty = @(& git -C $repo status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) {
    throw "Local checkout has uncommitted changes. Commit or stash them before map import."
}
& git -C $repo pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw "Could not safely fast-forward main. No files copied." }

$target = Join-Path $repo 'Content/Maps/TestWorld.umap'
$ini = Join-Path $repo 'Config/DefaultEngine.ini'
if (!(Test-Path -LiteralPath $ini)) { throw "Missing Config/DefaultEngine.ini" }
if ((Test-Path -LiteralPath $target) -and
    ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)) {
    throw "Different TestWorld.umap already exists in the repository. Refusing to overwrite it."
}
# Verify all config replacements BEFORE copying anything. Avoid writing partially edited maps.
$current = [IO.File]::ReadAllText($ini)
$updated = $current
foreach ($key in @('GameDefaultMap', 'EditorStartupMap', 'ServerDefaultMap')) {
    $regex = '(?m)^' + [regex]::Escape($key) + '=[^\r\n]*'
    if ([regex]::Matches($updated, $regex).Count -ne 1) {
        throw "Expected exactly one $key setting in $ini. No files copied."
    }
    $updated = [regex]::Replace($updated, $regex, $key + '=/Game/Maps/TestWorld')
}
$dir = Split-Path -Parent $target
if (!(Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
if (!(Test-Path -LiteralPath $target)) {
    Copy-Item -LiteralPath $source -Destination $target
}
if ($updated -ne $current) {
    [IO.File]::WriteAllText($ini, $updated, [System.Text.UTF8Encoding]::new($false))
}
& git -C $repo add -- 'Content/Maps/TestWorld.umap' 'Config/DefaultEngine.ini'
if ($LASTEXITCODE -ne 0) { throw "Git stage failed" }
& git -C $repo diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    & git -C $repo commit -m 'Add locally authored TestWorld map and configure startup'
    if ($LASTEXITCODE -ne 0) { throw "Git commit failed" }
} elseif ($LASTEXITCODE -ne 0) {
    throw "Git diff failed"
}
Write-Host "[CHECK] Uploading only the authored TestWorld.umap and DefaultEngine.ini" -ForegroundColor Cyan
Write-Host "[CHECK] If the map uses custom .uasset dependencies, add those separately."
& git -C $repo push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw "GitHub push failed. Local commit remains safe." }
Write-Host "[SUCCESS] Authored TestWorld and its startup map settings are in GitHub main." -ForegroundColor Green

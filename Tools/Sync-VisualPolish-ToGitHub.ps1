[CmdletBinding()]
param([switch]$WithImportedAssets)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$expectedHttps = "https://github.com/Zeihos/NYVERRA-Echo-Frontier.git"
$expectedSsh = "git@github.com:Zeihos/NYVERRA-Echo-Frontier.git"
$src = Join-Path $repo "Content/VisualPolishSource/Terrain"
$git = Get-Command git -ErrorAction Stop

if (!(Test-Path -LiteralPath (Join-Path $repo ".git"))) {
    throw "Not a Git clone. Download the 0.55 texture ZIP into your PRIVATE Git clone, not an unrelated Unreal folder."
}
$origin = (& git -C $repo remote get-url origin | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or ($origin -ne $expectedHttps -and $origin -ne $expectedSsh)) {
    throw "Unexpected Git remote origin: $origin"
}
$branch = (& git -C $repo branch --show-current | Out-String).Trim()
if ($branch -ne "main") { throw "Switch to branch main first. Current branch: $branch" }
$expectedNames = @()
foreach ($kind in @("Grass", "Rock", "Soil")) {
    foreach ($channel in @("Albedo", "Normal", "Roughness")) {
        $expectedNames += ("T_Ny{0}_{1}.png" -f $kind, $channel)
    }
}
foreach ($name in $expectedNames) {
    $path = Join-Path $src $name
    if (!(Test-Path -LiteralPath $path)) {
        throw "Texture pack incomplete: missing $path. No Git changes made."
    }
}
$confirm = Read-Host "Have you confirmed this GitHub repository is PRIVATE? [Y/N]"
if ($confirm -notin @("Y", "y")) { throw "Cancelled; no Git changes made" }

# Protect unrelated work. Pull only if the checkout is otherwise clean apart
# from the 0.55 source textures and optional UE-generated VisualPolish assets.
$dirty = @(& git -C $repo status --porcelain --untracked-files=all)
foreach ($line in $dirty) {
    if ($line.Length -le 3) { continue }
    $relative = $line.Substring(3).Trim('"').Replace('\', '/')
    if (-not ($relative.StartsWith("Content/VisualPolishSource/Terrain/") -or
              $relative.StartsWith("Content/NYVERRA/VisualPolish/") -or
              $relative -eq "Content/Maps/TestWorld_Visual056.umap")) {
        throw "Unrelated modified file present: $relative. Commit/stash it first."
    }
}
if ($dirty.Count -eq 0) {
    & git -C $repo pull --ff-only origin main
    if ($LASTEXITCODE -ne 0) { throw "Fast-forward pull failed" }
} else {
    Write-Warning "Texture files have been added locally. Skipping pull until they are committed."
}
& git -C $repo add -- "Content/VisualPolishSource/Terrain"
if ($LASTEXITCODE -ne 0) { throw "Failed to stage texture PNG files" }
$ueAssetsPath = Join-Path $repo "Content/NYVERRA/VisualPolish"
if ($WithImportedAssets) {
    if (!(Test-Path -LiteralPath $ueAssetsPath)) {
        throw "Missing imported Unreal assets; run VisualPolish056 installer first"
    }
    & git -C $repo add -- "Content/NYVERRA/VisualPolish"
    if ($LASTEXITCODE -ne 0) { throw "Failed to stage imported Unreal .uassets" }
    $visualMap = Join-Path $repo "Content/Maps/TestWorld_Visual056.umap"
    if (Test-Path -LiteralPath $visualMap) {
        & git -C $repo add -- "Content/Maps/TestWorld_Visual056.umap"
        if ($LASTEXITCODE -ne 0) { throw "Failed to stage safely generated visual map" }
    } else {
        Write-Warning "Visual test .umap not found. Textures and assets will be uploaded without a level."
    }
}
& git -C $repo diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    & git -C $repo commit -m "NYVERRA 0.56: upload PBR source textures, UE materials and safe visual test map"
    if ($LASTEXITCODE -ne 0) { throw "Commit failed" }
} elseif ($LASTEXITCODE -ne 0) {
    throw "Git diff error"
}
& git -C $repo push origin HEAD:main
if ($LASTEXITCODE -ne 0) {
    throw "Push failed (likely non-fast-forward). Your local commit is safe. Do not force push."
}
Write-Host "[SUCCESS] Visual files pushed to PRIVATE NYVERRA main." -ForegroundColor Green
if (-not $WithImportedAssets) {
    Write-Host "[NEXT] Run Unreal Editor import and apply scripts; then rerun with -WithImportedAssets."
}

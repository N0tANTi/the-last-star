[CmdletBinding()]
param(
    [ValidateSet("preview", "render", "assemble")]
    [string]$Mode = "preview",
    [string]$Shots = "all",
    [int]$Width = 1280,
    [int]$Height = 720,
    [int]$Samples = 20,
    [string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
if (!(Test-Path -LiteralPath $Blender)) {
    throw "Blender not found at $Blender"
}
& $Blender --background --factory-startup --python-exit-code 1 --python (Join-Path $root "src\pipeline.py") -- `
    --mode $Mode --shots $Shots --width $Width --height $Height --samples $Samples
if ($LASTEXITCODE -ne 0) {
    throw "Blender pipeline failed with exit code $LASTEXITCODE"
}

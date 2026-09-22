param(
    [Parameter(Mandatory=$true)][string]$PresentationPath,
    [Parameter(Mandatory=$true)][string]$ObjectsFile,
    [int]$SlideIndex = 1
)
# Run with Windows PowerShell 5.1. Attach only; never close the user's application.
$ErrorActionPreference = 'Stop'
$target = (Resolve-Path -LiteralPath $PresentationPath).Path
$objects = @(Get-Content -LiteralPath $ObjectsFile -Raw -Encoding UTF8 | ConvertFrom-Json)
$app = [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')
$matches = @($app.Presentations | Where-Object { $_.FullName -eq $target })
if ($matches.Count -ne 1) { throw 'Open exactly the requested file in PowerPoint before applying fonts.' }
$deck = $matches[0]
$slide = $deck.Slides.Item($SlideIndex)
$selected = @()
$names = @{}
# Validate all names before mutating any shape.
foreach ($item in $objects) {
    if (!$item.id -or !$item.font -or $names.ContainsKey($item.id)) { throw 'Require unique id and explicit font for every object.' }
    $names[$item.id] = $true
    $found = @($slide.Shapes | Where-Object { $_.Name -ceq $item.id })
    if ($found.Count -ne 1 -or $found[0].HasTextFrame -ne -1) { throw "Missing or ambiguous text object: $($item.id)" }
    $selected += @{ item=$item; shape=$found[0] }
}
$report = @()
foreach ($entry in $selected) {
    $item = $entry.item
    $shape = $entry.shape
    $frame = $shape.TextFrame
    $frame.TextRange.Font.Name = $item.font
    $frame.TextRange.Font.NameFarEast = $item.font
    $frame.AutoSize = 0
    $frame.MarginLeft = 0; $frame.MarginRight = 0
    $frame.MarginTop = 0; $frame.MarginBottom = 0
    if ($null -ne $item.wrap) { $frame.WordWrap = $(if ($item.wrap) { -1 } else { 0 }) }
    $report += [pscustomobject]@{
        id=$shape.Name; text=$frame.TextRange.Text
        font=$frame.TextRange.Font.Name; font_east_asian=$frame.TextRange.Font.NameFarEast
        left=$shape.Left; top=$shape.Top; width=$shape.Width; height=$shape.Height
        bound_width=$frame.TextRange.BoundWidth; bound_height=$frame.TextRange.BoundHeight
    }
}
# Caller saves through MCP and renders the same saved checkpoint.
$report | ConvertTo-Json -Depth 5

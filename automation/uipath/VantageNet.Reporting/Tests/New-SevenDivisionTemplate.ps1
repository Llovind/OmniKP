param([Parameter(Mandatory)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $OutputPath) { throw 'Choose a new template path.' }

function Color([string]$Hex) {
    return [Convert]::ToInt32($Hex.Substring(0, 2), 16) +
        256 * [Convert]::ToInt32($Hex.Substring(2, 2), 16) +
        65536 * [Convert]::ToInt32($Hex.Substring(4, 2), 16)
}

$navy = Color '142743'
$blue = Color '1456BA'
$light = Color 'DBE7F6'
$muted = Color '46617F'
$white = Color 'FFFFFF'
$coral = Color 'BA4F43'

function Box($Slide, $Name, $Text, $X, $Y, $W, $H, $Size, $Ink, [bool]$Bold = $false, $Font = 'Aptos') {
    $shape = $Slide.Shapes.AddTextBox(1, $X, $Y, $W, $H)
    $shape.Name = $Name
    $frame = $shape.TextFrame
    $frame.MarginLeft = 0
    $frame.MarginRight = 0
    $frame.MarginTop = 0
    $frame.MarginBottom = 0
    $frame.WordWrap = -1
    $frame.AutoSize = 0
    $range = $frame.TextRange
    $range.Text = $Text
    $range.Font.Name = $Font
    $range.Font.Size = $Size
    $range.Font.Color.RGB = $Ink
    if ($Bold) { $range.Font.Bold = -1 }
    $shape.TextFrame2.AutoSize = 0
    $shape.Height = $H
}

function Line($Slide, $X1, $Y, $X2, $Ink) {
    $line = $Slide.Shapes.AddLine($X1, $Y, $X2, $Y)
    $line.Line.ForeColor.RGB = $Ink
    $line.Line.Weight = 1
}

function Slide($Index, $Title, $Subheading = '') {
    $slide = $presentation.Slides.Add($Index, 12)
    $slide.FollowMasterBackground = 0
    $slide.Background.Fill.ForeColor.RGB = $white
    Box $slide 'Title' $Title 50 45 870 57 38 $navy $true
    if ($Subheading) { Box $slide 'Subheading' $Subheading 52 108 856 42 17 $muted }
    Line $slide 52 494 908 $light
    Box $slide 'Footer' 'VANTAGENET  /  SYNTHETIC DEMONSTRATION DATA' 52 506 760 20 11 $muted $true
    Box $slide 'Page' ('{0:00}' -f $Index) 882 506 27 20 11 $muted $true
    return $slide
}

$app = New-Object -ComObject PowerPoint.Application
$presentation = $app.Presentations.Add(0)
try {
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540
    $s = $presentation.Slides.Add(1, 12)
    $s.FollowMasterBackground = 0
    $s.Background.Fill.ForeColor.RGB = $navy
    Box $s 'Brand' 'VANTAGENET  /  MANAGEMENT PERFORMANCE REPORT' 52 47 856 25 15 $light $true
    Box $s 'Period' 'Reporting date' 52 125 860 26 16 $light
    Box $s 'Headline' 'Executive finding' 49 156 850 170 66 $white $true
    Box $s 'Scope' 'Scope' 52 344 860 36 25 $light $true
    Box $s 'Summary' 'Below target' 52 396 860 34 24 $white
    Line $s 52 471 908 $muted
    Box $s 'Synthetic' 'SYNTHETIC DEMONSTRATION DATA' 52 489 420 29 13 $light $true
    Box $s 'ApprovalMode' 'Approval status' 510 489 398 29 13 $light $true

    $s = Slide 2 'Performance by division' 'Target status for confirmed readings in each submitting division.'
    $fields = @('Division', 'kpis', 'readings', 'meeting', 'below_target')
    $labels = @('Division', 'KPIs', 'Readings', 'Meeting target', 'Below target')
    $columns = @(52, 365, 486, 625, 780)
    for ($j = 0; $j -lt $fields.Count; $j++) {
        Box $s "Header$j" $labels[$j] $columns[$j] 157 150 25 16 $blue $true
    }
    for ($i = 0; $i -lt 7; $i++) {
        $y = 193 + 41 * $i
        Line $s 52 ($y - 7) 908 $light
        for ($j = 0; $j -lt $fields.Count; $j++) {
            Box $s "$($fields[$j])$i" '-' $columns[$j] $y 150 28 19 $navy ($j -eq 0)
        }
    }

    $s = Slide 3 'Target status across both locations' 'Bar lengths represent shares of the full set of confirmed readings.'
    Box $s 'MetLabel' '-' 52 175 850 27 21 $navy $true
    Box $s 'MetBar' '-' 52 206 850 37 25 $blue $false 'Consolas'
    Box $s 'MissLabel' '-' 52 264 850 27 21 $navy $true
    Box $s 'MissBar' '-' 52 295 850 37 25 $coral $false 'Consolas'
    Line $s 52 365 908 $light
    Box $s 'Location0' '-' 52 389 850 30 20 $navy
    Box $s 'Location1' '-' 52 433 850 30 20 $navy

    $s = Slide 4 'Largest relative gaps to target' 'Ranked by gap relative to target. Zero targets use a near-zero denominator.'
    Box $s 'KpiHeading' 'KPI' 52 146 410 24 16 $blue $true
    Box $s 'ScopeHeading' 'Division / location' 485 146 180 24 16 $blue $true
    Box $s 'ActualHeading' 'Actual' 683 146 112 24 16 $blue $true
    Box $s 'TargetHeading' 'Target' 812 146 112 24 16 $blue $true
    for ($i = 0; $i -lt 5; $i++) {
        $y = 181 + 60 * $i
        Line $s 52 ($y - 4) 908 $light
        Box $s "GapKpi$i" '-' 52 ($y + 6) 412 50 17 $navy $true
        Box $s "GapScope$i" '-' 485 ($y + 6) 185 50 15 $muted
        Box $s "GapActual$i" '-' 683 ($y + 6) 119 50 17 $coral $true
        Box $s "GapTarget$i" '-' 812 ($y + 6) 112 50 17 $navy
    }

    $s = Slide 5 'What the evidence supports'
    Box $s 'EvidenceScope' '-' 52 108 850 32 20 $blue $true
    Box $s 'Focus' '-' 52 149 850 52 22 $navy $true
    Box $s 'Narrative' '-' 52 217 850 117 21 $navy
    Line $s 52 353 908 $light
    Box $s 'Evidence' '-' 52 371 850 62 16 $muted
    Box $s 'Model' '-' 52 454 850 25 14 $muted

    $s = Slide 6 'Actions for division follow-up'
    Box $s 'ActionScope' '-' 52 137 850 39 22 $blue $true
    Box $s 'Action' '-' 52 192 850 169 26 $navy
    Line $s 52 375 908 $light
    Box $s 'Followup' '-' 52 397 850 75 21 $muted

    $s = Slide 7 'Every reading has a workbook source' 'The bundle retains the worksheet row, fingerprint and backend confirmation timestamp.'
    Box $s 'DivisionHeading' 'Division' 52 153 150 24 16 $blue $true
    Box $s 'WorkbookHeading' 'Workbook' 246 153 185 24 16 $blue $true
    Box $s 'IdHeading' 'Submission ID' 471 153 437 24 16 $blue $true
    for ($i = 0; $i -lt 7; $i++) {
        $y = 189 + 34 * $i
        Line $s 52 ($y - 4) 908 $light
        Box $s "SourceDivision$i" '-' 52 $y 150 27 17 $navy $true
        Box $s "Workbook$i" '-' 246 $y 185 27 17 $navy
        Box $s "Submission$i" '-' 471 $y 437 27 15 $navy $false 'Consolas'
    }
    Box $s 'Approval' '-' 52 438 850 23 16 $blue $true
    Box $s 'Trace' '-' 52 468 850 21 13 $muted

    $presentation.SaveAs($OutputPath, 24)
} finally {
    $presentation.Close()
    if ($app.Presentations.Count -eq 0) { $app.Quit() }
}

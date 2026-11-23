#Requires -Version 7.6
[CmdletBinding()]
param([string] $ProjectFolder = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'
if ([Environment]::Version.Major -lt 10) { throw 'This regression requires .NET 10.' }
$project = (Resolve-Path -LiteralPath $ProjectFolder).Path
$temp = [IO.Directory]::CreateTempSubdirectory('vantagenet-feedback-test-').FullName
$harness = Join-Path $temp 'OperatorFeedbackHarness.cs'
try {
    [IO.File]::Copy((Join-Path $PSScriptRoot 'OperatorFeedbackHarness.cs.txt'), $harness)
    $names = @('OperatorFeedbackAcceptance.cs', 'SubmitOperatorFeedback.cs', 'BackendBundleV2Admission.cs',
        'BackendBundleV2Contract.cs', 'BackendBundleV2Digest.cs', 'BackendNarrativeV2.cs', 'NarrativeState.cs', 'MappingReview.cs')
    $sources = @($names | ForEach-Object { Join-Path $project $_ }) + $harness
    Add-Type -Path $sources -CompilerOptions '/warnaserror+' -ErrorAction Stop
    [OperatorFeedbackHarness]::Run($temp, $project).GetAwaiter().GetResult()
}
finally {
    # The path comes directly from CreateTempSubdirectory and belongs to this process.
    [IO.Directory]::Delete($temp, $true)
}

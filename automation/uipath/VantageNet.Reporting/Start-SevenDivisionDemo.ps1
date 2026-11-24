param(
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_-]{1,48}$')][string]$RunId,
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_-]{1,48}$')][string]$BundleId,
    [Parameter(Mandatory)][ValidatePattern('^v[1-9][0-9]{0,5}$')][string]$Revision,
    [Parameter(Mandatory)][string]$Python,
    [int]$Port = 8189,
    [string]$WorkRoot,
    [string]$InputRoot,
    [switch]$Resume,
    [switch]$AutomatedTest
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$fixtures = Join-Path $repo 'frontend/public/demo/divisions'
$Python = (Resolve-Path -LiteralPath $Python).Path
if (!$WorkRoot) { $WorkRoot = Join-Path $repo "tmp/$RunId" }
$WorkRoot = [IO.Path]::GetFullPath($WorkRoot)
$dbName = "disposable-$RunId.db"
$dbPath = Join-Path $WorkRoot $dbName
$configPath = Join-Path $WorkRoot 'seven-division-config.json'
$origin = "http://127.0.0.1:$Port"
if (!$Resume) {
    if (Test-Path -LiteralPath $WorkRoot) { throw 'Choose an unused work root for this new run.' }
    [IO.Directory]::CreateDirectory($WorkRoot) | Out-Null
    if (!$InputRoot) {
        $InputRoot = Join-Path $WorkRoot 'Input'
        foreach ($item in (Get-Content -LiteralPath (Join-Path $fixtures 'manifest.json') -Raw | ConvertFrom-Json)) {
            $folder = [IO.Path]::GetFileNameWithoutExtension($item.filename).ToUpperInvariant()
            $divisionFolder = Join-Path $InputRoot $folder
            [IO.Directory]::CreateDirectory($divisionFolder) | Out-Null
            Copy-Item -LiteralPath (Join-Path $fixtures $item.filename) -Destination (Join-Path $divisionFolder $item.filename)
        }
    }
    $mode = if ($AutomatedTest) { 'automated-test' } else { 'supervised-local' }
    $config = [ordered]@{
        run_id = $RunId; bundle_id = $BundleId; revision = $Revision; report_date = '2026-06-30'; decision_mode = $mode
        input_root = [IO.Path]::GetFullPath($InputRoot); work_root = $WorkRoot
        division_manifest = (Join-Path $fixtures 'manifest.json'); expected_readings = (Join-Path $fixtures 'expected-readings.json')
        backend_origin = $origin; expected_instance_id = $RunId; expected_database = "sqlite:$dbName"
    }
    [IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
} else {
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if ($config.run_id -cne $RunId -or $config.bundle_id -cne $BundleId -or $config.revision -cne $Revision -or
        $config.expected_database -cne "sqlite:$dbName" -or $config.expected_instance_id -cne $RunId -or
        $config.work_root -cne $WorkRoot -or $config.backend_origin -cne $origin -or !(Test-Path -LiteralPath $dbPath -PathType Leaf)) {
        throw 'Resume requires the existing disposable database and its matching run configuration.'
    }
}

$env:DATABASE_URL = 'sqlite:///' + $dbPath.Replace('\', '/')
$env:DEMO_DATABASE_URL = 'sqlite://'
$env:VANTAGENET_DISPOSABLE = '1'
$env:VANTAGENET_DISPOSABLE_INSTANCE_ID = $RunId
Write-Host "Robot configuration $configPath"
Write-Host "Disposable backend $origin"
Push-Location (Join-Path $repo 'backend')
try { & $Python -B -m uvicorn main:app --host 127.0.0.1 --port $Port --workers 1 --no-access-log }
finally { Pop-Location }
exit $LASTEXITCODE

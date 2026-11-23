# VantageNet — Gate 3D.1–3D.4 Deliverables & Handover Package

Self-contained technical handover, operational runbook, and verified `v7` reporting deliverables for **VantageNet / OmniKPI** (Domain `1` — Telecommunications).

---

## Package Contents

| File | Purpose |
|---|---|
| `README.md` | Package overview, architecture summary, quick start, and documentation links (this file). |
| `HANDOVER.md` | Complete English technical handover: architecture, dual AI provider setup (Local Ollama & OpenRouter), UiPath Studio & CLI guide, implementation details, acceptance evidence, and known limitations. |
| `RUNBOOK.md` | Complete operational runbook in **Bahasa Indonesia**: startup, dual AI configuration, UiPath Studio GUI & CLI operation, end-to-end report generation, safe shutdown, and troubleshooting. |
| `VantageNet-gate3d-ed-fact12-v7.pptx` | Final 3-slide PowerPoint report for `case-gate3d-ed-fact12` revision `v7` (Proposal 1 human-approved narrative unchanged, generated via `qwen3.5:9b` local GPU inference). |
| `report-proof.pdf` | 3-page PDF render proof exported from `VantageNet-gate3d-ed-fact12-v7.pptx` via Microsoft PowerPoint. |
| `generation-receipt.json` | Cryptographic generation receipt binding the `v7` admission bundle, human approval decision, narrative hash, pinned template hash, and PPTX hash. |
| `SHA256SUMS.txt` | Lowercase SHA-256 checksums for all deliverable files in this folder. |

---

## Architecture Overview

```text
+-------------------------------------------------------------------+
| C:\ (Windows 11 System & Local App Installations)                 |
|  - UiPath Studio & CLI: C:\Program Files\UiPathPlatform\...       |
|  - Acceptance Launcher: %LOCALAPPDATA%\VantageNet\                |
|    * start-acceptance-backend.ps1                                 |
|    * acceptance-venv\Scripts\python.exe                           |
|  - Disposable DB: %LOCALAPPDATA%\Temp\vantagenet-acceptance-...   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| D:\myProject\OmniKP-integration\ (Repository & Artifacts)         |
|  - FastAPI Backend: backend\ (http://127.0.0.1:8187)              |
|  - UiPath Project:  automation\uipath\VantageNet.Reporting\       |
|  - Deliverables:    deliverables\Gate-3D.1-VantageNet\            |
+----------------+----------------------------------+---------------+
                 |                                  |
     Option A    |                                  | Option B
   (Local GPU)   v                                  v (Cloud API)
+-------------------------------+      +----------------------------+
| E:\AI\ (Local AI Storage)     |      | OpenRouter API             |
|  - Ollama: E:\AI\Ollama\      |      |  - https://openrouter.ai/  |
|  - Models: E:\AI\Models\      |      |    api/v1                  |
|  - Logs:   E:\AI\Logs\        |      |  - Configurable LLM_MODEL  |
|  - qwen3.5:9b on RTX 5060 Ti  |      |  - Real OPENROUTER_API_KEY |
|  - http://127.0.0.1:11434/v1  |      +----------------------------+
+-------------------------------+
```

---

## Quick Start

### Option A — Local AI (Ollama `qwen3.5:9b` on RTX 5060 Ti 16GB)
1. Start Ollama with `E:\AI\Models` and `8192` context:
   ```powershell
   $env:OLLAMA_MODELS = "E:\AI\Models"
   $env:OLLAMA_NUM_PARALLEL = "1"
   $env:OLLAMA_CONTEXT_LENGTH = "8192"
   $env:OLLAMA_FLASH_ATTENTION = "1"
   $env:OLLAMA_HOST = "127.0.0.1:11434"
   E:\AI\Ollama\ollama.exe serve
   ```
2. Start the disposable acceptance backend (`127.0.0.1:8187`):
   ```powershell
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\VantageNet\start-acceptance-backend.ps1"
   ```
3. Verify health and provider status:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8187/api/v1/health
   Invoke-RestMethod http://127.0.0.1:8187/api/v1/ai/status
   ```

### Option B — OpenRouter API (Remote Cloud Provider)
Set `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`, a configurable `LLM_MODEL`, and a user-supplied `OPENROUTER_API_KEY` (never hardcoded or logged) in `backend\.env` or process environment variables before starting `uvicorn main:app` (see `HANDOVER.md` Section 2B and `RUNBOOK.md` Bagian 2B).

---

## Quick Checksum Verification

Run inside `D:\myProject\OmniKP-integration\deliverables\Gate-3D.1-VantageNet\`:
```powershell
Get-Content SHA256SUMS.txt | ForEach-Object {
    $expected, $file = $_ -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    [PSCustomObject]@{ File = $file; Match = ($actual -eq $expected); SHA256 = $actual }
} | Format-Table -AutoSize
```

---

## Documentation Links

- **Technical Handover (English)**: [HANDOVER.md](HANDOVER.md)
- **Operational Runbook (Bahasa Indonesia)**: [RUNBOOK.md](RUNBOOK.md)
- **Checksums**: [SHA256SUMS.txt](SHA256SUMS.txt)
- **Generation Receipt**: [generation-receipt.json](generation-receipt.json)

# Runbook Operasional VantageNet (Gate 3D.1–3D.4)

Panduan operasional lengkap untuk menjalankan backend VantageNet, memilih provider AI (**Local Ollama** atau **OpenRouter API**), mengoperasikan **UiPath Studio** (GUI maupun CLI), menghasilkan laporan PPTX/PDF, melakukan *shutdown* aman, dan menangani gangguan umum.

> **Peringatan Penting — Revisi `v7` Bersifat Final & Imutabel**
> Revisi `v7` pada kasus `gate3d-ed-fact12` sudah selesai disetujui dan diterbitkan (`VantageNet-gate3d-ed-fact12-v7.pptx`). **Jangan pernah menjalankan ulang atau menimpa `v7`.** Untuk demonstrasi atau pengujian baru, selalu gunakan nomor revisi baru (misalnya `v8`) atau `bundleId` baru.

---

## 1. Ikhtisar Lokasi Penyimpanan (`C:`, `D:`, `E:`)

| Drive | Fungsi | Lokasi Aktual |
|---|---|---|
| **`C:\`** | Aplikasi Windows, UiPath Studio/CLI, Python venv acceptance, launcher, dan database SQLite disposable | - UiPath Studio: `C:\Program Files\UiPathPlatform\Studio\26.10.0-cloud.25715\UiPath.Studio.exe`<br>- UiPath CLI: `C:\Program Files\UiPathPlatform\Studio\26.10.0-cloud.25715\cli\uip.cmd`<br>- Launcher Backend: `%LOCALAPPDATA%\VantageNet\start-acceptance-backend.ps1`<br>- Python Venv: `%LOCALAPPDATA%\VantageNet\acceptance-venv\Scripts\python.exe`<br>- Database Disposable: `C:\Users\Windows 11\AppData\Local\Temp\vantagenet-acceptance-20261121-e63c\disposable_vantagenet_acceptance_20261121_e63c.db` |
| **`D:\`** | Kode sumber repositori, backend FastAPI, proyek UiPath, hasil output, dan paket deliverables | - Repositori: `D:\myProject\OmniKP-integration`<br>- Backend: `D:\myProject\OmniKP-integration\backend`<br>- Proyek UiPath: `D:\myProject\OmniKP-integration\automation\uipath\VantageNet.Reporting`<br>- Deliverables: `D:\myProject\OmniKP-integration\deliverables\Gate-3D.1-VantageNet` |
| **`E:\`** | Runtime AI lokal (Ollama), bobot model, dan log server | - Biner Ollama: `E:\AI\Ollama\ollama.exe`<br>- Penyimpanan Model: `E:\AI\Models`<br>- Log Server: `E:\AI\Logs\` |

---

## 2. Konfigurasi Dual AI Provider

Backend (`backend\agents\openrouter_config.py`) membaca variabel lingkungan dengan urutan prioritas:
1. **Environment variable proses** (misalnya yang disetel oleh `start-acceptance-backend.ps1` atau sesi PowerShell saat ini) — **prioritas tertinggi**.
2. **File `backend\.env`** (dibaca melalui `load_dotenv()` hanya jika variabel belum ada di proses).
3. **Nilai default di kode** (`https://openrouter.ai/api/v1` dan `meta-llama/llama-3.1-70b-instruct`).

### Opsi A — Local AI (Ollama `qwen3.5:9b` di GPU RTX 5060 Ti 16GB) [Terverifikasi Live]

1. **Jalankan Server Ollama**:
   ```powershell
   $env:OLLAMA_MODELS = "E:\AI\Models"
   $env:OLLAMA_NUM_PARALLEL = "1"
   $env:OLLAMA_CONTEXT_LENGTH = "8192"
   $env:OLLAMA_FLASH_ATTENTION = "1"
   $env:OLLAMA_HOST = "127.0.0.1:11434"
   E:\AI\Ollama\ollama.exe serve
   ```
2. **Pastikan Model Tersedia**:
   ```powershell
   $env:OLLAMA_MODELS = "E:\AI\Models"
   E:\AI\Ollama\ollama.exe list
   # Harus menampilkan qwen3.5:9b (ukuran ~6.6 GB)
   ```
3. **Warm-up Model ke VRAM** (mencegah timeout 25 detik saat *cold load* pertama kali):
   ```powershell
   $warmBody = @{
       model = "qwen3.5:9b"; stream = $false; think = $false; keep_alive = "30m"
       options = @{ temperature = 0; num_predict = 8; num_ctx = 8192 }
       messages = @(@{ role = "user"; content = "ping" })
   } | ConvertTo-Json -Depth 6 -Compress
   Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/chat" -Method Post -ContentType "application/json" -Body $warmBody
   ```
4. **Verifikasi Akselerasi GPU**:
   ```powershell
   E:\AI\Ollama\ollama.exe ps
   # Pastikan PROCESSOR menunjukkan 100% GPU dan CONTEXT 8192
   nvidia-smi --query-gpu=name,utilization.gpu,memory.total,memory.used,memory.free --format=csv,noheader
   ```
5. **Jalankan Backend Acceptance**:
   Launcher `%LOCALAPPDATA%\VantageNet\start-acceptance-backend.ps1` sudah dikonfigurasi untuk menunjuk ke `http://127.0.0.1:11434/v1`, model `qwen3.5:9b`, dan kunci dummy `ollama-local`.

### Opsi B — OpenRouter API (Provider Cloud)

> **Catatan Keamanan**: Jangan pernah menulis API key asli di dalam script, kode sumber, atau Git, dan jangan pernah mencetaknya ke layar/log.

1. **Siapkan API Key**: Buat API key (`sk-or-v1-...`) dari dashboard akun OpenRouter (`https://openrouter.ai/`).
2. **Set Konfigurasi di PowerShell Secara Aman**:
   ```powershell
   $sec = Read-Host -Prompt "Masukkan OpenRouter API key" -AsSecureString
   $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
   try {
       $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
   } finally {
       [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
       $sec.Dispose()
   }
   $env:OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
   $env:LLM_MODEL = "<provider/model-id>"   # contoh model OpenRouter yang dipilih
   $env:OPENROUTER_MAX_RETRIES = "0"
   ```
3. **Jalankan Backend Acceptance dengan OpenRouter**:
   ```powershell
   $env:DATABASE_URL = "sqlite:///C:/Users/Windows 11/AppData/Local/Temp/vantagenet-acceptance-20261121-e63c/disposable_vantagenet_acceptance_20261121_e63c.db"
   $env:DEMO_DATABASE_URL = "sqlite://"
   $env:VANTAGENET_DISPOSABLE = "1"
   $env:VANTAGENET_DISPOSABLE_INSTANCE_ID = "vantagenet-acceptance-20261121-e63c"
   Push-Location D:\myProject\OmniKP-integration\backend
   & "$env:LOCALAPPDATA\VantageNet\acceptance-venv\Scripts\python.exe" -B -E -s -m uvicorn main:app --host 127.0.0.1 --port 8187 --workers 1 --lifespan off --log-level warning --no-access-log
   ```
4. **Verifikasi Tanpa Membocorkan Key**:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8187/api/v1/ai/status | Select-Object configured,mode,model,provider,max_retries
   ```
5. **Kembali ke Local Ollama**: Hentikan proses `uvicorn`, hapus `$env:OPENROUTER_API_KEY` (`Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue`), pastikan Ollama berjalan, lalu jalankan `start-acceptance-backend.ps1`.

### Perbandingan Provider

| Fitur | Local Ollama | OpenRouter |
|---|---|---|
| Lokasi inferensi | GPU Lokal | Cloud |
| Autentikasi | Kunci dummy lokal (`ollama-local`) | API key asli (`OPENROUTER_API_KEY`) |
| Kebutuhan internet | Tidak perlu untuk inferensi | Wajib |
| Biaya | Perangkat keras & listrik lokal | Tarif model/API OpenRouter |
| Pilihan model | Model lokal terpasang (`qwen3.5:9b`) | Model yang tersedia di OpenRouter |
| Privasi data | Inferensi lokal penuh | Request dikirim ke provider |
| Kebutuhan GPU | Ya (RTX 5060 Ti 16GB) | Tidak |

---

## 3. Prosedur Startup Sistem

1. Pilih provider AI (Opsi A: Local Ollama atau Opsi B: OpenRouter).
2. Jika memakai Opsi A, jalankan Ollama (`E:\AI\Ollama\ollama.exe serve`), lakukan *warm-up*, dan cek `ollama ps`.
3. Jalankan backend acceptance:
   ```powershell
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\VantageNet\start-acceptance-backend.ps1"
   ```
4. Di terminal lain, verifikasi kesehatan sistem:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8187/api/v1/health
   Invoke-RestMethod http://127.0.0.1:8187/_development/instance
   Invoke-RestMethod http://127.0.0.1:8187/api/v1/ai/status
   ```
5. Buka **UiPath Studio**: jalankan `C:\Program Files\UiPathPlatform\Studio\26.10.0-cloud.25715\UiPath.Studio.exe`, pilih **Open a Local Project**, lalu buka `D:\myProject\OmniKP-integration\automation\uipath\VantageNet.Reporting\project.json`.

---

## 4. Prosedur Pembuatan Laporan End-to-End (Untuk Revisi Baru, mis. `v8`)

> **Ingat**: Gunakan revisi baru (`v8`, dst.) atau `bundleId` baru. Jangan menimpa `v7`.

### Langkah 1 — Bundle Admission (`AdmitBackendReportBundleV2.cs`)
- **Melalui Studio GUI**: Buka `AdmitBackendReportBundleV2.cs` -> **Debug File** -> **Run File**, isi argumen di bawah.
- **Melalui CLI**:
  ```powershell
  $uip = "C:\Program Files\UiPathPlatform\Studio\26.10.0-cloud.25715\cli\uip.cmd"
  $proj = "D:\myProject\OmniKP-integration\automation\uipath\VantageNet.Reporting"
  & $uip rpa run --project-dir $proj --file-path "AdmitBackendReportBundleV2.cs" --profile "vantagenet-local-noauth" --skip-build --output json `
    --input-arguments "projectFolder=$proj" `
    --input-arguments "backendOrigin=http://127.0.0.1:8187" `
    --input-arguments "domainId=1" `
    --input-arguments "expectedInstanceId=vantagenet-acceptance-20261121-e63c" `
    --input-arguments "expectedDatabase=sqlite:disposable_vantagenet_acceptance_20261121_e63c.db" `
    --input-arguments "submissionId=aff04920-b5ee-4ddd-9786-9c94a7549d35" `
    --input-arguments "factId=12" `
    --input-arguments "bundleId=gate3d-ed-fact12" `
    --input-arguments "revision=v8"
  ```
- **Hasil yang Diharapkan**: File `bundle.json`, `state.json` (`evidence_status="draft_ready"`, `eligible_for_review=true`), dan `snapshot.json` di `Output\BackendReportBundlesV2\case-gate3d-ed-fact12\v8\`.

### Langkah 2 — Persiapan & Persetujuan Manusia (`ReviewBackendNarrativeV2.cs`)
1. **Prepare**:
   ```powershell
   & $uip rpa run --project-dir $proj --file-path "ReviewBackendNarrativeV2.cs" --profile "vantagenet-local-noauth" --skip-build --output json `
     --input-arguments "projectFolder=$proj" --input-arguments "bundleId=gate3d-ed-fact12" --input-arguments "revision=v8"
   ```
2. Buka `Output\BackendNarrativeReviewV2\case-gate3d-ed-fact12\v8\narrative-review.html` di browser, periksa narasi, isi nama reviewer, alasan, pilih **Approve**, lalu simpan file keputusan JSON.
3. **Record Decision**:
   ```powershell
   & $uip rpa run --project-dir $proj --file-path "ReviewBackendNarrativeV2.cs" --profile "vantagenet-local-noauth" --skip-build --output json `
     --input-arguments "projectFolder=$proj" --input-arguments "bundleId=gate3d-ed-fact12" --input-arguments "revision=v8" --input-arguments "decisionPath=<path-file-keputusan.json>"
   ```

### Langkah 3 — Generate PPTX (`GenerateBackendNarrativePptxV2.cs`) & Export PDF Proof
1. **Generate PPTX**:
   ```powershell
   & $uip rpa run --project-dir $proj --file-path "GenerateBackendNarrativePptxV2.cs" --profile "vantagenet-local-noauth" --skip-build --output json `
     --input-arguments "projectFolder=$proj" --input-arguments "bundleId=gate3d-ed-fact12" --input-arguments "revision=v8"
   ```
   Output: `Output\BackendNarrativeReviewV2\case-gate3d-ed-fact12\v8\report\VantageNet-gate3d-ed-fact12-v8.pptx` dan `generation-receipt.json`.
2. **Export PDF Proof via PowerPoint**:
   ```powershell
   $revDir = "$proj\Output\BackendNarrativeReviewV2\case-gate3d-ed-fact12\v8"
   $pp = New-Object -ComObject PowerPoint.Application
   $pres = $pp.Presentations.Open("$revDir\report\VantageNet-gate3d-ed-fact12-v8.pptx", $true, $false, $false)
   $pres.SaveAs("$revDir\report\report-proof.pdf", 32)
   $pres.Close(); $pp.Quit()
   ```
3. **Verifikasi Receipt & Checksum**:
   ```powershell
   (Get-FileHash "$revDir\report\VantageNet-gate3d-ed-fact12-v8.pptx" -Algorithm SHA256).Hash.ToLowerInvariant()
   # Bandingkan dengan field pptx_sha256 di generation-receipt.json
   ```

---

## 5. Prosedur Shutdown Aman

1. **Identifikasi Proses & Port**:
   ```powershell
   Get-NetTCPConnection -LocalPort 8187,11434 -ErrorAction SilentlyContinue | Select-Object LocalPort,State,OwningProcess
   ```
2. **Hentikan Backend VantageNet** (hanya PID pada port `8187`, jangan sentuh database):
   ```powershell
   $bePid = (Get-NetTCPConnection -LocalPort 8187 -State Listen -ErrorAction SilentlyContinue).OwningProcess
   if ($bePid) { Stop-Process -Id $bePid -Force }
   ```
3. **Hentikan Ollama** (opsional jika ingin membebaskan VRAM GPU):
   ```powershell
   Get-Process -Name "ollama","ollama app" -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
4. **Verifikasi Integritas**: Pastikan file database disposable dan folder `Output\` tidak dihapus atau diubah secara manual.

---

## 6. Panduan Troubleshooting

| Masalah | Penyebab Umum | Solusi |
|---|---|---|
| **Ollama tidak merespons (`127.0.0.1:11434`)** | Server Ollama belum berjalan | Jalankan `E:\AI\Ollama\ollama.exe serve` dengan `OLLAMA_MODELS=E:\AI\Models`. |
| **Model `qwen3.5:9b` tidak ditemukan** | `OLLAMA_MODELS` mengarah ke `C:\` bukan `E:\AI\Models` | Set `$env:OLLAMA_MODELS = "E:\AI\Models"` sebelum menjalankan `ollama serve` dan `ollama list`. |
| **VRAM GPU tidak cukup** | Aplikasi/game lain memakai VRAM berlebih di RTX 5060 Ti | Tutup aplikasi berat GPU lain, cek `nvidia-smi`, lalu warm-up ulang `qwen3.5:9b` (~5.9 GB VRAM). |
| **Timeout saat inferensi pertama (`25s`)** | *Cold load* model dari disk memakan waktu ~55 detik | Lakukan *warm-up* (`keep_alive: "30m"`) sebelum menjalankan `AdmitBackendReportBundleV2.cs`. |
| **OpenRouter HTTP 401 / 402 / 429 / 5xx** | Key salah (401), saldo habis (402), rate limit free tier (429), atau gangguan server (5xx) | Periksa key/kredit OpenRouter, ganti `LLM_MODEL`, atau beralih ke **Opsi A (Local Ollama)**. |
| **Port `8187` gagal bind / Connection refused** | Proses backend lama masih aktif atau backend belum start | Cek `Get-NetTCPConnection -LocalPort 8187`, hentikan proses lama jika perlu, lalu jalankan launcher. |
| **UiPath build / run gagal** | Ada perubahan `.cs` yang belum di-build | Jalankan `uip.cmd rpa build --project-dir ... --profile "vantagenet-local-noauth"`. |
| **Narasi ditolak validator (`missing_synthetic_framing` / `invalid_citations`)** | Model tidak menyertakan pembukaan wajib atau sitasi `[F6]` | Periksa log backend; pastikan `reasoning_effort="none"` aktif untuk Ollama lokal dan prompt tidak dimodifikasi. |

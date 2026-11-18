# Faizh Backend & Integration Handoff — VantageNet

Dokumen ini merangkum deliverables sisi backend, AI, dan integrasi milik **Faizh** untuk kontrak bersama di [VANTAGENET.md](VANTAGENET.md) serta menjawab kebutuhan di [FAIZH_INTEGRATION_HANDOFF.md](../automation/uipath/VantageNet.Reporting/FAIZH_INTEGRATION_HANDOFF.md).

---

## 1. Environment & Database Uji Disposable

### Reset database uji bersih (tanpa menyentuh `omnikpi.db` atau `omnikpi-demo.db`)
Jalankan dari folder `backend/`:

```powershell
..\.venv\Scripts\python.exe reset_disposable_db.py
```

Skrip `backend/reset_disposable_db.py` menghapus dan membuat ulang `backend/disposable_test.db` dengan hanya `dim_domain` (`domain_id = 1`, `domain_name = "Telecommunications"`, `domain_code = "digital_infra"`), `0` submissions, dan `0` readings.

### Menjalankan backend uji di loopback (`http://127.0.0.1:8000`)
Set variabel environment proses sebelum menjalankan `uvicorn` agar `backend/database.py` mengikat engine ke database disposable:

```powershell
cd backend
$env:DATABASE_URL="sqlite:///D:/Vantagenet/backend/disposable_test.db"
$env:VANTAGENET_DISPOSABLE="1"
$env:VANTAGENET_DISPOSABLE_INSTANCE_ID="disposable-local-test"
# Set OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL via environment lokal atau backend/.env (jangan commit secret)
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Verifikasi identitas instance sebelum memulai review atau confirm:

- `GET http://127.0.0.1:8000/_development/instance`
  ```json
  {
    "disposable": true,
    "instance_id": "disposable-local-test",
    "domain_id": 1,
    "app": "VantageNet",
    "database": "sqlite:disposable_test.db"
  }
  ```

---

## 2. Kontrak Endpoint yang Ditambahkan & Diverifikasi

Semua endpoint domain memakai prefix `/api/v1/domains/1`.

### A. Detail & Rekonsiliasi Submission (`GET /submissions/{submission_id}`)
Dipakai oleh `ControlledConfirm.cs` untuk verifikasi pasca-confirm dan pemulihan saat request `/confirm` timeout (GET-only recovery):

- Saat `status == "draft"`, `readings` bernilai `[]`.
- Saat `status == "confirmed"`, mengembalikan `mapping`, `fingerprint`, serta array `readings` terurut berdasarkan `source_row`, `fact_id` yang memuat `fact_id`, `submission_id`, `division`, `source_file`, `source_row`, `date`, `kpi_id`, `kpi_name`, `kpi_archetype`, `location_id`, `location_name`, `actual_value`, `target_value`, `unit`, `higher_is_better`, `status`, dan `attainment_pct`.
- Baseline ED (`frontend/public/demo/divisions/ed.xlsx`, sheet `Report`, `header_row=4`, `header_depth=1`, `division="ED"`, `report_date="2026-06-30"`):
  - File SHA-256: `8f35c686bb3f27521637787694d061660f657ac9a2a87ba4aeaedd77d9d3a498`
  - Submission fingerprint: `9ce70be76344f7839cb405c2053cd9e2b5ce750794ff53d84c61793903bd5b1c`
  - Jumlah readings: `26` (13 KPI × 2 lokasi)
- Layout kedua MBB (`frontend/public/demo/divisions/mbb.xlsx`, wide location columns, sheet `Report`, `header_row=4`, `header_depth=1`, `division="MBB"`, `report_date="2026-06-30"`):
  - Jumlah readings: `34` (17 KPI × 2 lokasi), tanpa kolom `notes` sehingga reading shortfall awal berstatus `awaiting_feedback`.

### B. Pembacaan & Provenance Feedback Exact-Fact (`GET /feedback?fact_id={fact_id}` & `POST /feedback`)
- `GET /api/v1/domains/1/feedback?fact_id=123` mengembalikan seluruh catatan feedback milik `fact_id` tersebut beserta:
  - `feedback_id`, `reference` (`F<id>`), `fact_id`, `division`, `explanation`, `corrective_action`, `created_at`
  - `origin`:
    - `"fixture-worksheet-notes"` jika berasal dari kolom `notes`/`Keterangan` workbook saat `confirm()` (contoh: `ed.xlsx`)
    - `"operator-api"` jika dikirim melalui `POST /api/v1/domains/1/feedback`
- `POST /api/v1/domains/1/feedback` mengembalikan `feedback_id`, `reference`, `fact_id`, `division`, `origin: "operator-api"`, dan `created_at`.

### C. Eksportir Report Bundle 1-Reading (`POST /report-bundles` & `backend/export_report_bundle.py`)
Menghasilkan payload JSON konsisten dalam satu sesi baca database (`backend/services/report_bundle.py`):

- **Kontrak jujur & terpisah dari fixture sintetis:**
  - `contract`: `"vantagenet.report-bundle"`
  - `schema_version`: `2` (dipisahkan secara eksplisit dari `schema_version: 1` `source_kind: "synthetic-fixture"` milik `AdaptReportBundle.cs`)
  - `source_kind`: `"backend-read-bundle"`
  - `dataset`: `"submitted"`
- **Identitas & Integritas Producer (`producer`):**
  - `domain_id`, `disposable`, `instance_id`, `captured_at`, `submission_fingerprint`, dan `reading_sha256` (hash SHA-256 kanonik atas reading + provenance + feedback).
- **Normalisasi ID & Provenance (`scope` & `snapshot`):**
  - `fact_id`, `kpi_id`, `location_id`, `feedback_id` dinormalisasi menjadi string lossless.
  - `reading.status_code`, `reading.status`, `reading.attainment_pct`, dan `reading.chart_supported` dihitung deterministik oleh backend.
- **Pemetaan Status Evidence (`evidence_status`):**
  1. `awaiting_feedback` — belum ada feedback untuk `fact_id`; `ai_invoked: false`, `narrative.origin: "backend-deterministic-gate"`, `narrative.draft: null`.
  2. `insufficient_evidence` — model AI dipanggil (`ai_invoked: true`), namun feedback dinilai tidak cukup; `narrative.draft: null`.
  3. `provider_unavailable` — provider key hilang, provider error, atau sitasi `[F<id>]` gagal validasi; `ai_invoked: false`, `narrative.origin: "provider-error"`, `narrative.draft: null`, `narrative.error` berisi pesan error (tidak ada teks pengganti palsu).
  4. `draft_ready` — model AI menghasilkan draft dengan sitasi `[F<id>]` terverifikasi terhadap feedback milik `fact_id` yang sama; `ai_invoked: true`, `narrative.origin: "live-provider-rca"`, `narrative.references` berisi detail tiap feedback tersitasi.

Contoh request `POST /api/v1/domains/1/report-bundles`:
```json
{
  "submission_id": "<confirmed_submission_uuid>",
  "fact_id": 1,
  "bundle_id": "mbb-shortfall",
  "revision": "v1"
}
```

Atau ekspor langsung ke file via CLI dari `backend/`:
```powershell
..\.venv\Scripts\python.exe export_report_bundle.py --submission-id <uuid> --fact-id 1 --bundle-id mbb-shortfall --revision v1 --output bundle.json
```

---

## 3. Jawaban Checklist Admission (`FAIZH_INTEGRATION_HANDOFF.md` Section 6)

| Item Checklist | Status & Implementasi |
|---|---|
| 1. Disposable backend identity / base URL / domain & startup | Tersedia via `GET /_development/instance` + `backend/reset_disposable_db.py` (`http://127.0.0.1:8000`, `domain_id: 1`). |
| 2. Kesepakatan versi bundle & pemisahan jujur dari synthetic envelope | Memakai `schema_version: 2`, `source_kind: "backend-read-bundle"` (tidak melabeli data backend sebagai `synthetic-fixture`). Menunggu ekstensi admission terpisah di sisi UiPath (`AdaptReportBundle` masih v1-only). |
| 3. Export 1-reading konsisten beserta revision & provenance | Disediakan oleh `backend/services/report_bundle.py`, `POST /api/v1/domains/1/report-bundles`, dan `backend/export_report_bundle.py` dengan `submission_fingerprint` dan `reading_sha256`. |
| 4. Record feedback exact-fact & origin (`fixture` vs `operator-api`) | Disediakan oleh `DivisionFeedback.origin`, `GET /api/v1/domains/1/feedback?fact_id=...`, dan `snapshot.feedback.records`. |
| 5. RCA exact-fact & validasi sitasi | `backend/agents/feedback_rca.py` mengunci query pada `fact_id`, memvalidasi `[F<id>]` secara struktural, dan menyertakan `origin` serta `fact_id` pada `evidence`. Uji live provider di lingkungan robot tetap dijalankan saat `OPENROUTER_API_KEY` aktif. |
| 6. Kasus `awaiting_feedback`, `insufficient_evidence`, `provider_unavailable` | Diuji dan diverifikasi pada `backend/test_product_flow.py` (`test_feedback_provenance_and_consistent_report_bundle_statuses`) dengan mocked provider/missing key tanpa narasi palsu. |
| 7. Uji joint acceptance real-backend | Siap dijalankan bersama Lazuardi begitu ekstensi v2 di sisi UiPath aktif menggunakan disposable DB + live provider key lokal. |

---

## 4. Pemeriksaan yang Sudah Dijalankan

- **Backend unittest (`backend/`):**
  `..\.venv\Scripts\python.exe -m unittest test_product_flow test_demo test_ai_revision -v` → **22 tests OK** (dengan mocked AI provider untuk jalur pengujian deterministik; uji live provider eksternal memerlukan `OPENROUTER_API_KEY` aktif saat sesi integrasi).
- **Frontend (`frontend/`):**
  `npm run lint` (0 warnings, 0 errors), `npm run typecheck`, `npm run build` → **OK**.
- **Disposable DB CLI (`backend/`):**
  `..\.venv\Scripts\python.exe reset_disposable_db.py --db disposable_verify.db --instance-id verify-instance` → membuat DB bersih dengan `0` submissions dan `0` readings.

# Bukti dampak VantageNet

## Ringkasan untuk pitch

- **Mock offline, satu fixture ED sintetis.** Sebanyak 26 dari 26 readings cocok dengan fixture untuk nilai aktual, target, lokasi, dan baris sumber. Enam request backend berjumlah 2,1705 detik. Jumlah ini mencakup pemeriksaan instance dan pengambilan ledger. Waktu UiPath, PPTX, dan tiga keputusan manusia masih kosong. [Diff ledger](ledger_diff.json) · [Timing](timing.csv)
- **Regresi.** Empat kelas lulus di backend: duplikat/konflik, mapping invalid, sitasi RCA invalid, dan provider gagal. Dependensi PPTX berhasil dimuat pada retry. Tes UiPath untuk penolakan sebelum confirm dan approval basi/revisi berubah masih terblokir saat memuat CLI. Label slide 6 dan 7: **Tes tersedia, belum lulus di mesin uji.** [Peta kelas error](error_tests.md) · [Manifest retry](test_runs.json) · [Impor PPTX](raw/pptx_import.log)
- **Smoke test live terpisah, satu fixture ED sintetis.** Gemini mengembalikan HTTP 200 untuk mapping (2,467 detik, 469 token input dan 264 output) dan RCA (2,421 detik, 326 input dan 81 output). Backend mengimpor 26 readings dengan mapping programatis dari hasil preview dan mengembalikan draf Demo North dengan sitasi tervalidasi. Harness kemudian keluar dengan kode 1 karena event loop sudah ditutup saat membersihkan klien HTTP. Angka ini mencatat satu run, dengan cakupan backend dan provider. [Rekaman live, status HTTP dan token](live_provider_run.json)

## Stopwatch proksi dan baseline

Untuk tiga halaman berikut, catat detik aktif, keputusan, dan alasan. Labeli hasil **ESTIMASI (proksi)**. Stopwatch dimulai saat halaman dibuka dan berhenti saat keputusan dicatat. Ketiganya menggunakan bukti mock offline melalui halaman baca terpisah dari form UiPath.

| Gerbang | Bahan baca | Detik aktif | Keputusan |
| --- | --- | --- | --- |
| Review mapping | [Usulan mapping ED](gate_proxy/01-review-mapping.md) | | |
| Otorisasi impor | [Validasi dan ringkasan ledger](gate_proxy/02-otorisasi-impor.md) | | |
| Persetujuan narasi | [Draf dan sitasi Demo North](gate_proxy/03-persetujuan-narasi.md) | | |

Untuk baseline, konsolidasikan [ED](../frontend/public/demo/divisions/ed.xlsx) lalu [MBB](../frontend/public/demo/divisions/mbb.xlsx) ke [template Excel kosong](manual_baseline_template.xlsx). Catat waktu kerja aktif tiap divisi di [template stopwatch](manual_timing_template.csv). Untuk kedua fixture, gunakan tanggal `2026-06-30`. Jalankan penilaian dengan `--division ED` dan `--division MBB` secara terpisah. Bandingkan proksi ED hanya dengan aktivitas manual ED yang sepadan. [Manifest fixture](../frontend/public/demo/divisions/manifest.json) · [Penilai workbook](score_manual.py)

## Input skenario biaya

**ASUMSI SIMULASI** untuk batas anggaran internal.

| Parameter | Nilai ilustratif | Dasar |
| --- | --- | --- |
| Tarif analis | Rp100.000/jam | Tarif bulat untuk menguji sensitivitas kapasitas kerja |
| Volume | 4 siklus/bulan | Satu siklus per minggu dalam bulan empat minggu |
| Biaya tetap | Rp500.000/bulan | Skenario alokasi demo; ganti dengan biaya lisensi/runtime dan infrastruktur aktual saat tersedia |

Biaya LLM per siklus **belum diukur**. Smoke live mencatat usage dan latensi, dengan harga efektif atau tagihan belum tersedia. Perhitungan hemat dan titik impas menunggu baseline manual, waktu gerbang, dan biaya LLM. [Kalkulator](cost_model.py) · [Usage live](live_provider_run.json)

## Rincian run mock offline

**Run Demo North** pada branch `handoff/vantagenet-ed-mvp`, commit `c247093c6a052b04e74412c4cdf8164cfd28690b`. Run memakai `ed.xlsx` sintetis dan SQLite disposable baru. Bundle memakai reading **Demo North**, sementara diff mencakup seluruh reading ED dari kedua lokasi. Pengukuran dilakukan melalui backend Uvicorn di loopback dengan provider mock dan pemetaan programatis. [Run dan timestamp UTC](ed_run.json)

| Metrik | Nilai | Status | Path bukti | Catatan keterbatasan |
| --- | --- | --- | --- | --- |
| Wall-clock backend preview | 1.9944537 detik | TERUKUR | [timing.csv](timing.csv) · [ed_run.json](ed_run.json) | Satu request HTTP lokal dalam satu run. Termasuk parsing XLSX dan panggilan ke transport mock. |
| Wall-clock backend review | 0.0158512 detik | TERUKUR | [timing.csv](timing.csv) · [ed_run.json](ed_run.json) | Validasi pemetaan programatis pada API. |
| Wall-clock backend confirm | 0.1124347 detik | TERUKUR | [timing.csv](timing.csv) · [ed_run.json](ed_run.json) | Penulisan ke database disposable. |
| Wall-clock backend fetch bundle | 0.0278605 detik | TERUKUR | [timing.csv](timing.csv) · [ed_run.json](ed_run.json) | POST `/report-bundles` untuk Demo North dengan draf RCA mock. |
| Wall-clock UiPath preview, review, confirm, fetch bundle, adapt, generate PPTX | tidak terukur | TIDAK TERUKUR | [timing.csv](timing.csv) · [CLI](raw/uip_lookup.log) · [SDK](raw/dotnet_sdks.log) · [error tes robot](raw/test_controlled_confirm.log) | CLI tidak ditemukan dan daftar SDK kosong. Kolom waktu fase robot dikosongkan. |
| Waktu mapping di transport mock | 0.0001258 detik | TERUKUR | [ai_timing_and_tokens.csv](ai_timing_and_tokens.csv) | Hanya waktu handler transport mock. |
| Waktu RCA di transport mock | 0.0003016 detik | TERUKUR | [ai_timing_and_tokens.csv](ai_timing_and_tokens.csv) | Hanya waktu handler transport mock. |
| Waktu inferensi AI nyata, model aktual, penggunaan token aktual | tidak terukur | TIDAK TERUKUR | [probe lokal](raw/ollama_loopback_probe.log) · [ai_timing_and_tokens.csv](ai_timing_and_tokens.csv) | Probe lokal timeout. Run ini hanya memakai `synthetic-offline-mock`. Respons mock tidak mengembalikan `usage`. |
| Estimasi token payload mock mapping | input 497, output 41 | ESTIMASI | [ai_timing_and_tokens.csv](ai_timing_and_tokens.csv) · [payload](raw/ed-91c6a8e3-518b-440b-80d5-ae599a2d37bd/mock_preview_mapping_1.json) | `ceil(byte UTF-8 / 4)`, dari JSON pesan input dan teks jawaban mock. Bukan hitungan tokenizer model. |
| Estimasi token payload mock RCA | input 334, output 55 | ESTIMASI | [ai_timing_and_tokens.csv](ai_timing_and_tokens.csv) · [payload](raw/ed-91c6a8e3-518b-440b-80d5-ae599a2d37bd/mock_rca_2.json) | Rumus byte yang sama. Panjang draf model aktual dapat berbeda. |
| Waktu menunggu keputusan manusia | tidak terukur | TIDAK TERUKUR | [timing.csv](timing.csv) · [ed_run.json](ed_run.json) | Run programatis ini tidak menghasilkan file keputusan manusia dari run nyata. |
| Baseline waktu konsolidasi manual dan penghematan waktu | tidak terukur | TIDAK TERUKUR | [manual_timing_template.csv](manual_timing_template.csv) | Template untuk stopwatch. Sel mulai, selesai dan jumlah reading sengaja kosong. |
| Jumlah reading ED | 26 pada ledger, 26 pada expected | TERUKUR | [ledger_diff.json](ledger_diff.json) | Ledger API backend disposable. |
| Nilai aktual | 26 cocok, 0 tidak cocok, 0 hilang | TERUKUR | [ledger_diff.json](ledger_diff.json) | Perbandingan nilai terhadap `expected-readings.json` pada reading ED. |
| Target | 26 cocok, 0 tidak cocok, 0 hilang | TERUKUR | [ledger_diff.json](ledger_diff.json) | Perbandingan target dengan lingkup yang sama. |
| Lokasi | 26 cocok, 0 tidak cocok, 0 hilang | TERUKUR | [ledger_diff.json](ledger_diff.json) | Perbandingan nama lokasi. |
| Baris sumber | 26 cocok, 0 tidak cocok, 0 hilang | TERUKUR | [ledger_diff.json](ledger_diff.json) | Dicocokkan per KPI di antara baris expected dan ledger. Lihat kunci pairing di JSON. |
| Regresi backend | 15 lulus pada product flow, 6 lulus pada AI revision, 1 lulus pada demo | TERUKUR | [Product flow](raw/test_product_flow.log) · [AI revision](raw/test_ai_revision.log) · [Demo](raw/test_demo.log) · [Peta kelas error](error_tests.md) | Tes otomatis sintetis. Hasil suite tidak mengukur tingkat error operasional. |
| Regresi robot untuk reject, approval basi, revisi berubah dan kontrol confirm | tidak terukur | TIDAK TERUKUR | [Peta kelas error](error_tests.md) | Skrip tes tersedia dan proses percobaan dicatat. Assertion belum berjalan karena CLI tidak ditemukan. |
| Jumlah sel salah pada konsolidasi manual dan perbandingan error manual dengan otomasi | tidak terukur | TIDAK TERUKUR | [score_manual.py](score_manual.py) | Membutuhkan workbook hasil kerja manual. |
| Biaya AI atau komputasi per run nyata | tidak terukur | TIDAK TERUKUR | [usage live](live_provider_run.json) · [probe lokal](raw/ollama_loopback_probe.log) | Usage tersedia dari satu smoke live. Harga efektif, tagihan provider, dan biaya komputasi lokal belum diukur. |
| Tarif analis, siklus per bulan, biaya tetap dan biaya lisensi | lihat skenario di atas | ASUMSI SIMULASI | [cost_model.py](cost_model.py) | Tarif dan alokasi ilustratif. Nilai aktual menunggu input tim. |
| Hemat per siklus dan titik impas bulanan | tidak terukur | TIDAK TERUKUR | [cost_model.py](cost_model.py) | Belum ada input yang dapat digunakan untuk menghitung skenario biaya. |

## Yang perlu diisi manusia

- **Baseline manual** menggunakan `manual_timing_template.csv` dengan workbook ED sintetis dan hasil kerja manual pada lingkup yang sama. Isi waktu stopwatch per pekerjaan serta jumlah reading selesai. Simpan berkas hasil konsolidasi untuk penilaian.
- **Keputusan manusia pada run nyata**. Simpan file keputusan HTML/JSON yang benar-benar dibuat operator beserta timestamp awal penyerahan tugas. Selang dari penyerahan sampai keputusan mengukur waktu menunggu, termasuk jeda. Jam kerja aktif perlu bukti tersendiri sebelum digunakan dalam model penghematan tenaga kerja.
- **Tarif analis per jam**, **frekuensi laporan per bulan**, dan **biaya lisensi atau biaya tetap per bulan** dalam satu mata uang. Masukkan biaya AI per siklus bila ada bukti harga dan usage. Rumus hosted `(token_input × harga_input_per_juta + token_output × harga_output_per_juta) / 1_000_000` hanya berlaku setelah parameter harga diberikan dan penggunaan aktual tercatat untuk model yang sama.

## Reproduksi dan penggunaan

- `python impact_evidence/run_ed.py` menjalankan kontrak backend di port loopback baru. Perintah, route, sumber, timestamp dan path respons berada di [ed_run.json](ed_run.json). Bagian `backend.*` pada CSV adalah durasi request dari `perf_counter_ns`, sedangkan kolom `mulai` dan `selesai` memakai jam UTC. File mock menyimpan payload sintetis tanpa header autentikasi. Jalankan ulang hanya jika ingin membuat bukti pengukuran baru.
- `python impact_evidence/run_checks.py` menjalankan suite regresi dan probe runtime. Kendala awal proxy SOCKS tersimpan di [initial_backend_execution.log](raw/initial_backend_execution.log) dan log regresi awal. Retry menghapus variabel proxy dalam proses pengukuran offline. [Manifest tes dan perintah](test_runs.json)
- `python impact_evidence/run_ed_live.py` menjalankan alur backend pada fixture ED sintetis dengan konfigurasi provider lokal dan menyimpan bukti di `output/impact-ed-live/`. Opsi ini membuat request provider nyata. Smoke test yang tercatat menggunakan mapping programatis dan tidak menjalankan UiPath.
- `python impact_evidence/score_manual.py HASIL.xlsx --division ED --sheet "Expected readings"` membandingkan ED dengan [workbook expected](../frontend/public/demo/divisions/expected-consolidated.xlsx). Hilangkan filter untuk cakupan seluruh divisi. `--sheet` opsional jika sheet dapat diidentifikasi. Baris pertama perlu unit pengirim, KPI, tanggal laporan, lokasi, nilai aktual, dan target. `Source file` dan `Source row` membantu memasangkan reading. Urutan pairing per unit, KPI dan tanggal memakai provenance yang unik, lalu lokasi unik, lalu pasangan nilai dan target yang unik. Pasangan tersisa dapat dipasangkan jika masing-masing sisi tersisa satu. Pasangan ambigu dilaporkan tanpa skor total. Hanya sel lokasi, nilai aktual dan target yang dihitung. Satu reading hilang berarti tiga sel yang dinilai hilang. Baris tambahan dilaporkan terpisah. Formula dibaca dari nilai cache Excel, jadi simpan hasil perhitungan di Excel terlebih dahulu.
- `python impact_evidence/cost_model.py --help` menampilkan enam parameter wajib. Opsi `--sensitivitas PARAMETER MIN MAX LANGKAH` bisa diulang. Setiap rentang mengubah satu parameter dan memakai input awal untuk parameter lain. Titik impas dihitung jika hemat per siklus positif, dan pecahan berulang ditampilkan sebagai rasio eksak.
- Kedua skrip diperiksa dengan input verifikasi terpisah. Hash Git untuk workbook ED, expected readings, dan expected consolidated cocok dengan commit aktif. [Verifikasi skrip](raw/utility_verification.log) · [Integritas sumber](raw/source_integrity.log)

### Pesan blocker persis

- `where.exe uip` · `INFO: Could not find files for the given pattern(s).`
- `dotnet --list-sdks` · stdout dan stderr kosong, exit code 0.
- Harness UiPath · `RuntimeError: Set UIPATH_CLI to your existing uip executable/launcher or add it to PATH. No installer is run.`
- Probe Ollama lokal · `httpx.ConnectTimeout: timed out`

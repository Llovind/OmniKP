# Role Faizh — Backend, AI & Integration Engineer

**Proyek:** VantageNet, sebelumnya omniKPI

**Periode rencana:** 16–25 November 2026

**Deadline:** 25 November 2026, 23.59 WIB

**Partner integrasi:** Lazuardi — UiPath & Automation Developer

Baca [konteks dan kontrak bersama](VANTAGENET.md) dan
[role Lazuardi](ROLE_LAZUARDI.md). Ini rencana kerja; adapter/workflow tambahan tidak
boleh dianggap sudah tersedia hanya karena disebut di dokumen.

## 1. Hasil yang menjadi tanggung jawab Faizh

Menyediakan fondasi backend/AI yang dapat dipakai robot secara konsisten: file
ditafsirkan, hasil koreksi divalidasi, data dikonfirmasi beserta sumbernya, feedback
diikat ke reading yang tepat, dan laporan menerima data serta narasi yang disetujui.

Prioritasnya integrasi yang berjalan. VantageNet memakai fondasi omniKPI; tidak
perlu menulis ulang aplikasi, mengganti stack/database, atau rename seluruh kode.

## 2. Peta kode yang perlu dibaca

| File | Peran |
|---|---|
| `backend/main.py` | Entry FastAPI, startup, router, CORS dan static frontend |
| `backend/database.py` | Models, engine dan relasi data |
| `backend/routers/submissions.py` | Preview, review, confirm, ledger dan feedback |
| `backend/services/intake.py` | Parser, live AI mapping, normalisasi, konflik dan transaksi import |
| `backend/services/performance.py` | Target status dan statistik histori |
| `backend/routers/kpi.py`, `anomaly.py` | Data dashboard/history serta reading gagal target |
| `backend/agents/feedback_rca.py`, `backend/routers/rca.py` | Draft dari feedback exact reading dan pemeriksaan sitasi |
| `backend/routers/ai.py` | Status AI dan evidence benchmark |
| `frontend/src/api/client.js` | Kontrak request frontend normal/demo |
| `frontend/src/App.jsx` | Refresh data, pemilihan reading, feedback dan RCA |

Nama file pada tabel relatif terhadap root repo. Detail run/test ada di
[handoff.md](../handoff.md#10-run-locally).

## 3. Pekerjaan pertama: siapkan kontrak yang dapat dipakai Lazuardi

Pada **16 November**, berikan:

1. Base URL uji yang bisa dijangkau runtime robot dan instruksi startup.
2. Database sintetis terpisah/disposable serta prosedur reset khusus pengujian.
3. Satu request preview multipart yang berhasil beserta contoh respons tanpa secret.
4. Contoh request review/confirm dan cara menerjemahkan `column_mapping` dari preview.
5. Daftar error yang harus ditangani robot, termasuk can_confirm=false dalam HTTP 200.
6. Expected output fixture ED: 13 KPI / 26 readings / dua lokasi pada 2026-06-30.

Jangan menunggu dokumentasi API sempurna untuk melakukan uji HTTP bersama. Pada akhir
17 November, satu input harus berhasil dikoreksi manusia dan dikonfirmasi oleh robot.

## 4. API dan aturan import yang Faizh jaga

Gunakan [kontrak utama](VANTAGENET.md#7-kontrak-integrasi-yang-sudah-ada) sebagai
rujukan bersama. API yang sudah ada dipakai ulang; endpoint baru diberi status
proposed sampai benar-benar diimplementasikan dan diuji.

- Preview membaca XLSX/CSV dan memanggil AI live. Local aliases hanya konteks.
- Saved mapping atau `use_ai=false` tidak boleh menjadi jalan melewati AI.
- Respons menyertakan alasan, trace model/batch/sample dan hasil validasi yang jelas.
- Review memproses mapping hasil koreksi, bukan memulihkan mapping awal secara diam-diam.
- Confirm melakukan validasi ulang. Masalah satu reading tidak boleh membuat subset
  valid terlanjur diimpor tanpa penjelasan.
- Faktanya satu submission dapat tersimpan sebagai draft sebelum confirm. Pernyataan
  yang benar adalah readings belum masuk `fact_kpi`, bukan belum ada write sama sekali.
- Konflik/duplikasi ditolak; jangan menghapus pengecekan agar retry terlihat berhasil.
- Field asal seperti division, filename, worksheet, source_row dan tanggal dipertahankan.

Belum ada endpoint detail draft/reject khusus untuk integrasi. Jika workflow butuh
resume atau rekonsiliasi hasil confirm, sepakati adapter/status contract terkecil
bersama Lazuardi. Jangan menyuruh robot memeriksa atau mengubah SQLite langsung.

## 5. AI, feedback dan RCA

- Key/provider/model dikonfigurasi melalui environment lokal; jangan masukkan nilai
  rahasia ke contoh request, log, source atau video.
- `/ai/status` membuktikan konfigurasi, bukan provider success; uji satu panggilan
  menggunakan data sintetis untuk membuktikan jalur live.
- Mapping memerlukan makna semua kolom; keluaran tidak lengkap harus menjadi error.
- RCA memakai `fact_id` yang tepat, bukan reading terbaru yang kebetulan satu KPI.
- Tanpa feedback, API mengembalikan `awaiting_feedback` tanpa memanggil model.
- Model dapat mengembalikan `insufficient_evidence` setelah dipanggil; robot harus
  membedakan kondisi ini dari provider failure.
- Provider hilang/gagal atau sitasi tidak valid harus terlihat sebagai error; jangan
  mengaktifkan kembali fallback non-AI atau replay tanpa label.
- Simpan referensi feedback yang mendasari draft. Cek sitasi struktural bukan bukti
  bahwa root cause secara faktual benar.

ED membawa feedback sintetis dari fixture. Siapkan kasus MBB/reading tanpa feedback
untuk menguji pengumpulan feedback baru. Hasil sebelum dan sesudah feedback harus
mengacu ke fact_id yang sama.

## 6. Data untuk laporan dan approval

Faizh menyediakan data laporan; Lazuardi memiliki workflow pengisian PowerPoint.
Sepakati dengan PIC produk/QA template dan field minimum yang dibutuhkan.

Kebutuhan bundle/snapshot **yang direncanakan**:

- run_id, submission yang termasuk, tanggal dan cakupan unit;
- ringkasan status untuk reading dalam cakupan tersebut;
- actual, target, unit, lokasi, sumber file/baris dan division;
- fact_id yang dibahas, feedback sumber dan referensi sitasinya;
- narasi serta versi yang disetujui reviewer;
- data chart atau gambar chart yang dihasilkan dari snapshot yang sama.

Pilih mekanisme terkecil yang cukup: komposisi endpoint yang ada, bundle JSON, atau
adapter export baru jika diperlukan. **Belum ada API export/PPTX/snapshot yang dijanjikan
oleh kode saat ini.** Setelah disepakati, tulis kontrak aktualnya di VANTAGENET.md.

Review manusia harus tercatat bersama versi konten yang disetujui. Jika narasi atau
cakupan data berubah setelah approval, hasil perlu ditinjau ulang. Jangan menjadikan
flag approval yang dapat dikirim sembarang client sebagai klaim security produksi.
Autentikasi/role enforcement backend belum tersedia pada fondasi ini.

## 7. UI dan perilaku dashboard

Perubahan UI diprioritaskan untuk kebutuhan demo/integrasi: nama VantageNet pada
bagian yang terlihat, pemilihan data yang benar, refresh hasil robot, dan error yang jelas.

- Pertahankan API contracts, source attribution, filter tanggal/unit, dan light/dark mode.
- Dashboard saat ini tidak mendapat push update dari robot. Pilih refresh eksplisit
  atau polling terukur jika dibutuhkan; jangan menulis klaim real-time tanpa implementasi.
- Jangan membuat redesign frontend besar sebelum jalur robot stabil.
- `/app?demo=1` dapat mempersiapkan dataset seeded. Gunakan `/app` pada backend uji
  yang bersih untuk menunjukkan readings hasil import robot.
- Jangan mencampurkan synthetic seed history dengan hasil submission yang sedang diuji.

## 8. Environment, data uji dan pemulihan

- Sediakan database uji terpisah. `seed_data.py` adalah reset legacy yang destruktif,
  bukan perintah startup rutin atau reset aman database kerja.
- Untuk custom normal `DATABASE_URL`, set di process environment sebelum startup;
  `database.py` saat ini dapat terimpor sebelum `.env` dibaca di `main.py`.
- Folder sumber privat `KPI_data/` tidak masuk ZIP demo dan tidak dikirim ke provider.
- Bounded sample ke provider tetap merupakan pengiriman data; itu bukan masking.
- Simpan kaitan run, submission, task, approval dan output tanpa secret.
- Siapkan prosedur rekonsiliasi ketika confirm timeout: bedakan gagal, sudah berhasil,
  dan hasil belum diketahui. Jangan menambah retry write otomatis tanpa kontrol.
- Workflow lock demo yang lama bersifat process-local dan bukan isolasi per pengguna.

## 9. Pengujian dan bukti yang harus diserahkan

Jalankan pemeriksaan yang sesuai setelah perubahan pada lingkungan uji sintetis:

```powershell
# Dari backend/, memakai virtual environment proyek
..\.venv\Scripts\python.exe -m unittest test_product_flow test_demo test_ai_revision -v

# Dari frontend/ jika ada perubahan frontend
npm run lint
npm run typecheck
npm run build
```

Test otomatis memakai mocked provider bukan bukti live AI. Catat uji integrasi
nyata bersama Lazuardi secara terpisah, dengan hasil yang benar-benar terjadi.

| Skenario minimum | Expected result |
|---|---|
| ED bersih dengan mapping yang benar | 26 readings, provenance dan target status cocok reference |
| Mapping dikoreksi setelah preview | Payload koreksi tervalidasi dan dipakai saat confirm |
| Mapping/data invalid | can_confirm=false atau error yang jelas; tidak ada import parsial |
| File/reading diimpor ulang | Konflik terlihat; total readings tidak bertambah |
| Reviewer menolak | Robot berhenti sebelum confirm; draft boleh tetap ada |
| Reading tanpa feedback | Bukti tidak cukup tanpa panggilan model |
| Feedback ditambahkan | RCA menggunakan fact_id dan feedback yang benar |
| Provider/sitasi gagal | Error terlihat; tidak ada penjelasan pengganti palsu |
| Laporan dibuat setelah approval | Angka, tanggal, sumber dan narasi cocok snapshot yang disetujui |

Bandingkan hasil dengan `frontend/public/demo/divisions/expected-readings.json` dan
reference workbook. Fixture/reference adalah data sintetis, bukan hasil jaringan nyata.

## 10. Milestone Faizh

| Tanggal | Deliverable |
|---|---|
| 16 Nov | Backend/database uji, contoh request/response dan kontrak field untuk Lazuardi |
| 17 Nov | Dampingi jalur satu file → koreksi manusia → review → confirm |
| 18–19 Nov | Stabilkan error/duplikasi/layout kedua dan rekonsiliasi retry |
| 20–21 Nov | Pastikan feedback/RCA exact reading dan data approval dapat dipakai robot |
| 22 Nov | Data/bundle laporan stabil, dukungan refresh dan label VantageNet minimum; feature freeze |
| 23 Nov | Regression test serta uji end-to-end berulang dari kondisi bersih |
| 24 Nov | Instruksi backend, dependency/config contoh tanpa secret dan dukungan paket/video |
| 25 Nov | Buffer perbaikan serta pendampingan submission |

## 11. Definition of done

- [ ] Lazuardi dapat memakai API dengan kontrak yang didokumentasikan.
- [ ] Backend memblokir data invalid; dalam alur MVP, robot mengirim versi mapping yang disetujui manusia.
- [ ] Hasil import cocok dengan reference untuk file yang benar-benar diproses robot.
- [ ] Provider failure, no-feedback dan insufficient-evidence dapat dibedakan.
- [ ] Feedback/RCA tidak mengambil bukti dari reading atau periode lain.
- [ ] Data dan narasi dalam PPTX dapat ditelusuri ke run, reading, sumber dan approval.
- [ ] Pemeriksaan otomatis yang relevan dijalankan dan hasilnya dicatat apa adanya.
- [ ] Cara setup/reset uji dapat dijalankan anggota lain tanpa memakai database kerja.
- [ ] Tidak ada perubahan API diam-diam, credential bocor, atau klaim fitur yang belum ada.

Yang ditunda: migrasi stack/database besar, forecasting, model ML baru, autonomous
remediation, integrasi NMS vendor, autentikasi enterprise lengkap dan redesign besar.
Kebutuhan security untuk deployment harus dicatat; jangan mengklaim fondasi demo
sebagai sistem produksi hanya karena integrasi robot sudah berjalan.

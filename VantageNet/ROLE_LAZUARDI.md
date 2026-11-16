# Role Lazuardi — UiPath & Automation Developer

**Proyek:** VantageNet, sebelumnya omniKPI

**Periode rencana:** 16–25 November 2026

**Deadline:** 25 November 2026, 23.59 WIB

**Partner integrasi:** Faizh — Backend / AI / Integration Engineer

Baca [konteks dan kontrak bersama](VANTAGENET.md) terlebih dahulu, lalu
[role Faizh](ROLE_FAIZH.md). Dokumen ini menetapkan pekerjaan yang perlu dibuat;
bukan bukti bahwa integrasinya sudah selesai.

## 1. Hasil yang menjadi tanggung jawab Lazuardi

Menghasilkan **project UiPath yang benar-benar dapat dijalankan**, membawa laporan
dari folder input sampai laporan PPTX, dengan keputusan manusia di tengah proses.
UiPath harus mengatur urutan, penugasan, kondisi lanjut/berhenti dan pemulihan error.

## 2. Yang Lazuardi pegang

| Area | Tanggung jawab |
|---|---|
| Runtime UiPath | Memilih Studio/runtime yang tersedia, menguji akses API, dan memverifikasi Action Center beserta permission/package |
| Pengambilan file | Membaca input dari satu folder dan memasangkan file dengan unit/tanggal/header yang benar |
| Integrasi HTTP | Mengirim multipart preview, mengolah JSON respons, dan memanggil review/confirm/feedback/RCA |
| Human task | Membuat form review mapping dan review narasi; menerima koreksi, penolakan dan persetujuan |
| Kelanjutan workflow | Menunggu keputusan tanpa busy-loop; lanjut hanya jika syarat terpenuhi |
| Notifikasi | Mengirim melalui satu kanal uji, menentukan penerima dari konfigurasi, dan mencegah pesan berulang |
| Output Office | Mengisi satu template PPTX dengan data dan teks yang disetujui, lalu menyimpan hasil |
| Paket robot | Source project, konfigurasi contoh tanpa secret, README, input/output contoh, serta bukti run |

Faizh tetap memiliki parsing, kalkulasi KPI, validasi, model AI dan data sumber.
Jangan menduplikasi engine tersebut dalam aktivitas Excel UiPath.

## 3. Pekerjaan pertama: buktikan satu jalur vertikal

Target akhir **17 November**:

1. Robot membaca fixture ED dari folder input uji.
2. Robot memanggil `/submissions/preview` dengan metadata yang tepat.
3. Form menampilkan kolom asli, contoh nilai, usulan target dan alasan AI.
4. Reviewer mengoreksi mapping atau menolaknya.
5. Jika diteruskan, robot mengirim mapping yang sudah diperiksa ke `/review`.
6. Jika `can_confirm=true` dan keputusan manusia setuju, robot memanggil `/confirm`.
7. Ledger/dashboard backend uji memperlihatkan 26 readings ED beserta sumbernya.

Jangan menunggu semua konektor jadi untuk mencoba jalur ini bersama Faizh.

## 4. Kontrak dengan Faizh

Gunakan prefix dan payload pada [VANTAGENET.md bagian 7](VANTAGENET.md#7-kontrak-integrasi-yang-sudah-ada).
Sebelum coding form terlalu jauh, sepakati:

- Base URL yang bisa diakses runtime robot; localhost bergantung pada mesin eksekusi.
- Backend dan database sintetis untuk pengujian; jangan gunakan database kerja pemilik.
- Contoh respons preview asli dari file uji dan field yang harus ditampilkan.
- Cara mengubah `column_mapping[col].target` menjadi `mapping[col]` berupa string.
- Cara menunjukkan `issues`, `conflicts`, `can_confirm`, dan alasan kegagalan.
- Cara mendapatkan fact_id yang benar setelah import serta data untuk laporan.
- Cara menyimpan task ID, keputusan reviewer, approved mapping/narasi dan path output.

**Review/confirm harus memakai mapping hasil koreksi**, bukan mapping awal AI atau
dictionary hardcoded. Jika mapping berubah lagi setelah review API, validasi ulang.

## 5. Desain human task

### Task A — mapping laporan

Tampilkan nama file, unit, tanggal, kolom asal, contoh nilai, usulan field, alasan AI,
serta pilihan field yang valid. Sediakan aksi koreksi/setuju/tolak yang benar-benar
memengaruhi proses.

- Penolakan menghentikan import; simpan keputusan pada jejak workflow.
- Masalah validasi dikembalikan untuk diperbaiki, bukan disembunyikan.
- Endpoint reject khusus belum tersedia; jangan mengasumsikan backend menyimpan
  status penolakan Action Center tanpa adapter yang disepakati.
- Gunakan mekanisme wait/resume yang sesuai runtime. Buktikan workflow melanjutkan
  submission yang sama setelah task selesai.

### Task B — review laporan

Tampilkan KPI, lokasi, tanggal, actual/target, feedback sumber dan draft RCA beserta
referensinya. Reviewer dapat menyetujui atau meminta perbaikan.

Jika teks diubah reviewer, versi yang dipakai PPTX adalah teks yang ia setujui.
Catat sebagai narasi yang direview manusia; jangan mengklaim seluruh edit manusia
telah diverifikasi oleh pemeriksa sitasi AI.

## 6. Notifikasi dan feedback

- Gunakan daftar penerima uji yang disepakati tim, dipetakan dari division. Belum
  ada direktori pemilik KPI terverifikasi dalam backend.
- Mulai dengan satu kanal email. Isi minimal: nama KPI, unit, lokasi, tanggal,
  actual/target, serta cara memberikan feedback untuk fact_id yang tepat.
- Reading merah berarti **gagal target**, bukan otomatis insiden darurat/Z-score.
- Gunakan penanda kirim per run/reading/penerima agar retry tidak mengirim berulang.
- Feedback baru dikirim ke `/feedback`, lalu `/rca` dipanggil untuk reading yang sama.
- Jika feedback sudah tersedia, catat bahwa langkah permintaan feedback dilewati.

ED sudah memiliki feedback sintetis pada fixture. Pakai MBB/reading tanpa feedback
untuk menunjukkan permintaan feedback yang benar-benar baru, setelah dikonfirmasi
oleh Faizh melalui API.

## 7. Menghasilkan PPTX

Lazuardi memiliki workflow pengisian template. Faizh menyiapkan data yang diperlukan;
PIC produk/QA menyediakan template dan expected output.

Isi minimal: periode/cakupan unit, ringkasan readings, visual KPI, reading yang
dibahas, sumber/feedback yang dirujuk, dan narasi yang disetujui.

- Gunakan satu template dengan placeholder/nama shape stabil yang disepakati.
- Ganti placeholder hanya dengan data run yang disetujui; jangan mengambil latest
  dashboard tanpa filter sehingga laporan berubah di tengah proses.
- Tentukan apakah chart native atau gambar chart yang benar-benar dihasilkan dari
  data run. Jangan memakai screenshot dashboard lama sebagai bukti run baru.
- Uji kebutuhan PowerPoint/runtime untuk aktivitas yang dipilih. Tidak semua
  aktivitas PowerPoint bekerja tanpa membuka aplikasi.
- Output pertama cukup ke folder hasil. Integrasi cloud storage menyusul jika inti stabil.
- Nama output mengandung run_id/periode; retry tidak boleh membagikan laporan ganda.

## 8. Error handling minimum

| Kondisi | Perilaku robot |
|---|---|
| API tidak dapat diakses / provider gagal | Tampilkan kegagalan yang dapat ditindaklanjuti; jangan memakai output AI palsu |
| HTTP 200 pada review tetapi can_confirm=false | Tampilkan issues/conflicts dan kembali ke koreksi |
| Reviewer menolak | Berhenti sebelum confirm dan simpan keputusan |
| HTTP 409 pada confirm | Perlakukan sebagai konflik; minta rekonsiliasi, bukan loop retry |
| Timeout saat confirm | Hasil write mungkin belum diketahui; cek dengan mekanisme yang disepakati Faizh sebelum mengulang |
| Bukti tidak cukup untuk RCA | Minta feedback/tinjauan, jangan memaksakan penjelasan |
| Penyimpanan/PPTX gagal | Pertahankan data approval dan run; jangan mengimpor ulang file hanya untuk membuat ulang output |

Jangan menulis secret ke activity log, screenshot, argumen publik, atau konfigurasi
yang masuk ZIP. Gunakan penyimpanan credential yang tersedia di lingkungan tim.

## 9. Milestone Lazuardi

| Tanggal | Deliverable |
|---|---|
| 16 Nov | Lingkungan UiPath, akses tenant/runtime, folder input dan HTTP preview terbukti |
| 17 Nov | Task mapping → koreksi → review API → confirm satu file selesai |
| 18–19 Nov | File kedua, reject/invalid/duplicate/provider failure tertangani |
| 20–21 Nov | Notifikasi, feedback dan task review narasi tersambung |
| 22 Nov | Template PPTX menghasilkan output final; feature freeze |
| 23 Nov | Uji proses dari kondisi awal dan pemulihan error bersama tim |
| 24 Nov | ZIP robot + README, input/output contoh dan dukungan rekaman video selesai |
| 25 Nov | Buffer perbaikan dan submission |

## 10. Definition of done

- [ ] Source project robot lengkap tersedia, bukan hanya screenshot/flowchart.
- [ ] Orang lain dapat membuka project, mengisi konfigurasi dan menjalankannya.
- [ ] Aksi manusia mengubah jalannya workflow; tak ada auto-confirm sebelum persetujuan.
- [ ] Payload yang dikirim sama dengan versi mapping yang disetujui.
- [ ] Satu alur input → dataset → RCA/review → PPTX selesai tanpa edit database manual.
- [ ] Retry tidak menambah reading, pesan, atau distribusi laporan secara diam-diam.
- [ ] Output dan task dapat ditelusuri ke run serta submission asalnya.
- [ ] Secrets tidak masuk source ZIP; dependensi, versi package, runtime dan koneksi ditulis dalam README.

Folder project robot yang **diusulkan**, belum dibuat oleh dokumentasi ini:
`automation/uipath/VantageNet.Reporting/`. Studio Desktop dikemas sebagai project
lengkap; untuk Studio Web, sertakan export project sesuai ketentuan kompetisi.

## 11. Yang tidak dikerjakan dulu

Login NMS vendor, WhatsApp/Slack bersamaan, perhitungan KPI versi robot, model AI baru,
perubahan database langsung dari robot, dan cloud storage multi-provider.
Jika terblokir oleh tenant/package, laporkan ke tim pada hari yang sama dengan
pesan error dan bukti uji tanpa credential; jangan menunggu sampai hari integrasi.

# Pemeriksaan dan perbedaan visual

Deck dirender melalui Microsoft PowerPoint COM menjadi PDF, lalu Poppler menjadi PNG seluruh slide. Pemeriksaan dilakukan dalam beberapa putaran. Seluruh slide diperiksa secara visual; pemeriksaan TextFrame2 pada versi akhir menemukan 0 teks melebihi tinggi kotak dengan toleransi 3 pt. Validator paket dan geometri melaporkan 0 finding dan 0 warning.

## Perbedaan yang disengaja dari Baiess

Palet navy, royal blue, dan sky, header berpanel, section navigation, serta footer navy dipertahankan. Navigasi lebih tipis; kartu dipakai untuk pengelompokan isi dan node diagram, tidak menjadi pola semua halaman. Header memakai panel navy dengan node-line, bukan foto stok yang tidak berhubungan. Font Calibri adalah fallback yang tersedia; tidak mengklaim font Poppins terpasang. Cover memakai foto dari deck pengguna. Chart, tabel, arsitektur dan ERD tetap native; screenshot produk dan foto tetap berupa gambar yang dapat diganti.

## Pemeriksaan per slide

| Slide | Keputusan dan hasil review |
| --- | --- |
| 1 | Pembuka berupa pertanyaan analis; foto telco dan identitas tim asli dipertahankan. |
| 2 | Data TM Forum diberi populasi responden dan batas interpretasi; implikasi Ericsson terpisah. |
| 3 | Rani diberi label persona ilustratif; angka tujuh laporan disebut sebagai demo. |
| 4 | Journey empat fase dengan native timeline; provenance menjadi penghubung ke AI. |
| 5 | Header ED literal diverifikasi terhadap worksheet; mapping dan tabel editable. |
| 6 | Arsitektur native menunjukkan workspace, API, confirm, database, serta dua jalur model. |
| 7 | Reading → feedback → draft menjadi satu adegan; keputusan kembali ke Rani. |
| 8 | Screenshot aplikasi aktual dan native donut; angka status tidak disebut akurasi AI. |
| 9 | Kelayakan memisahkan alur yang berjalan dari persyaratan pilot. |
| 10 | Target 9.1 ditampilkan sebagai jalur kontribusi, bukan hasil SDG terukur. |
| 11 | Perbandingan evaluasi dan rumus metrik; belum ada angka hasil atau ROI. |
| 12 | Menutup cerita Rani; tautan melompati appendix menuju penutup. |
| 13 | Proposal historis dibandingkan dengan cakupan implementasi sekarang. |
| 14 | Tabel dan stacked bar native langsung dari fixture per unit. |
| 15 | ERD native menggambarkan foreign key inti dan hubungan sumber/feedback. |
| 16 | Perilaku evidence gate, error provider, sitasi, serta confirm dibedakan dari kontrol produksi. |
| 17 | Bagian wajib dipetakan ke slide; rubrik final dibedakan dari seleksi proposal. |
| 18 | Penutup dengan link repository dan navigasi kembali ke appendix. |

## Revisi 6 November 2026 (AI evidence)

Perubahan teks pada slide 5, 7, 11, dan 16, ditambah notes dan narasi pembicara.

- **Slide 5:** keluaran AI sekarang menyebut “arti kolom + alasan”; sumber menyebut model aktif `google/gemini-2.5-flash-lite` dan `GET /api/v1/ai/status`. Notes mengoreksi klaim lama bahwa seluruh laporan selalu melalui model; AI bersifat opt-in dan memiliki fallback tercatat berlabel.
- **Slide 7:** sumber menambahkan penanda `ai_invoked`. Narasi mengoreksi perilaku kegagalan provider: ringkasan feedback beratribusi, bukan error tanpa pengganti.
- **Slide 11:** subtitle memuat hasil sintetis terukur (5 layout × 3 repeat; tak dikenal 0/7→7/7, reorder 0/7→6/7). Notes dan narasi memisahkan hasil sintetis dari metrik laporan nyata yang belum diukur.
- **Slide 16:** perilaku provider gagal diperjelas (usulan tercatat berlabel pada intake; ringkasan feedback pada RCA).

Pemeriksaan render: PDF dibuat ulang lewat PowerPoint COM, PNG 18 slide dibuat ulang lewat Poppler. Slide 5, 11, dan 16 diperiksa visual pada 110 dpi; tidak ada teks terpotong atau tumpang tindih pada kotak yang diubah. Slide lain hanya berubah pada notes.

File cadangan sebelum revisi: `.deploy/omniKPI_ITASE_Evidence_Story.original.pptx` (tidak termasuk paket).

## Batas penggunaan

- Tidak ditemukan defect clipping/overlap pada render akhir yang diperiksa. Hasil visual bisa berubah jika font atau aplikasi pembuka berbeda; gunakan PDF sebagai acuan visual.
- Alokasi 10 menit pada notes adalah rencana penyampaian, bukan rehearsal yang telah diukur.
- Screenshot dan diagram implementasi mengacu ke worktree review lokal, belum membuktikan perubahan ada di branch main atau deployment.
- Pengecekan 180 reading terhadap fixture bukan held-out benchmark AI, studi pengguna, atau pembuktian dampak operasional.
- File sumber tidak ditimpa. Tidak ada commit, merge, atau push pada tugas deck ini.

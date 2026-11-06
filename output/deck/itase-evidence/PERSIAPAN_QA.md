# Persiapan Q&A ITASE 7.0

Gunakan jawaban ini sebagai bahan latihan, bukan klaim bahwa pilot atau benchmark sudah selesai. Presentasi utama ada pada slide 1–12; tombol pada slide 12 melompat ke penutup 18. Appendix 13–17 bisa dibuka dari penutup.

## Apa yang sebenarnya dicari track ini?

Guidebook meminta solusi untuk masalah nyata dengan AI sebagai komponen utama, kaitan ke salah satu SDG yang ditentukan, serta penjelasan mekanisme, pilihan teknologi, dan kelayakan. Model yang sudah tersedia diperbolehkan; training model sendiri bukan pembeda yang diwajibkan. Briefing final membobotkan kelengkapan PPT 20%, presentasi 50%, dan tanya jawab 30%. Rubrik 15/25/25/20/15 pada guidebook adalah konteks seleksi proposal; jangan menyebutnya sebagai bobot briefing final.

Sumber: guidebook hlm. 13–14 dan 16; dua gambar briefing final 28 Oktober 2026 dalam `Documents/`.

## Di mana AI-nya, jika konsolidasi dikerjakan backend?

Ada dua pekerjaan interpretasi. Pertama, LLM mengusulkan makna kolom dari header dan maksimal tiga contoh nilai per kolom. Kedua, LLM menyusun draft penjelasan dari feedback yang terikat ke reading terpilih. Konsolidasi, validasi, penolakan duplikasi, dan hitung status target memang tugas deterministik. Nilai inovasinya terletak pada penempatan interpretasi AI dalam workflow pelaporan yang tertelusur, bukan mengubah seluruh backend menjadi AI. Tunjukkan slide 5–7.

## Apakah ini inovasi algoritma baru?

Tidak diklaim demikian. Ini inovasi terapan pada workflow pelaporan divisional: memahami laporan yang berbeda, mempertahankan sumber angka, dan mengikat draft penjelasan ke feedback spesifik. Tim memakai pretrained LLM dan tetap perlu membuktikan kualitas serta beban koreksi pada tugas representatif. Jangan mengklaim pertama di dunia atau satu-satunya solusi.

## Mengapa memakai LLM, bukan aturan tetap saja?

Aturan alias dan fuzzy matching bisa menjadi baseline yang baik untuk istilah yang dikenal. LLM dipilih untuk interpretasi label dan konteks kolom yang bervariasi. Apakah keunggulan itu cukup besar harus diuji dengan layout terpisah dari pengembangan, jawaban acuan, dan jumlah koreksi analis. Rules only pada slide 11 adalah pembanding evaluasi, bukan opsi mematikan AI pada produk.

## Model apa yang dipakai?

Konfigurasi yang diuji dan dideploy memakai `google/gemini-2.5-flash-lite` melalui API kompatibel OpenAI (OpenRouter). Tim tidak melatih foundation model. Periksa `GET /api/v1/ai/status` lagi sebelum presentasi: endpoint itu melaporkan mode (`live`, `recorded`, `skipped`) dan model aktif. Jangan tampilkan API key. Jangan mengklaim versi underlying tertentu atau hasil studi komparatif model yang belum dilakukan.

## Bagaimana kalau kunci AI tidak ada saat demo?

Aplikasi menyatakan mode, bukan berpura-pura live. Tanpa kunci, tujuh layout demo memakai usulan tercatat dan UI memberi label “AI suggestion · recorded” beserta model dan tanggal perekaman; layout tidak dikenal berstatus skipped. Dengan kunci, jejaknya `live` dan menampilkan latensi. Ini fallback yang disengaja, bukan hasil inferensi baru, dan harus disebut begitu jika terjadi.

## Apakah hasil benchmark ini akurasi AI pada laporan nyata?

Tidak. `backend/evidence/mapping-benchmark-live.json` berisi lima layout sintetis tulisan tim, tiga pengulangan, memakai satu model. Aturan lokal memetakan 7/7 pada header konvensional dan Indonesia, 9/9 pada wide, tetapi 0/7 pada header tak dikenal dan 0/7 pada header reorder. Model memetakan 7/7 pada layout tak dikenal dan 6/7 pada reorder, dengan latensi sekitar 1,5–2 detik. Dua layout berbagi kosakata sehingga tidak independen. Koreksi analis, waktu end-to-end, dan akurasi laporan nyata belum diukur.

## Apakah data industri membuktikan masalah Infranexia?

Tidak secara khusus. Publikasi TM Forum melaporkan 2 dari 87 pemimpin senior IT dan jaringan pada surveinya menyatakan data perusahaan sepenuhnya didemokratisasi. Itu bukti kontekstual tentang akses/berbagi data, bukan statistik penggunaan Excel, Indonesia, atau Infranexia. Pengalaman magang memotivasi pilihan workflow; persona Rani menjelaskan pekerjaan tersebut secara ilustratif. Ketiganya adalah dasar bukti yang berbeda.

Sumber: https://inform.tmforum.org/research-and-analysis/reports/unlocking-ai-potential-through-a-modern-data-architecture

## Data demo ini data asli perusahaan?

Nilai aktual, target, lokasi, feedback, dan layout file input bersifat sintetis. Nama KPI, satuan, arah, dan kelompok pengirim mengikuti struktur workbook referensi. Tujuh file tersebut direkonstruksi untuk demonstrasi, bukan template asli tiap unit yang berhasil dipulihkan. Demo mencakup 90 KPI dan 180 reading pada dua lokasi fiktif. Tunjukkan label pada slide 8 dan rincian slide 14.

## Apakah 67,2% berarti akurasi model?

Tidak. Itu 121 reading memenuhi target dibagi 180 reading demo. Sisanya 59/180 = 32,8%. Ini distribusi target attainment. Pemeriksaan konsistensi output terhadap expected readings tidak menjadi akurasi AI pada laporan operasional atau held-out benchmark.

## Bagaimana menghindari RCA yang mengarang sebab?

Feedback diambil berdasarkan `fact_id`, sehingga terikat pada KPI, lokasi, dan tanggal yang dipilih. Tanpa feedback, sistem meminta bukti tanpa memanggil model. Draft harus mengutip ID feedback yang dikenal. Provider gagal atau sitasi invalid menghasilkan error, bukan draft pengganti. Tetap ada batas: ID valid tidak membuktikan setiap kalimat didukung sumber atau penyebabnya benar. Review analis masih wajib. Tunjukkan slide 7, 15, dan 16.

## Apakah data dikirim keluar? Apakah sudah aman untuk produksi?

Header dan sampel yang dibatasi, serta konteks reading/feedback untuk RCA, dikirim ke provider yang dikonfigurasi. Demo menggunakan data sintetis. Jangan mengklaim masking otomatis, on-premise deployment, sertifikasi, autentikasi, atau otorisasi produksi yang belum ada. Sebelum pilot, pemilik data dan organisasi perlu menyetujui kebijakan tersebut. Tunjukkan slide 6 dan 9.

## Mengapa bukan memasukkan Excel ke chatbot biasa?

Fokus omniKPI adalah pengelolaan workflow persisten: unit dan periode, review mapping, validasi, konsolidasi, sumber per reading, serta feedback yang tertaut. Jangan mengklaim chatbot atau BI tertentu tidak mampu mengolah file tanpa evaluasi produk pembanding. Jelaskan pekerjaan spesifik yang omniKPI jadikan alur produk, lalu buktikan melalui demo.

## Mengapa proposal awal berbeda?

Proposal mencakup visi lebih luas dan sudah membedakan beberapa komponen sebagai rancangan. Final memusatkan prototipe pada masalah pelaporan divisional yang dapat diuji. Hybrid retrieval, case library, Isolation Forest, pengelompokan insiden, dan verifikasi pemulihan tidak diklaim telah dibuktikan oleh alur demo saat ini. Tunjukkan slide 13.

## SDG 9-nya seberapa langsung?

Alignment utamanya pada arah Target 9.1: mendukung tim yang bertanggung jawab atas infrastruktur andal melalui laporan yang tertinjau dan tertelusur. Ini jalur kontribusi operasional, bukan bukti peningkatan keandalan. Indikator resmi 9.1.1 dan 9.1.2 terkait transportasi tidak diukur oleh produk ini. Target 9.c relevan sebagai konteks ICT; indikator 9.c.1 mengukur cakupan populasi jaringan mobile menurut teknologi, bukan jumlah KPI yang terunggah. Tunjukkan slide 10.

Sumber: https://sdgs.un.org/goals/goal9

## Apa bukti berikutnya sebelum mengklaim manfaat?

Uji laporan representatif dengan output acuan dan layout uji yang dipisahkan dari pengembangan. Bandingkan manual, baseline aturan, dan AI plus review. Ukur mapping benar, koreksi analis, waktu end-to-end termasuk tunggu dan retry, serta dukungan tiap klaim draft oleh feedback. Libatkan pemilik proses untuk menilai kelayakan dan biaya aktual. Jangan mengarang angka penghematan atau target ROI. Tunjukkan slide 11.

## Catatan demo saat presentasi

- Screenshot di deck berasal dari worktree lokal `C:/KPI_Dashboard_UI_Review`, bukan bukti bahwa perubahan sudah digabung ke main atau dideploy.
- Pastikan aplikasi, provider, dan koneksi diuji sebelum sesi. Siapkan workspace demo yang sudah terisi; jangan reset di tengah presentasi tanpa kebutuhan.
- Alur bukti singkat: buka workspace → pilih ED → inspect reading → lihat sumber → lihat feedback → lihat draft model dan referensinya.
- Bila koneksi gagal, gunakan screenshot aktual sebagai penjelasan alur dan katakan keterbatasan koneksinya. Jangan menyajikan teks sintetis yang diketik manual sebagai hasil panggilan model baru.
- Alokasi 600 detik pada notes merupakan rencana. Rehearsal tim tetap diperlukan untuk menyesuaikan kecepatan bicara dan pergantian presenter.

Catatan seed: Try demo menyiapkan dan mengonfirmasi fixture sintetis melalui layanan intake/confirm. Ini bukan pengukuran review analis; pada upload laporan pengguna, mapping tetap harus ditinjau dan dikonfirmasi analis.

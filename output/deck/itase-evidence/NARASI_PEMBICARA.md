# Narasi dan sumber per slide

## Slide 1

DURASI SASARAN: 35 detik.

Bayangkan Rani, analis performance jaringan, sedang menjawab stakeholder: angkanya sudah ada, tetapi kenapa KPI ini turun? Sebelum menjawab, ia perlu memastikan angka mana yang dipakai, dari divisi mana, dan penjelasan siapa yang mendukungnya. Rani adalah persona ilustratif; masalahnya berangkat dari pengalaman magang tim di fungsi Performance dan Support Network Infranexia. omniKPI kami usulkan untuk menyatukan pekerjaan itu: AI membantu memahami struktur laporan dan menyusun draft penjelasan, sementara analis tetap memutuskan. Agar persoalan ini tidak berhenti pada pengalaman tim, kita lihat konteks industri yang mendukungnya.

JENIS DATA DAN BATAS KLAIM
Persona Rani ilustratif. Pengalaman magang adalah motivasi tim, bukan hasil studi pengguna atau endorsement perusahaan.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
Documents/OMNIkpi.pdf, 31 halaman; khususnya hlm. 3-4, 7-16, 19-25, 30-31

## Slide 2

DURASI SASARAN: 50 detik.

Pengalaman tim selaras dengan persoalan industri yang lebih luas. Dalam publikasi survei TM Forum pada Agustus 2025, hanya dua dari delapan puluh tujuh pemimpin senior IT dan jaringan menyatakan perusahaan mereka telah sepenuhnya mendemokratisasi data. Ini ukuran akses dan berbagi data pada responden survei, bukan survei penggunaan Excel di Indonesia. White paper Ericsson pada Januari 2026 juga menjelaskan fragmentasi data lintas domain, platform, dan skema. Implikasinya bagi rancangan kami: data perlu disatukan secara semantik dan tetap memiliki jejak asal. omniKPI mengambil bagian yang spesifik dan dapat kami uji, yaitu laporan KPI divisional yang masuk sebagai file. Sekarang kita lihat pekerjaan orang yang harus menyatukannya.

JENIS DATA DAN BATAS KLAIM
Data industri eksternal: 2 dari 87 responden senior IT/network, TM Forum 2025. Bukan estimasi populasi atau data Infranexia. Tahun publikasi adalah metadata sumber.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
https://inform.tmforum.org/research-and-analysis/reports/unlocking-ai-potential-through-a-modern-data-architecture
https://www.ericsson.com/en/reports-and-papers/white-papers/future-proof-data-management-for-ai-networks

## Slide 3

DURASI SASARAN: 55 detik.

Konteks industri tadi menjadi konkret pada pekerjaan Rani. Dalam cerita ilustratif ini, ia menerima laporan dari beberapa unit, sebagaimana struktur paket demo kami. Sumber masalah yang sesungguhnya adalah pengalaman magang: supervisor menyatukan berbagai ekstrak Excel sebelum menilai KPI untuk stakeholder. Ada tiga kebutuhan yang berbeda. Analis memerlukan angka yang dapat dibandingkan. Pemilik KPI memerlukan feedback yang terhubung dengan pertanyaan yang tepat. Stakeholder memerlukan angka yang bisa ditelusuri. Saat KPI tidak memenuhi target, kompilasi angka belum menjawab penyebabnya; Rani tetap perlu bertanya ke divisi. Karena itu, solusi kami tidak berhenti pada dashboard. Ia harus menyambungkan laporan, angka, dan penjelasannya dalam satu alur yang dapat ditinjau.

JENIS DATA DAN BATAS KLAIM
Persona ilustratif dan adegan rekaan berdasarkan motivasi tim. Data demo (a): 7 laporan unit. Tidak ada kutipan responden atau ukuran waktu kerja.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
Documents/OMNIkpi.pdf, 31 halaman; khususnya hlm. 3-4, 7-16, 19-25, 30-31
frontend/public/demo/divisions/validation-summary.json

## Slide 4

DURASI SASARAN: 45 detik.

Jawaban kami adalah satu alur yang menghubungkan pekerjaan tadi. Pada Submit, unit dan tanggal menjadi konteks laporan. Pada Review mapping, model mengusulkan arti setiap kolom berdasarkan header dan contoh nilainya; analis dapat membetulkan usulan itu. Pada Consolidate, aturan memeriksa nilai dan duplikasi, lalu analis mengonfirmasi data sebelum masuk ke pandangan bersama. Pada Investigate, Rani memilih reading tertentu, menambahkan feedback divisi, dan meminta draft penjelasan dengan referensi. File, baris, dan unit pengirim tetap ikut bersama angka. Ini bukan klaim bahwa empat fase otomatis menghemat waktu tertentu: beberapa pekerjaan manual tetap ada di dalamnya. Perubahan yang kami demonstrasikan adalah keterhubungan alur. Berikutnya, kita lihat tugas interpretasi yang memang membutuhkan AI.

JENIS DATA DAN BATAS KLAIM
Empat fase adalah pengelompokan journey, bukan pengukuran efisiensi; bukan perbandingan durasi sebelum/sesudah.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend

## Slide 5

DURASI SASARAN: 65 detik.

Di sinilah elemen AI pertama bekerja. Ambil ED sebagai contoh sintetis: KPI WISA memuat nama KPI, Realisasi adalah nilai aktual, dan TGT adalah target. FORMULA memuat arah HIGHER BETTER, bukan rumus Excel yang harus dihitung. Kemiripan teks saja tidak selalu cukup untuk mengenali istilah yang berbeda atau membedakan kolom aktual dengan target. Parser memilih worksheet dan header, lalu model menerima header, usulan aturan awal, serta maksimal tiga contoh nilai per kolom. Model mengembalikan arti kolom beserta alasan singkat per kolom. AI bersifat opsional lewat kotak centang saat unggah; tanpa kunci provider, aplikasi memakai usulan tercatat untuk tujuh layout demo dan memberi label "AI suggestion Â· recorded", sedangkan layout lain berstatus skipped. Setiap respons membawa jejak mode, model, jumlah kolom, batas sampel, batch, dan latensi. Model yang dikonfigurasi adalah google/gemini-2.5-flash-lite melalui router kompatibel OpenAI, bukan model yang dilatih tim. Pilihan kelas LLM sesuai tugas interpretasi bahasa; kami belum melakukan studi yang membuktikan model ini paling unggul. Analis tetap meninjau hasilnya. Bagaimana kontrol ini ditempatkan di sistem?

JENIS DATA DAN BATAS KLAIM
Parameter implementasi: maksimum 3 sampel per kolom. Data demo: contoh aktual 97,8%, target 98,5%, dari ED. Header literal diverifikasi pada ed.xlsx / Report / baris 4. Model dan mode diverifikasi melalui GET /api/v1/ai/status.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend
frontend/public/demo/divisions/validation-summary.json

## Slide 6

DURASI SASARAN: 55 detik.

Arsitektur ini membedakan antarmuka, layanan aplikasi, penyimpanan, dan provider AI eksternal. Unit mengirim Excel atau CSV ke workspace React dan Vite. FastAPI memparse laporan dan menyiapkan konteks mapping, kemudian menghubungi model melalui API kompatibel OpenAI. Usulan kembali ke workspace untuk diperiksa. Jalur konfirmasi memvalidasi nilai dan menolak duplikasi sebelum menulis reading beserta sumbernya melalui SQLAlchemy ke SQLite. Layanan performance menghitung status target secara deterministik. Untuk RCA, layanan mengambil feedback yang terikat pada reading yang dipilih, bukan semua catatan di lokasi sekitar, lalu meminta draft model. Panah provider adalah jalur layanan AI; model tidak punya jalur tulis langsung ke database atau perangkat jaringan. Ini arsitektur prototipe lokal, belum arsitektur produksi. Sesudah data tersimpan, kita ikuti satu pertanyaan Rani sampai penjelasannya.

JENIS DATA DAN BATAS KLAIM
Tidak ada ukuran kinerja. Diagram menyederhanakan endpoint sebagai kelompok layanan, bukan mengklaim layanan terdistribusi. Provider menggunakan alias model konfigurasi lokal.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend

## Slide 7

DURASI SASARAN: 60 detik.

Sekarang stakeholder bertanya mengapa Compliance Deployment Supervision berada pada sembilan puluh tujuh koma delapan persen, di bawah target sembilan puluh delapan koma lima persen. Semua nilai pada adegan ini sintetis. Rani membuka reading dan melihat ED, ed.xlsx, baris lima, lokasi Demo North, serta tanggal laporannya. Namun sumber angka belum menjelaskan penyebab. Feedback ED yang tertaut pada reading itu menyatakan jadwal akses lokasi berubah sehingga penyelesaian deployment tertunda. Komponen AI kedua mengubah feedback menjadi draft beratribusi dan mengutip F1. Dalam uji lokal, model menghasilkan draft dengan referensi itu; teks di slide diparafrasekan ke Indonesia. Tanpa feedback, sistem meminta bukti dan tidak memanggil model. Bila provider gagal atau sitasi tidak valid, sistem menampilkan ringkasan feedback yang tetap beratribusi dan menandai bahwa AI tidak dipanggil, bukan mengarang draft pengganti. Sitasi yang valid membuktikan identitas sumber, bukan kebenaran sebab. Jadi Rani tetap menilai kecukupan bukti dan tindakan.

JENIS DATA DAN BATAS KLAIM
Data demo sintetis: aktual 97,8%; target 98,5%; baris sumber 5; tanggal 30 Juni 2026. F1 adalah ID feedback, bukan confidence score. Teks draft merupakan parafrasa Indonesia dari keluaran model lokal.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend
frontend/public/demo/divisions/validation-summary.json

## Slide 8

DURASI SASARAN: 55 detik.

Inilah workspace yang benar-benar berjalan dengan data sintetis, bukan mockup layar. Paketnya berisi tujuh laporan divisional, sembilan puluh KPI, dua lokasi fiktif, dan seratus delapan puluh reading pada satu tanggal demo. Nama KPI, unit, arah, dan kelompok pengirim mengikuti struktur workbook referensi; nilai, target, lokasi, feedback, dan layout input direkonstruksi untuk demo. Hasil referensinya adalah seratus dua puluh satu reading memenuhi target dan lima puluh sembilan belum memenuhi, setara enam puluh tujuh koma dua dan tiga puluh dua koma delapan persen. Itu distribusi status demo, bukan akurasi AI. File input, expected readings, dan checksum memungkinkan hasilnya diperiksa. Panggilan model dan draft bersitasi juga terlihat pada aplikasi. Bukti ini menunjukkan keterhubungan alur, tetapi belum mengukur produktivitas analis atau dampak jaringan.

JENIS DATA DAN BATAS KLAIM
Data demo (a): 90 KPI, 180 readings, 7 unit, 2 lokasi, 121 memenuhi dan 59 belum. Turunan (b): 121/180Ã—100=67,2%; 59/180Ã—100=32,8%, pembulatan satu desimal. Screenshot dari aplikasi review lokal, bukan versi main/deployment.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
frontend/public/demo/divisions/validation-summary.json
backend

## Slide 9

DURASI SASARAN: 40 detik.

Kelayakan awalnya ada pada titik masuk yang dekat dengan kebiasaan pengguna: laporan Excel atau CSV yang sudah mereka miliki. Prototipe tidak memerlukan penggantian sistem sumber untuk menunjukkan alur intake sampai investigasi. Namun kemudahan demo tidak sama dengan kesiapan produksi. Sebelum pilot, pemilik data perlu mengizinkan penggunaan laporan dan menetapkan kebijakan pengiriman sampel serta feedback ke provider. Identitas pengguna dan hak akses unit juga belum tersedia pada prototipe. Kami mengusulkan sponsor proses dari fungsi performance untuk menilai apakah manfaatnya cukup kuat dibanding usaha review dan biaya aktual. Belum ada harga, ROI, atau penghematan yang dapat kami klaim. Hubungan ke SDG pun kami tempatkan sebagai jalur kontribusi yang perlu dibuktikan, bukan dampak yang sudah terjadi.

JENIS DATA DAN BATAS KLAIM
Tidak ada proyeksi pendapatan atau nilai finansial. Sponsor/pemilik anggaran merupakan usulan untuk validasi, bukan pelanggan atau mitra yang sudah berkomitmen.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend

## Slide 10

DURASI SASARAN: 45 detik.

Mengapa ini relevan dengan SDG sembilan? Infrastruktur digital mendukung layanan yang dipakai masyarakat. Sebagai konteks global, ITU memperkirakan enam miliar orang menggunakan internet pada tahun 2025. Namun besarnya penggunaan internet tidak membuktikan dampak produk kami. Posisi yang lebih tepat adalah dukungan operasional pada arah Target sembilan titik satu, yaitu infrastruktur berkualitas, andal, dan tangguh. Rantai kontribusinya dimulai dari output yang dapat kami tunjukkan: dataset tertinjau dan sumber per reading. Output itu diharapkan membantu follow-up tim performance, lalu berpotensi mendukung keandalan layanan. Dua hubungan terakhir belum kami ukur. Target sembilan c adalah konteks telekomunikasi, sedangkan indikator resminya mengukur cakupan populasi. Dashboard kami tidak mengukur indikator tersebut. Untuk menguatkan kontribusi, langkah berikutnya adalah evaluasi bersama analis.

JENIS DATA DAN BATAS KLAIM
Industri eksternal: estimasi 6 miliar pengguna internet global pada 2025, ITU Facts and Figures 2025. Kode 9.1, 9.c, dan 9.c.1 adalah identitas target/indikator, bukan metrik demo. Kontribusi operasional dan outcome jaringan belum diukur.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
https://sdgs.un.org/goals/goal9
https://www.itu.int/en/ITU-D/Statistics/Pages/facts/default.aspx

## Slide 11

DURASI SASARAN: 55 detik.

Agar nilai AI tidak berhenti pada klaim, kami sudah menjalankan benchmark sintetis lima layout dengan tiga pengulangan memakai google/gemini-2.5-flash-lite. Aturan lokal unggul pada header konvensional dan Indonesia, tetapi gagal total pada header tak dikenal dan header yang diacak. Model memetakan seluruh tujuh kolom pada layout tak dikenal dan enam dari tujuh pada layout reorder; satu kolom, Reporting area, tetap dipetakan sebagai ignore. Latensi pratinjau naik dari sekitar nol koma nol satu detik menjadi sekitar satu koma lima sampai dua detik. Artinya AI dipakai untuk kasus yang tidak bisa diselesaikan aturan, bukan untuk semuanya. Hasil ini tetap sintetis, berasal dari lima layout tulisan tim, bukan laporan divisi nyata dan bukan data held-out; dua layout berbagi kosakata sehingga tidak independen. Yang belum diukur adalah koreksi analis sesungguhnya, waktu end-to-end, dan dukungan klaim RCA pada laporan nyata. Rencana berikutnya memakai laporan representatif dengan jawaban acuan serta pemisahan data pengembangan dan pengujian.

JENIS DATA DAN BATAS KLAIM
Semua metrik pada slide tetap menjadi kerangka evaluasi untuk laporan nyata; yang sudah terukur hanya benchmark sintetis lima layout (tak dikenal 0/7 ke 7/7, reorder 0/7 ke 6/7, latensi sekitar 1,5 sampai 2 detik). Rumus kualitas mapping = benar/dinilai; koreksi = diubah/dinilai; dukungan draft = klaim didukung/klaim dinilai. Tidak ada klaim penghematan waktu.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
Documents/OMNIkpi.pdf, 31 halaman; khususnya hlm. 3-4, 7-16, 19-25, 30-31
backend

## Slide 12

DURASI SASARAN: 40 detik.

Kita kembali ke pertanyaan Rani di awal: angkanya sudah ada, mengapa KPI ini turun? omniKPI tidak menjawab dengan menebak penyebab dari deviasi angka. Produk ini lebih dulu menyatukan laporan, menjaga sumber setiap reading, lalu menggunakan feedback divisi sebagai dasar draft penjelasan. AI berada di dua pekerjaan interpretasi: memahami arti kolom dan menyusun narasi yang beratribusi. Validasi dan perhitungan angka tetap dilakukan oleh kode, sementara konfirmasi dan keputusan tetap di analis. Prototipe sintetis sudah menunjukkan alur tersebut. Bukti berikutnya adalah kualitas output dan beban review pada pekerjaan analis yang representatif. Itulah kontribusi yang kami bawa: membuat angka dan bukti siap ditinjau bersama untuk mendukung tim penjaga infrastruktur digital.

JENIS DATA DAN BATAS KLAIM
Kesimpulan membedakan prototipe yang berjalan dari evaluasi yang masih diusulkan. Tidak ada klaim penghematan, akurasi lapangan, atau dampak jaringan.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend
frontend/public/demo/divisions/validation-summary.json

## Slide 13

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Proposal awal membahas visi yang lebih luas. Pada saat pengajuan, banyak komponen sudah ditandai sebagai rancangan, dan lampiran mengungkap keterbatasan ketika model menerima log konteks yang tidak relevan. Final ini mempersempit demonstrasi pada pain point pelaporan divisional dari pengalaman tim. Koneksi upload sampai konsolidasi sekarang berjalan, sementara draft RCA menggunakan feedback yang sudah terikat ke reading. Ini pemurnian cakupan, bukan klaim semua rencana di proposal sudah selesai. Hybrid retrieval, Isolation Forest, case library, dan verifikasi pemulihan tidak kami masukkan sebagai fitur yang dibuktikan oleh demo ini.

JENIS DATA DAN BATAS KLAIM
Tidak ada metrik kuantitatif.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
Documents/OMNIkpi.pdf, 31 halaman; khususnya hlm. 3-4, 7-16, 19-25, 30-31
backend

## Slide 14

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Tabel dan stacked bar berasal langsung dari ringkasan validasi fixture. BGES dan OLO memiliki empat puluh satu KPI dengan delapan puluh dua reading, MBB tujuh belas dan tiga puluh empat, ED tiga belas dan dua puluh enam. Unit lainnya mengikuti tabel. Tiap KPI memiliki dua lokasi pada tanggal demo yang sama. Jumlah status per unit dihitung oleh paket referensi, bukan direka untuk chart ini. Struktur nama, satuan, arah, dan kepemilikan mengikuti referensi KPI, sedangkan nilai aktual dan target adalah sintetis. Karena distribusinya dibuat untuk demonstrasi, persentase memenuhi target tidak menyatakan kesehatan jaringan perusahaan.

JENIS DATA DAN BATAS KLAIM
Data demo (a): seluruh angka pada tabel dan seri chart berasal dari validation-summary.json. Total 90 KPI, 180 readings, 121 memenuhi, 59 belum; 7 unit dan 2 lokasi. Tanggal demo 30 Juni 2026.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
frontend/public/demo/divisions/validation-summary.json

## Slide 15

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Untuk pertanyaan teknis, pusat skema adalah fact_kpi. Ia mereferensikan definisi KPI, lokasi, dan periode, serta menyimpan actual, target, dan status. ReadingSource memakai fact_id sebagai primary key sekaligus foreign key, sehingga angka dapat dirunut ke submission dan source row. Submission menyimpan filename, worksheet, serta unit pengirim. DivisionFeedback memakai foreign key fact_id: ini yang membuat penjelasan spesifik terhadap KPI, lokasi, dan periode tertentu. Panah menunjukkan relasi referensial dari induk ke tabel yang mereferensikannya; bukan urutan panggilan API. Diagram ini sengaja tidak mengklaim case library atau embedding sebagai bagian aktif alur divisional.

JENIS DATA DAN BATAS KLAIM
Tidak ada metrik. ID dan nama tabel adalah struktur implementasi; diagram bukan ERD lengkap semua tabel legacy.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend

## Slide 16

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Ada beberapa batas yang bisa dijelaskan secara konkret. Tanpa feedback, endpoint langsung mengembalikan permintaan bukti, sehingga LLM tidak diminta menebak. Bila provider gagal atau kunci tidak ada, intake memakai usulan tercatat yang diberi label "AI suggestion Â· recorded" dan menyatakan bahwa itu bukan panggilan live; bila layout tidak dikenal, statusnya skipped. Pada RCA, kegagalan provider atau sitasi tidak valid menghasilkan ringkasan feedback beratribusi, bukan draft model, dan respons menyatakan ai_invoked false. Draft yang sah harus memuat ID feedback yang dikenal serta kutipan inline yang konsisten. Pada intake, validasi dan penolakan duplikasi berjalan sebelum confirm. Tetapi pemeriksaan ID belum membuktikan setiap kalimat didukung sumber atau penyebabnya benar, sehingga review manusia tetap penting. Autentikasi, masking otomatis, dan kontrol produksi belum ada pada alur demo ini.

JENIS DATA DAN BATAS KLAIM
Tidak ada ukuran efektivitas guardrail. Pernyataan adalah perilaku implementasi, bukan klaim keamanan menyeluruh.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend

## Slide 17

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Slide ini hanya untuk memeriksa kelengkapan atau menjawab pertanyaan format. Briefing final meminta delapan bagian dan membobotkan kelengkapan dua puluh persen, presentasi lima puluh persen, serta tanya jawab tiga puluh persen. Guidebook memuat rubrik seleksi proposal yang berbeda, sehingga tidak kami gunakan sebagai bobot final. Ketentuan pemanfaatan AI meminta komponen utama, penjelasan mekanisme, alasan pemilihan, dan peran AI. Peserta dapat memanfaatkan model tersedia tanpa training dari nol. Presentasi utama dialokasikan sepuluh menit, dengan sepuluh menit tanya jawab sesuai briefing.

JENIS DATA DAN BATAS KLAIM
Aturan kompetisi: 20/50/30 persen, 10 menit presentasi + 10 menit Q&A. Rubrik proposal: 15/25/25/20/15 persen. Angka pada tabel adalah referensi nomor slide, bukan metrik hasil.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
Documents/GUIDEBOOK ITASE 7.0.pdf, halaman 13-14 dan 16
Documents/WhatsApp Image 2026-10-28 at 19.49.23.jpeg; Documents/WhatsApp Image 2026-10-28 at 19.50.32.jpeg

## Slide 18

APPENDIX: gunakan saat Q&A, tidak termasuk alokasi presentasi utama.

Terima kasih. Kami siap membahas mekanisme AI, sumber data, batas validasi, rancangan pilot, atau kaitan SDG. Gunakan tautan appendix untuk membuka bukti tambahan; tautan repository mengarah ke kode publik. Versi prototipe yang dipresentasikan berasal dari worktree lokal review yang belum digabung ke main.

JENIS DATA DAN BATAS KLAIM
Tidak ada metrik. Identitas universitas mengikuti materi tim yang disediakan.
Nomor slide, kode SDG, versi produk, nomor referensi, dan urutan langkah merupakan identitas, bukan ukuran hasil.

SUMBER
backend
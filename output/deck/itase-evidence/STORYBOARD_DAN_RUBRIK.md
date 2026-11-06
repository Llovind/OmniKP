# Storyboard dan rencana penyampaian

Presentasi utama: slide 1–12, alokasi total 600 detik (10 menit). Appendix: 13–17. Penutup: 18. Klik “Akhiri presentasi” pada slide 12 untuk melewati appendix. Durasi adalah rencana, bukan hasil rehearsal.

| Slide No & Type | Action Title (Headline) | Core Content & Data Points | Visual Layout Anchor & Layout Instruction | C-Level Executive So What? |
| --- | --- | --- | --- | --- |
| 1 / Hook | Angkanya sudah ada. Mengapa KPI ini turun? | Pertanyaan analis; motivasi magang | Foto telco sumber deck + headline + identitas tim | Pertanyaan pengguna menjadi alasan membangun produk. |
| 2 / Industry | Silo data menghambat kesiapan AI telco | TM Forum 2/87; fragmentasi Ericsson | Angka besar kiri; dua implikasi kanan | Celah yang kami pilih: pelaporan divisional yang masih bergantung pada file. |
| 3 / SCQA | Rani menyatukan laporan, lalu mencari penjelasan | Rani ilustratif; pekerjaan analis, divisi, stakeholder | Persona kiri; SCQA kanan | Rani membutuhkan satu pandangan KPI yang tetap menyimpan pemilik dan sumbernya. |
| 4 / Solution | Satu alur KPI, keputusan tetap di analis | Empat fase journey | Timeline horizontal native | Perbedaan utamanya: interpretasi AI masuk ke alur kerja, sebelum data dikonfirmasi. |
| 5 / AI mechanism | AI menafsirkan kolom sebelum angka digabung | Header + ≤3 sampel; JSON; model alias | Tabel native → interpretasi → mapping native | Analis memeriksa usulan; JSON yang valid belum menjamin pemetaan benar. |
| 6 / Architecture | AI mengusulkan; analis mengendalikan data | React/Vite, FastAPI, SQLite, external API | Diagram native berlapis + konektor | Angka tidak ditulis oleh model: konfirmasi analis dan validasi mengendalikan penyimpanan. |
| 7 / Evidence-linked RCA | Shortfall ditelusuri hingga penjelasan divisi | 97,8 vs 98,5; ed.xlsx baris 5; F1 | Reading → feedback → draft native | Sitasi mengikat penjelasan ke feedback; kebenaran penyebab tetap harus diperiksa analis. |
| 8 / Prototype proof | Demo menyatukan laporan yang dapat diperiksa | 90/180/7/2; 121/59; 67,2/32,8% | Screenshot aktual + native donut | Demo membuktikan alur dan konsistensi fixture, belum efektivitas pada laporan lapangan. |
| 9 / Feasibility | Adopsi dimulai dari file yang sudah dipakai | Input eksisting; izin data, akses, biaya | Sudah berjalan vs sebelum pilot | Mulai dari satu alur yang bisa diuji, lalu tambah kontrol sebelum membawa data sensitif. |
| 10 / SDG | Pelaporan tertelusur mendukung arah SDG 9.1 | Target 9.1; 6 miliar konteks ITU | Tile SDG + rantai output/contribution/outcome | Keandalan layanan adalah tujuan lanjutan; demo belum membuktikan perubahan outcome jaringan. |
| 11 / Validation | Nilai AI diuji lewat kualitas dan beban review | Manual vs rules vs AI; koreksi, kualitas, waktu, dukungan | Tiga pembanding + empat ukuran | Nilai AI dibuktikan jika output benar dan pekerjaan koreksi dapat dipertanggungjawabkan. |
| 12 / Recommendation | Angka, sumber, dan bukti siap ditinjau Rani | Keputusan manusia, workflow AI, validasi berikutnya | Tiga baris ringkasan | Rani tetap memutuskan; omniKPI menata angka dan bukti yang ia perlukan. |
| 13 / Scope appendix | Final memusatkan proposal pada alur divisional | Proposal vs implemented | Perbandingan empat baris | Arah awal dipertahankan; status implementasi diperjelas agar rencana tidak dibaca sebagai hasil. |
| 14 / Fixture appendix | Status demo dapat diperiksa per unit | Counts by unit and status | Tabel native + stacked bar native | 121 memenuhi + 59 belum = 180 readings; distribusi ini bukan skor akurasi AI. |
| 15 / Data architecture appendix | Setiap reading menautkan angka dengan bukti | FK fact/source/submission/feedback/dimensions | ERD native | Feedback untuk satu fact_id tidak otomatis menjadi bukti bagi KPI atau tanggal lain. |
| 16 / Controls appendix | Sistem meminta bukti sebelum menyusun jawaban | Evidence gate, provider errors, citation checks | Empat kondisi dan perilaku | Guardrail mengurangi jalur kesalahan; pemeriksaan ID tidak menggantikan penilaian manusia. |
| 17 / Rubric appendix | Delapan bagian wajib hadir dalam cerita utama | Final20/50/30 and required8sections | Crosswalk ke slide utama | Prioritas final adalah cerita yang jelas, demo yang dapat dijelaskan, dan jawaban yang akurat. |
| 18 / Close | Terima kasih | Identitas tim dan repository | Navy typography | Diskusi bukti dan langkah berikutnya. |

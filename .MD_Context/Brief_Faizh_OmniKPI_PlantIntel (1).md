# 📋 RESEARCH & CONTENT BRIEF: OMNIKPI / PLANTINTEL AI

**Role:** Data Research, Business Analyst, & Proposal/Deck Writer
**Assignee:** Faizh
**Objective:** Mengumpulkan data pendukung (*evidence*), memvalidasi klaim, dan menyusun *outline* narasi yang 100% *aligned* dengan rubrik penjurian CALIBER 2026 & ITASE 7.0.

Dokumen ini *strictly* mengacu pada *Guidebook* resmi CALIBER 2026 dan ITASE 7.0. Semua instruksi di sini dirancang untuk mengarahkan riset Faizh agar setiap argumen bisnis dan data yang dia kumpulkan **langsung mencetak skor pada rubrik penjurian**, tanpa membuang waktu pada narasi "teknologi keren" yang tidak dinilai.

---

## 0. PROJECT CONTEXT (BUAT FAIZH YANG BARU MASUK)

Biar riset lu nggak salah arah, ini gambaran singkat produknya:

**Asal usul:** Project ini pivot dari KPI WISA Dashboard (dashboard KPI telco yang dibangun pas internship di Infranexia — ETL 90+ KPI dari 32 file Excel). Sekarang di-generalize jadi platform dual-track: satu codebase yang sama dipakai buat dua kompetisi berbeda domain — ITASE 7.0 (telco) dan CALIBER 2026 (petrokimia, case Chandra Asri).

**Nama produk:** OmniKPI / PlantIntel — Agentic Enterprise KPI Intelligence Platform.

**Masalah yang diselesaikan:**
- Data operasional (Excel, LIMS, DCS, SAP, WISA) tersebar dan terisolasi ("dark data").
- Engineer/manager habis waktu buat extract-clean data manual, bukan analisis.
- Waktu diagnosa root cause pas ada anomali KPI itu lambat dan mahal.
- Pengetahuan tacit soal troubleshooting sering hilang, nggak terdokumentasi.

**Arsitektur — Tri-Agent System:**
1. **Harvester Agent** — user upload Excel berantakan, sistem otomatis parsing & mapping kolom ke database terstruktur (pakai fuzzy matching, fallback ke LLM kalau confidence rendah).
2. **ML Heatmap Engine** — dashboard yang render matrix KPI, highlight node yang anomali (merah/hijau) berdasarkan deteksi statistik (Z-score), bukan tebakan AI.
3. **RCA Agent** — kalau node merah diklik, LLM narasikan root cause analysis berdasarkan data historis + shift logs yang di-retrieve, kasih rekomendasi tindakan (tapi cuma *advisory*, nggak eksekusi otomatis).

**Prinsip keamanan (penting buat narasi Feasibility):** AI ini read-only terhadap sistem operasional (OT), ngikutin Purdue Model / ISA-95. AI cuma kasih rekomendasi (*human-in-the-loop*) — nggak pernah mengeksekusi perintah fisik kayak buka-tutup katup pabrik sendiri. Ini garansi zero cyber-safety risk yang harus konsisten muncul di narasi lu.

Tugas lu bukan ngoding — tugas lu nyariin **peluru data** yang bikin klaim-klaim di atas defensible di depan juri, bukan kedengeran kayak asumsi ngarang.

---

## 1. COMPETITION SCORING MAP (RUBRIK PENJURIAN)

Ini *cheat-sheet* lu. Setiap kalimat yang lu tulis di proposal atau deck **harus** menjawab salah satu kriteria di tabel ini. Kalau sebuah data nggak berkontribusi ke metrik ini, **buang**.

| Area Fokus Produk | Kriteria ITASE 7.0 (Bobot) | Kriteria CALIBER 2026 | *Feature* OmniKPI yang Menjawab | ⚠️ Kelemahan Kita Saat Ini (Fokus Riset Lu) |
| :--- | :--- | :--- | :--- | :--- |
| **The "Why"** | Identifikasi Permasalahan (15%) | Problem Understanding & Business Impact | 4 Hard Data Points (Dark Data, 80/20 Trap, Cost of Downtime, Tacit Knowledge) | Butuh kutipan/sumber asli untuk angka klaim kita. Tanpa kutipan, juri anggap ini asumsi fiktif. |
| **The "What"** | Inovasi Solusi (25%) + Pemanfaatan AI (25%) | Solution Design & Prototype Quality | Tri-Agent System: Harvester (ETL), ML Heatmap (Visualisasi), RCA Agent (Diagnosis) | Harus bisa menjustifikasi kenapa pakai Fuzzy Matching & LLM RAG, bukan sekadar "chatbot biasa". |
| **The "How"** | Kelayakan Implementasi (20%) | Feasibility & Roadmap | Purdue Model / ISA-95 Compliance, Human-in-the-loop, Z-Score Deterministic Math | Juri industri sangat kritis di sini. Cari referensi cara implementasi AI yang aman di pabrik (OT security). |
| **Context Fit** | Kontribusi SDGs (15% — SDG 9) | Chemical Domain Relevance | Use Case Telco (ITASE) dan Pabrik Kimia/OEE (CALIBER) | Riset metrics spesifik Chandra Asri (Flaring Loss, Ethylene Yield, MTTR). |

---

## 2. RESEARCH TASKS FOR FAIZH (DATA & EVIDENCE)

Tugas lu adalah mencari peluru (data) untuk menjustifikasi arsitektur teknis yang sedang dibangun. Cari paper, artikel, laporan tahunan, atau jurnal untuk memvalidasi angka-angka berikut:

### TASK A: Validasi "The 4 Hard Data Points" (Sangat Krusial!)
- **Claim 1:** "73% data operasional jadi Dark Data/Siloed." (Cari sumbernya — Forrester/Gartner/IBM report soal industrial data.)
- **Claim 2:** "80/20 Rule: Engineer habiskan 80% waktu buat rekap data manual." (Cari survei produktivitas Data Analyst/Engineer.)
- **Claim 3:** "Kerugian downtime mencapai $100k/Hour." (Cari referensi kerugian unplanned downtime spesifik industri Petrokimia/Manufaktur skala besar.)
- **Claim 4:** "40% Tacit Knowledge hilang." (Cari artikel soal aging workforce atau knowledge loss di industri berat/manufaktur.)

**⚠️ Aturan sourcing — WAJIB dibaca sebelum mulai:**
Kalau lu nggak nemu angka pasti yang spesifik ke domain kita (telco/petrokimia), boleh pakai angka proxy dari industri yang mirip (manufaktur umum, industri berat lain) — TAPI footnote-nya harus eksplisit bilang itu proxy, bukan angka asli domain kita. Contoh footnote yang benar: *"Angka ini berdasarkan studi pada sektor manufaktur umum; belum ada data spesifik industri petrokimia yang ditemukan."* Jangan tempel sumber yang cuma "mirip-mirip" terus dibiarkan kedengaran seolah itu angka asli Chandra Asri/telco — juri industri (khususnya CALIBER) kemungkinan besar tau persis angka riil di sektor mereka, dan kalau ketauan angka kita "dipaksa cocok," itu lebih ngerusak kredibilitas kita daripada kita jujur bilang belum ketemu angka pasti.

### TASK B: Riset Spesifik Chandra Asri (Domain Relevance)
Buka Annual Report atau Sustainability Report PT Chandra Asri Pacific Tbk terbaru. Cari kata kunci terkait efisiensi operasional, digitalisasi, atau reliability. Jadikan ini landasan di latar belakang deck CALIBER agar terlihat tailor-made.

### TASK C: Competitive Case Studies
Cari 2-3 contoh real perusahaan besar (misal Shell, ExxonMobil, atau Telkomsel) yang sudah menggunakan AI for Root Cause Analysis atau Automated Dashboards.

**⚠️ Batasan narasi — penting:** Case study ini dipakai buat membuktikan bahwa *pendekatan/arah teknologi* kita (AI-driven RCA, automated anomaly detection) sudah terbukti jalan di industri global — itu klaim yang valid dan memperkuat poin Feasibility. **Yang TIDAK boleh** adalah narasi yang mengesankan OmniKPI/PlantIntel *sendiri* sudah "teruji" atau "divalidasi" seperti sistem-sistem itu — karena produk kita belum pernah di-deploy di mana pun. Framing yang aman: *"Pendekatan serupa telah diadopsi oleh [Perusahaan X] untuk [use case Y], menunjukkan arah teknologi ini feasible untuk diimplementasikan di skala industri."* Jangan sampai kalimatnya blur jadi "solusi kita sudah teruji seperti mereka."

---

## 3. PITCH DECK NARRATIVE ARC (CALIBER 2026 FOCUS)

Ikuti *strict format* 7 Slide wajib dari Guidebook CALIBER (Halaman 10). Ini outline narasinya — tugas lu mengisi teks poin-poinnya berdasarkan riset di Task A-C.

- **Slide 1: Cover** → Nama Tim & Case 2.
- **Slide 2: Background & Problem Statement** → *[Skoring: Problem Understanding]* Masukkan hasil validasi Task A (4 Hard Data). Ceritakan mahalnya Alert Fatigue & Data Silos.
- **Slide 3: Solution (The Tri-Agent Platform)** → *[Skoring: Solution Design]* Jabarkan Harvester (Data Ingestion), ML Viz (Anomaly Heatmap), RCA Agent (LLM).
- **Slide 4: Business Impact & KPIs** → *[Skoring: Business Impact]* Kuantifikasi keuntungan — berapa jam MTTR yang dihemat, berapa downtime cost yang dihindari.
  **⚠️ Framing wajib:** angka penghematan di slide ini adalah proyeksi/model berdasarkan benchmark eksternal (dari Task A/C), BUKAN hasil aktual dari sistem yang sudah berjalan — karena OmniKPI belum pernah di-deploy nyata. Tulis eksplisit "estimasi berdasarkan benchmark industri" di slide, jangan biarkan angka itu kedengaran seperti hasil terukur dari sistem kita sendiri. Ini slide paling rawan kepeleset ke overclaim pas nulis under deadline pressure — double-check sebelum finalisasi.
- **Slide 5: Feasibility & Roadmap** → *[Skoring: Feasibility & Roadmap]* Krusial. Jelaskan keamanan IT/OT (Purdue Model), konsep Read-Only Data Diode, dan Human-in-the-Loop Advisory (AI tidak memutar katup pabrik secara otomatis).
- **Slide 6: Conclusion** → Summary value proposition.
- **Slide 7: Team Profile** → Format tabel wajib (Nama, Major, Semester, Expertise, Contribution).

---

## 4. PROPOSAL DOCUMENT STRUCTURE (ITASE 7.0 FOCUS)

Proposal ITASE harus mengikuti format wajib (Guidebook Halaman 17). Fokus narasi di sini adalah Telco KPI (Kisah Nyata Ms. Metha) dan SDG 9.

- **BAB I: Pendahuluan** → Masukkan riset Task A (konteks Telco/WISA). Fokus pada rumusan masalah: grueling manual work dan fragmentasi data.
- **BAB II: Konsep Solusi AI** → Deskripsikan peran AI Agent (RAG/LLM) untuk RCA dan Harvester Agent untuk mapping data. Sebutkan bahwa kita mematuhi aturan lomba (tidak men-train LLM dari nol, tapi menggunakan RAG/Prompting dengan model pre-trained).
- **BAB III: Perancangan Solusi** → Narasi untuk Flowchart (Excel Ingest → Star Schema DB → Z-Score Anomaly → LLM RCA).
- **BAB IV: Rencana Implementasi** → Sambungkan langsung dampak platform ini terhadap SDG 9 (Industry, Innovation & Infrastructure) — misal menciptakan infrastruktur data yang resilient dan mengadopsi teknologi bersih/efisien. Jelaskan Feasibility (keamanan data, otentikasi).
- **BAB V: Penutup & Daftar Pustaka** → Cantumkan semua paper/link referensi dari Task A & C.

---

## 5. RISK CHECK (UNVERIFIABLE CLAIMS)

Sebelum nulis kalimat final di proposal atau deck, pastikan lewat checklist ini:

1. **Downtime Cost ($100k/hr):** Kalau gagal menemukan sumber absolut angka ini untuk Chandra Asri/Petrokimia, ubah narasinya jadi: *"Berdasarkan studi benchmark industri petrokimia global (Sumber X), unplanned downtime dapat menimbulkan kerugian hingga $Y/jam..."*
2. **RCA Accuracy/Confidence:** Jangan klaim "AI kita 100% akurat". Gunakan narasi Deterministic Z-Score: *"Sistem mendeteksi anomali secara deterministik (Z-Score > 2.0), lalu AI hanya bertugas memberikan konteks naratif (narrating the root cause), sehingga menghilangkan risiko halusinasi AI."*
3. **Deployment Reality:** Jangan klaim sistem berjalan otonom penuh. Tegaskan klaim Advisory Mode / Human-in-the-Loop agar juri teknis tidak menilai sistem kita sebagai ancaman Cybersecurity OT.
4. **Case Study Framing (baru):** Jangan biarkan kalimat soal Shell/ExxonMobil/Telkomsel terbaca seolah OmniKPI sendiri sudah divalidasi seperti mereka. Bedakan tegas: "pendekatan ini terbukti di industri global" (valid) vs "produk kita sudah teruji" (tidak valid, karena belum pernah deploy).

---

*(End of Brief)*

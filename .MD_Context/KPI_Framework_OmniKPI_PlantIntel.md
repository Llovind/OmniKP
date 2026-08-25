# KPI ARCHETYPE FRAMEWORK — OMNIKPI / PLANTINTEL
**Basis riset, bukan asumsi.** Dokumen ini memetakan struktur KPI generic yang dipakai `dim_kpi` di database, berdasarkan dua standar industri independen yang benar-benar ada — bukan framework yang gua karang buat "menyatukan semua industri."

---

## 1. SUMBER FRAMEWORK (BUKAN NGARANG)

### Sisi Manufaktur/Petrokimia (CALIBER) — ISO 22400
- **ISO 22400** ("Automation systems and integration — KPI for manufacturing operations management") adalah standar internasional resmi yang mendefinisikan 34 KPI manufaktur, lengkap dengan formula, satuan, dan definisi presisi — dirancang biar dua pabrik berbeda bisa hitung angka yang sama dengan cara yang sama.
- Standar ini terikat ke model ISA-95 (persis konsep Purdue Model yang udah kita pakai di arsitektur Harvester Agent).
- KPI-nya terkelompok ke 4-5 kategori besar: **Availability/Utilization, Performance/Speed, Quality/Yield, Reliability/Maintenance (MTBF, MTTR), dan Logistics/Inventory.**
- KPI komprehensif OEE = Availability × Performance × Quality — ini formula resmi standar, bukan simplifikasi kita.

### Sisi Telekomunikasi (ITASE) — TM Forum + Praktik Industri
- **TM Forum** adalah badan standar telco global (~800 perusahaan anggota) yang mengembangkan Business Process Framework (eTOM) dan Application Framework (TAM), dipakai operator telco real untuk fault management dan performance management.
- Praktik industri umum mengelompokkan KPI telco ke kategori: **Network Performance (availability, latency, packet loss, jitter), Operations (MTTR, MTTD), Customer Experience, dan Finance.**
- Sub-kategori network performance yang umum dipakai di level RAN: **Accessibility, Retainability, Mobility, Integrity, Availability.**

### Poin Penting: Ini Bukan "Satu Framework Universal"
Kita **tidak** mengklaim ada satu standar yang meng-cover semua industri. Yang kita klaim: dua standar independen (ISO 22400 dan TM Forum/praktik telco) **secara terpisah** sampai pada pola struktural yang mirip — availability, throughput/performance, dan quality selalu muncul sebagai kategori inti. Kesamaan pola inilah yang menjadi basis desain `dim_kpi` yang generalizable.

---

## 2. TABEL ARKETIPE KPI — PEMETAAN LINTAS DOMAIN

| Arketipe (Category) | Definisi Generic | ISO 22400 — Istilah Petrokimia (CALIBER) | TM Forum/Praktik — Istilah Telco (ITASE) | Formula Pattern |
|---|---|---|---|---|
| **Availability** | Persentase waktu aset/sistem beroperasi dari waktu yang direncanakan | Equipment Availability (Operating Time / Planned Production Time) | Network Availability / Uptime (target umum: "five nines" 99.999%) | `Actual Uptime / Planned Uptime × 100%` |
| **Performance/Throughput** | Kecepatan atau volume output dibanding kapasitas ideal | Performance Rate (Ideal Cycle Time vs Actual Cycle Time), Throughput Rate | Data Throughput, Traffic Volume, Bandwidth Utilization | `Actual Output / Ideal Output × 100%` |
| **Quality/Integrity** | Persentase output yang memenuhi standar tanpa cacat/gangguan | Quality Ratio, First Pass Yield, Scrap Ratio | Packet Loss Rate, Call Drop Rate, Bit Error Rate | `Good Units (atau Sesi Bersih) / Total Units × 100%` |
| **Reliability/Maintenance** | Ketahanan sistem terhadap kegagalan dan kecepatan pemulihan | MTBF (Mean Time Between Failure), MTTR (Mean Time To Repair) | MTTR (jaringan), MTTD (Mean Time To Detect) | `Total Uptime / Jumlah Kegagalan` (MTBF); `Total Downtime / Jumlah Insiden` (MTTR) |
| **Composite/Effectiveness** | Skor gabungan yang meringkas beberapa arketipe di atas jadi satu angka | OEE = Availability × Performance × Quality | (Belum ada 1 metrik gabungan standar setara OEE di telco — biasanya dilaporkan terpisah per kategori) | `A × P × Q` (khusus manufaktur; telco tetap terpisah) |

**Catatan jujur:** Baris terakhir (Composite/Effectiveness) menunjukkan generalisasi **tidak sempurna** — telco nggak punya padanan OEE tunggal yang diformalkan seperti manufaktur. Ini bagus untuk disebut di proposal sebagai *"batasan yang kami sadari"* — itu justru nambah kredibilitas dibanding pura-pura semua sempurna simetris.

---

## 3. SKEMA `dim_kpi` (KOLOM DATABASE)

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `kpi_id` | INTEGER (PK) | ID unik KPI |
| `kpi_name` | TEXT | Nama KPI sesuai istilah domain asli (mis. "Ethylene Yield", "Network Availability") |
| `kpi_archetype` | TEXT (FK ke lookup) | Salah satu dari 5 arketipe di atas — ini yang bikin cross-domain query bisa jalan |
| `domain_id` | INTEGER (FK ke `dim_domain`) | 1 = telco, 2 = petrochemical |
| `formula_description` | TEXT | Formula/cara hitung, mengikuti definisi standar (ISO 22400 atau praktik TM Forum) |
| `unit` | TEXT | %, ms, jam, unit/jam, dll |
| `target_threshold` | REAL | Nilai target/SLA untuk KPI ini |
| `higher_is_better` | BOOLEAN | TRUE untuk Availability/Performance/Quality; FALSE untuk MTTR/Packet Loss |
| `source_standard` | TEXT | "ISO 22400" atau "TM Forum / Industry Practice" — buat traceability kalau juri tanya sumbernya |

---

## 4. CONTOH SEED DATA (BUAT ISI `dim_kpi`)

| kpi_name | kpi_archetype | domain | formula_description | unit | source_standard |
|---|---|---|---|---|---|
| Equipment Availability | Availability | Petrochemical | Operating Time / Planned Production Time | % | ISO 22400 |
| Network Availability | Availability | Telco | Actual Uptime / Total Period | % | TM Forum/Industry |
| OEE | Composite | Petrochemical | Availability × Performance × Quality | % | ISO 22400 |
| Throughput Rate | Performance | Petrochemical | Actual Output / Time Period | unit/jam | ISO 22400 |
| Data Throughput | Performance | Telco | Actual Data Transferred / Time Period | Mbps | Industry Practice |
| Scrap Ratio | Quality | Petrochemical | Defect Units / Total Units | % | ISO 22400 |
| Packet Loss Rate | Quality | Telco | Lost Packets / Total Packets Sent | % | Industry Practice |
| MTBF | Reliability | Petrochemical | Total Uptime / Number of Failures | jam | ISO 22400 |
| MTTR | Reliability | Petrochemical & Telco | Total Downtime / Number of Incidents | jam/menit | ISO 22400 & TM Forum |
| Flaring Loss | Quality/Efficiency | Petrochemical | Volume Gas Flared / Total Production Volume | % | Domain-specific (perlu riset Faizh lebih lanjut ke laporan Chandra Asri) |

**Catatan:** Baris "Flaring Loss" sengaja ditandai belum ada standar ISO/TM Forum resmi — ini metrik spesifik industri petrokimia yang Faizh perlu validasi dari sumber domain (annual report Chandra Asri atau jurnal petrokimia), sesuai Task B di brief riset.

---

## 5. CARA PAKAI FRAMEWORK INI DI PROPOSAL/DECK

Narasi yang defensible:

> "Struktur `dim_kpi` kami tidak menghafal daftar KPI per industri secara manual, melainkan mengorganisir KPI ke dalam lima arketipe struktural — Availability, Performance, Quality, Reliability, dan Composite Effectiveness. Pendekatan ini terinspirasi dari kesamaan pola yang kami temukan secara independen di dua standar industri: ISO 22400 untuk manufaktur/petrokimia, dan praktik standar TM Forum untuk telekomunikasi. Dengan skema ini, Harvester Agent, mesin deteksi anomali, dan RCA Agent yang sama dapat bekerja lintas domain tanpa perlu logika terpisah per industri — cukup memetakan KPI baru ke salah satu dari lima arketipe yang sudah terdefinisi."

Ini kalimat yang bisa langsung dipakai di BAB II proposal ITASE dan Slide 3 deck CALIBER — konsisten di dua submission, sesuai strategi "satu spine, beda skin" yang udah disepakati.

---
*(End of Document)*

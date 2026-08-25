# PROJECT CONTEXT: OMNIKPI / PLANTINTEL

## 1. ORIGIN & INSPIRATION

Project ini terinspirasi dari KPI WISA Dashboard — dashboard KPI telco yang dibangun selama internship di Infranexia (PT Telkom Infrastruktur Indonesia), yang mengolah 90+ KPI dari 32 file Excel wide-format via ETL pipeline.

**PENTING — batasan data:** OmniKPI/PlantIntel TIDAK menggunakan data, angka, atau struktur internal Infranexia secara langsung. Yang diadopsi hanya konsep umum (dashboard KPI dengan anomaly detection dan RCA), digeneralisasi ke struktur yang berbasis standar industri publik (lihat Section 4). Semua data yang dipakai di demo adalah data sintetis yang di-generate, bukan data operasional riil dari perusahaan manapun.

Tech stack dan arsitektur project ini adalah pivot penuh dari versi awal (Flask + Next.js), atas rekomendasi mentor internship (Bu Metha), menjadi stack yang lebih ringan dan agentic-friendly untuk kebutuhan dual-track competition.

## 2. TECH STACK

- **Frontend:** React (Vite) + TailwindCSS + Recharts. Strict rule: NO Next.js, NO SSR — SPA murni.
- **Backend:** Python + FastAPI.
- **Database:** SQLite via SQLAlchemy, Star Schema.
- **AI/LLM:** Diakses via OpenRouter/NineRouter (atau router sejenis) menggunakan model gratis/free-credit tier, bukan API OpenAI/Claude berbayar langsung — RAG/prompting saja, TIDAK training model dari nol (lihat Section 3, aturan kompetisi). Client kompatibel format OpenAI SDK, tinggal ganti `base_url` dan `api_key` ke endpoint router. Siapkan fallback ke provider berbayar untuk Final Stage CALIBER (hackathon 24 jam, live) kalau free-tier kena rate limit di hari-H.
- **Architecture style:** Monorepo, frontend-backend decoupled via REST API.

## 3. DUAL-TRACK COMPETITION COMPLIANCE

Codebase yang sama menyasar dua kompetisi dengan requirement berbeda. Semua keputusan desain harus valid untuk KEDUANYA secara simultan.

### ITASE 7.0 — AI Innovation Challenge (Telco / SDG 9)
- Diselenggarakan oleh HIMA Sistem Informasi, Telkom University Kampus Purwokerto.
- Wajib pilih 1 dari 3 fokus SDG: SDG 3, SDG 8, atau **SDG 9 (Industry, Innovation and Infrastructure)** — dipilih.
- **Aturan keras:** Peserta TIDAK boleh membangun/melatih model AI dari awal. Wajib pakai model AI yang sudah tersedia (LLM, dll), dengan menjelaskan mekanisme kerja, alasan pemilihan, dan peran AI dalam solusi.
- Kriteria penilaian: Identifikasi Permasalahan (15%), Inovasi Solusi (25%), Pemanfaatan AI (25%), Kelayakan Implementasi (20%), Kontribusi SDGs (15%).
- Deliverable: Proposal (BAB I-V sesuai template resmi) — deadline submit **17-18 Oktober 2026**.
- Final: presentasi 10 menit + tanya jawab 10 menit, online, 5 tim finalis, **7 November 2026**.

### CALIBER 2026 — Chandra Asri (Petrochemical/Manufacturing)
- Wajib pilih 1 dari 2 use case, **Case 2 dipilih: "Manufacturing Intelligence"** (Unified Dashboard, AI Insight, Root Cause Analysis, Follow-up Action Recommendation) — mengatasi data performa manufaktur yang fragmented di banyak dashboard/sistem, sulit monitor plant performance, identify root cause, prioritize alert, track follow-up.
- (Case 1 — Knowledge Hub — TIDAK dipilih, jangan campur narasi ke arah tacit knowledge/knowledge base.)
- **Semua materi submission wajib Bahasa Inggris** — deck, video, mock-up, semuanya.
- Preliminary Stage butuh 3 deliverable, total gabungan **maksimal 10MB**:
  1. Mock-up/prototype (Figma, HTML, atau setara yang bisa dinavigasi panitia).
  2. Video demo 3 menit.
  3. Deck PDF maksimal 7 slide (termasuk cover, tidak termasuk appendix), mengikuti struktur wajib: Cover → Background & Problem Statement → Solution → Business Impact → Feasibility & Roadmap → Conclusion → Team Profile.
- Kriteria penilaian: Problem Understanding & Business Impact, Solution Design & Prototype Quality, Presentation Quality, Feasibility & Roadmap, **Chemical Domain Relevance**.
- Timeline: Registrasi tutup **6 September 2026**, proposal submission **4 Oktober 2026 23:59 WIB**, pengumuman lolos final 23 Oktober 2026.
- **Final Stage BUKAN lanjutan proposal ini** — top 10 tim akan diberi use case BARU yang sama sekali berbeda, dikerjakan dalam 24 jam on-site di Jakarta, presentasi Bahasa Inggris. (Tanggal final: guidebook menyebut dua tanggal berbeda — 28-29 Oktober di satu bagian, 4-5 November di bagian lain — perlu diklarifikasi ke panitia sebelum planning kehadiran.)
- Wajib punya dosen pembimbing terdaftar.
- Penggunaan AI tools untuk proses development diperbolehkan asal outputnya divalidasi — tidak ada larangan eksplisit soal training model custom di guidebook CALIBER (beda dari ITASE), tapi tetap ikuti pendekatan non-training demi konsistensi satu codebase.

## 4. DATA STRUCTURE

### Star Schema
`dim_kpi`, `dim_location`, `dim_period`, `dim_domain`, `fact_kpi`, plus `shift_logs`/`incident_notes` untuk RCA retrieval.

### `dim_domain`
Isolasi tenant antar kompetisi: `1 = telco (ITASE)`, `2 = petrochemical (CALIBER)`. Semua route FastAPI wajib enforce `domain_id` via `Depends()` di level router, bukan manual per-endpoint.

### `dim_kpi` — berbasis 5 arketipe generic (BUKAN framework yang dikarang sendiri)
KPI dikategorikan ke 5 arketipe struktural, disourced dari dua standar independen: **ISO 22400** (manufacturing/petrochemical) dan **TM Forum/praktik industri telco**:
1. **Availability** — Equipment Availability (petrochemical) / Network Availability (telco)
2. **Performance/Throughput** — Throughput Rate / Data Throughput
3. **Quality/Integrity** — Scrap Ratio / Packet Loss Rate
4. **Reliability/Maintenance** — MTBF, MTTR (kedua domain)
5. **Composite/Effectiveness** — OEE (petrochemical only; telco tidak punya padanan formal, ini disclosure yang disengaja, bukan generalisasi dipaksakan)

Kolom `dim_kpi`: `kpi_id`, `kpi_name`, `kpi_archetype`, `domain_id`, `formula_description`, `unit`, `target_threshold`, `higher_is_better`, `source_standard`.

### `dim_location` — Adjacency List, hierarchy-agnostic
`location_id`, `location_name`, `location_type`, `parent_location_id` (self-referencing FK), `domain_id`. Rollup pakai `WITH RECURSIVE` CTE dengan anchor base case di leaf node (`NOT EXISTS` child) — mencegah double-counting di semua level hierarki, baik telco (Nasional-Regional-Witel-District) maupun petrochemical (Plant-Unit-Line). Nama lokasi di seed data pakai nama geografis generik, bukan struktur organisasi internal satu perusahaan spesifik.

### Anomaly Detection
Z-score/IQR terhadap historical window (30 hari, minimum 10 sample point sebelum dianggap valid — di bawah itu return `is_anomaly: false, reason: "insufficient_historical_data"`). Threshold `|Z| > 2.0`. Confidence score di RCA Agent diturunkan dari Z-score aktual, LLM hanya menarasikan — bukan menghasilkan angka sendiri.

### RCA Retrieval
`shift_logs` table dengan SQLite FTS5 + SQL metadata filter (domain_id + location_id + timestamp), bukan vector DB — dijustifikasi karena volume data kecil dan terstruktur.

## 5. TRI-AGENT ARCHITECTURE
1. **Harvester Agent** — ingest Excel, column mapping via rapidfuzz (fuzzy matching lokal), fallback ke LLM kalau confidence < 80%.
2. **ML Heatmap Engine** — render dashboard KPI matrix, highlight anomali berdasarkan Z-score (bukan threshold binary sederhana).
3. **RCA Agent** — LLM menarasikan root cause dari data historis + shift logs yang di-retrieve, output: root cause, confidence score (dari Z-score), prescriptive action — bersifat advisory, human-in-the-loop, TIDAK eksekusi otomatis (Purdue Model / ISA-95 compliance, read-only terhadap OT).

## 6. SEED DATA STATUS
Dua skenario demo (Golden Flow) sudah dirancang: KPI Network Availability drop (telco) dan Equipment Availability/OEE drop (petrochemical), lengkap dengan shift log entries dan expected RCA Agent JSON output. Generator untuk histori 30-hari (buat baseline Z-score) masih perlu dibuat — belum ada di codebase.

# GOLDEN FLOW DEMO CASE STUDIES

Dua skenario konkret — satu per domain — yang mengisi `fact_kpi` dan `shift_logs` dengan data yang bikin RCA Agent bisa nunjukin diagnosis yang koheren, bukan generic. Setiap skenario dirancang supaya Z-score anomaly detection trigger secara natural, dan RCA Agent punya bukti (shift log) yang bisa di-retrieve buat narasi root cause.

---

## SKENARIO 1: TELCO (ITASE) — Network Availability Drop

**KPI:** Network Availability (Arketipe: Availability)
**Lokasi:** District Bandung Timur → Witel Bandung → Regional Jawa Barat (hierarki `dim_location`)
**Threshold:** 99.5% | **Historical mean (30 hari):** 99.6%, std dev 0.15%

| Field | Value |
|---|---|
| `actual_value` | 96.2% |
| `z_score` | ≈ -22.6 (jauh di luar ±2.0, valid anomaly) |
| `status` | RED |

**`shift_logs` seed entries (yang di-retrieve RCA Agent via FTS5):**

1. `[2026-08-20 03:14] Lokasi: District Bandung Timur. Deteksi fiber cut pada jalur backbone segmen Cicaheum-Ujungberung akibat proyek galian kabel PDAM. Tim OSP dikerahkan.`
2. `[2026-08-20 04:02] Lokasi: District Bandung Timur. BTS cluster (12 site) failover ke jalur redundant, namun kapasitas redundant hanya menopang 60% traffic normal.`
3. `[2026-08-19 14:30] Lokasi: District Bandung Timur. Maintenance terjadwal pada core router — tidak berkaitan dengan insiden hari ini, dicatat sebagai baseline.`

**RCA Agent expected output (JSON demo):**
```json
{
  "root_cause": "Fiber cut pada backbone Cicaheum-Ujungberung akibat aktivitas galian pihak ketiga, menyebabkan 12 BTS cluster failover ke jalur redundant berkapasitas terbatas (60%).",
  "confidence_score": 94,
  "confidence_basis": "Z-score -22.6 (30-hari historical window, n=30) + korelasi waktu langsung dengan shift log 03:14",
  "prescriptive_action": "Eskalasi ke tim OSP untuk perbaikan splice fiber; pertimbangkan aktivasi kapasitas redundant tambahan untuk cluster terdampak sambil menunggu perbaikan permanen.",
  "estimated_impact": "≈40% penurunan kapasitas layanan pada 12 BTS, berpotensi customer complaint spike"
}
```

---

## SKENARIO 2: PETROKIMIA (CALIBER) — Equipment Availability / OEE Drop

**KPI:** Equipment Availability (Arketipe: Availability, komponen OEE)
**Lokasi:** Unit Polyethylene Plant B → Plant Cilegon (hierarki `dim_location`)
**Threshold:** 92% | **Historical mean (30 hari):** 91.8%, std dev 1.2%

| Field | Value |
|---|---|
| `actual_value` | 78.4% |
| `z_score` | ≈ -11.2 |
| `status` | RED |

**`shift_logs` seed entries:**

1. `[2026-08-21 09:10] Lokasi: Unit Polyethylene Plant B. Feed pump P-204 trip akibat lonjakan vibrasi di atas ambang batas (8.2 mm/s, threshold 7.0 mm/s). Unit shutdown otomatis via interlock safety.`
2. `[2026-08-21 09:45] Lokasi: Unit Polyethylene Plant B. Tim maintenance konfirmasi indikasi bearing wear pada P-204, terakhir preventive maintenance 145 hari lalu (jadwal standar: 90 hari).`
3. `[2026-08-15 11:00] Lokasi: Unit Polyethylene Plant B. Catatan rutin — tidak ada anomali, dicatat sebagai baseline.`

**RCA Agent expected output (JSON demo):**
```json
{
  "root_cause": "Trip pada feed pump P-204 akibat vibrasi berlebih yang mengindikasikan bearing wear, kemungkinan besar disebabkan oleh preventive maintenance yang terlambat (145 hari vs jadwal standar 90 hari).",
  "confidence_score": 91,
  "confidence_basis": "Z-score -11.2 (30-hari historical window) + korelasi langsung dengan shift log 09:10 dan histori maintenance overdue",
  "prescriptive_action": "Jadwalkan inspeksi/replacement bearing P-204 segera; evaluasi ulang interval preventive maintenance pump-pump kritikal di Unit B untuk mencegah overdue serupa.",
  "estimated_impact": "Unit shutdown penuh, estimasi downtime cost berdasarkan benchmark industri (lihat brief riset Faizh Task A untuk angka bersumber)"
}
```

---

## KENAPA DUA SKENARIO INI "AMAN" DIPAKAI DI DEMO

- Angka (`actual_value`, threshold, z-score) — sintetis, di-generate untuk demo, bukan data operasional riil manapun.
- Nama lokasi (Bandung Timur, Cilegon) — nama geografis generik yang valid dipakai kedua domain, bukan merujuk struktur internal satu perusahaan spesifik.
- Root cause yang dipilih (fiber cut, pump bearing wear) — skenario kegagalan yang umum terjadi dan well-known di masing-masing industri, bukan kasus rahasia/spesifik satu perusahaan.
- `confidence_score` di kedua contoh **diturunkan dari Z-score aktual**, sesuai keputusan arsitektur — bukan angka yang LLM karang sendiri.

## CATATAN IMPLEMENTASI

Dua skenario ini bisa langsung jadi INSERT statement awal buat `fact_kpi` dan `shift_logs` di `database.py`. Kalau Faizh nanti nemu angka downtime cost yang lebih akurat dari Task A riset, tinggal update field `estimated_impact` di skenario 2 — strukturnya udah siap nampung itu.

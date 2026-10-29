"""Synthetic telco demo generator for OmniKPI, ITASE 7.0.

Creates one domain, seven hierarchy nodes, fifteen KPIs, thirty periods,
1,350 readings and three operational logs. The featured incident is a fiber cut
at District Bandung Timur. Running this script replaces the local demo database.
"""

import sys
import os

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError for non-ASCII chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import math
import random
import datetime


# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import (
    init_db, SessionLocal,
    DimDomain, DimKPI, DimLocation, DimPeriod, FactKPI, ShiftLog,
)

random.seed(42)   # Fully reproducible output across runs

# ── Simulation constants ──────────────────────────────────────────────────────
START_DATE    = datetime.date(2026, 7, 27)   # Day 1 of historical window
NUM_DAYS      = 30                           # Day 30 = 2026-08-25 (anomaly injection day)
Z_THRESHOLD   = 2.0                          # |Z| > 2.0 → anomaly (RED)
YELLOW_Z      = 1.5                          # 1.5 < |Z| ≤ 2.0 → YELLOW
MIN_SAMPLES   = 10                           # < 10 data points → suppress anomaly flag


# ── KPI definitions ───────────────────────────────────────────────────────────
# Each row: (kpi_name, archetype, formula_description, unit, target_threshold,
#            higher_is_better, source_standard,
#            sim_mean, sim_std, clip_lo, clip_hi)
# sim_mean / sim_std drive the synthetic normal distribution for seed data generation.

TELCO_KPIS = [
    # ── Availability ──────────────────────────────────────────────────────────
    (
        "Network Availability", "Availability",
        "Actual Uptime / Total Period × 100",
        "%", 99.5, True, "TM Forum/Industry",
        99.6, 0.15, 99.0, 100.0,
    ),
    (
        "BTS Accessibility Rate", "Availability",
        "Successful RRC Setup Attempts / Total RRC Attempts × 100",
        "%", 98.0, True, "TM Forum/Industry",
        98.5, 1.5, 94.0, 100.0,
    ),
    (
        "Core Network Uptime", "Availability",
        "Core Network Uptime / Planned Operation Time × 100",
        "%", 99.9, True, "TM Forum/Industry",
        99.92, 0.03, 99.8, 100.0,
    ),
    # ── Performance ───────────────────────────────────────────────────────────
    (
        "Data Throughput", "Performance",
        "Actual Data Transferred / Time Period",
        "Mbps", 1000.0, True, "Industry Practice",
        850.0, 80.0, 500.0, 1100.0,
    ),
    (
        "Bandwidth Utilization", "Performance",
        "Used Bandwidth / Total Bandwidth Capacity × 100",
        "%", 80.0, False, "Industry Practice",
        65.0, 8.0, 30.0, 95.0,
    ),
    (
        "Handover Success Rate", "Performance",
        "Successful Handovers / Total Handover Attempts × 100",
        "%", 97.0, True, "TM Forum/Industry",
        97.5, 0.4, 95.0, 99.5,
    ),
    (
        "Network Congestion Rate", "Performance",
        "Congested Time Slots / Total Available Slots × 100",
        "%", 5.0, False, "Industry Practice",
        3.5, 1.0, 0.5, 9.0,
    ),
    # ── Quality ───────────────────────────────────────────────────────────────
    (
        "Packet Loss Rate", "Quality",
        "Lost Packets / Total Packets Sent × 100",
        "%", 0.1, False, "Industry Practice",
        0.08, 0.02, 0.01, 0.5,
    ),
    (
        "Call Drop Rate", "Quality",
        "Dropped Calls / Total Established Calls × 100",
        "%", 0.5, False, "TM Forum/Industry",
        0.4, 0.15, 0.05, 2.0,
    ),
    (
        "Latency (RTT)", "Quality",
        "Round-Trip Time average across monitored segments",
        "ms", 50.0, False, "Industry Practice",
        42.0, 5.0, 20.0, 90.0,
    ),
    (
        "Jitter", "Quality",
        "Statistical variation in packet inter-arrival delay",
        "ms", 5.0, False, "Industry Practice",
        4.2, 0.6, 1.0, 12.0,
    ),
    # ── Reliability ───────────────────────────────────────────────────────────
    (
        "MTTR", "Reliability",
        "Total Downtime / Number of Incidents",
        "hours", 4.0, False, "TM Forum/Industry",
        3.5, 0.5, 1.0, 10.0,
    ),
    (
        "MTTD", "Reliability",
        "Time from incident occurrence to detection",
        "minutes", 15.0, False, "Industry Practice",
        12.0, 3.0, 5.0, 30.0,
    ),
    (
        "Service Restoration Time", "Reliability",
        "Time from incident report to full service restoration",
        "minutes", 30.0, False, "TM Forum/Industry",
        25.0, 5.0, 10.0, 60.0,
    ),
    (
        "Fiber Restoration Time", "Reliability",
        "Time from fiber cut detection to splice completion and restoration",
        "hours", 8.0, False, "Industry Practice",
        6.5, 1.2, 2.0, 15.0,
    ),
]

# ── Golden Flow anomaly overrides (Day 30) ────────────────────────────────────
# (location_name, kpi_name): anomalous_actual_value
# Values are chosen to produce Z-scores matching Demo_Case_Studies_OmniKPI.md.
#
# Note: Bandwidth Utilization at Bandung Timur is HIGH anomalous (higher_is_better=False)
#       representing congestion on the redundant path after fiber cut.
ANOMALY_OVERRIDES = {
    # Scenario 1: Fiber cut — District Bandung Timur (Telco)
    ("District Bandung Timur", "Network Availability"):    96.2,    # Z ≈ −22.6
    ("District Bandung Timur", "BTS Accessibility Rate"): 82.0,    # Z ≈ −11.0 (12 BTS impacted)
    ("District Bandung Timur", "Call Drop Rate"):           2.8,    # Z ≈ +16.0 (higher_is_better=F)
    ("District Bandung Timur", "Data Throughput"):        312.0,    # Z ≈ −6.7  (redundant capacity)
    ("District Bandung Timur", "Bandwidth Utilization"):   89.5,    # Z ≈ +3.1  (congestion)
}


# ── Pure utility functions (no DB) ────────────────────────────────────────────

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def gauss_series(mean: float, std: float, n: int, lo: float, hi: float) -> list:
    """Generate n clamped normal-distribution samples."""
    return [clamp(random.gauss(mean, std), lo, hi) for _ in range(n)]


def compute_stats(values: list) -> tuple:
    """Return (mean, std) for a list of floats. std floor: 1e-9."""
    n   = len(values)
    mu  = sum(values) / n
    var = sum((v - mu) ** 2 for v in values) / n
    return mu, math.sqrt(var) or 1e-9


def compute_z(v: float, mu: float, sigma: float) -> float:
    return (v - mu) / sigma if sigma > 1e-9 else 0.0


def status_from_z(z: float, idx: int) -> tuple:
    """
    Return (is_anomaly, anomaly_reason, status_str) for a given Z-score.
    Suppresses anomaly flag for the first MIN_SAMPLES data points.
    """
    abs_z = abs(z)
    if idx < MIN_SAMPLES:
        return False, "insufficient_historical_data", "GREEN"
    if abs_z > Z_THRESHOLD:
        return True, f"Z-score {z:.2f}", "RED"
    if abs_z > YELLOW_Z:
        return False, None, "YELLOW"
    return False, None, "GREEN"


# ── Main seeder ───────────────────────────────────────────────────────────────

def main() -> None:
    # Drop and recreate DB for a clean slate on each run
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "omnikpi.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  [-] Removed existing {db_path}")

    print("[*] Seeding OmniKPI database...\n")
    init_db()
    db = SessionLocal()

    try:
        # ── 1. Domains ────────────────────────────────────────────────────────
        telco = DimDomain(domain_id=1, domain_name="Digital Infrastructure (SDG 9.c)", domain_code="digital_infra")
        db.add(telco)
        db.flush()
        print("  [1/6] Domains ......... 1 (Telecommunications, SDG 9.c)")

        # ── 2. Locations ──────────────────────────────────────────────────────
        # Telco (domain 1): Nasional → Regional Jawa Barat → Witel → Districts
        l_nas   = DimLocation(location_name="Nasional",               location_type="national",  parent_location_id=None,              domain_id=1)
        db.add(l_nas); db.flush()

        l_jabar = DimLocation(location_name="Regional Jawa Barat",    location_type="regional",  parent_location_id=l_nas.location_id, domain_id=1)
        db.add(l_jabar); db.flush()

        l_wbdg  = DimLocation(location_name="Witel Bandung",          location_type="witel",     parent_location_id=l_jabar.location_id, domain_id=1)
        l_wcrb  = DimLocation(location_name="Witel Cirebon",          location_type="witel",     parent_location_id=l_jabar.location_id, domain_id=1)
        db.add_all([l_wbdg, l_wcrb]); db.flush()

        l_bdgt  = DimLocation(location_name="District Bandung Timur", location_type="district",  parent_location_id=l_wbdg.location_id, domain_id=1)  # DEMO
        l_bdgb  = DimLocation(location_name="District Bandung Barat", location_type="district",  parent_location_id=l_wbdg.location_id, domain_id=1)
        l_crbn  = DimLocation(location_name="District Cirebon",       location_type="district",  parent_location_id=l_wcrb.location_id, domain_id=1)
        db.add_all([l_bdgt, l_bdgb, l_crbn]); db.flush()

        telco_leaves = [l_bdgt, l_bdgb, l_crbn]
        print(f"  [2/6] Locations ....... 7 telco hierarchy nodes")

        # ── 3. KPIs ───────────────────────────────────────────────────────────
        def insert_kpis(definitions, domain_id):
            """Insert KPI rows, return list of (DimKPI, sim_mean, sim_std, lo, hi)."""
            result = []
            for row in definitions:
                kpi = DimKPI(
                    kpi_name=row[0], kpi_archetype=row[1], domain_id=domain_id,
                    formula_description=row[2], unit=row[3],
                    target_threshold=row[4], higher_is_better=row[5],
                    source_standard=row[6],
                )
                db.add(kpi)
                result.append((kpi, row[7], row[8], row[9], row[10]))
            db.flush()
            return result

        t_kpis = insert_kpis(TELCO_KPIS, domain_id=1)
        print(f"  [3/6] KPIs ............ {len(t_kpis)} telco")

        # KPI name → kpi_id lookups (used for shift log references)
        t_kpi_id = {kpi.kpi_name: kpi.kpi_id for kpi, *_ in t_kpis}

        # ── 4. Periods ────────────────────────────────────────────────────────
        periods = []
        for i in range(NUM_DAYS):
            d = START_DATE + datetime.timedelta(days=i)
            p = DimPeriod(date=d.isoformat(), shift="Daily", period_label=f"{d.isoformat()} Daily")
            db.add(p)
            periods.append(p)
        db.flush()
        end_date = START_DATE + datetime.timedelta(days=NUM_DAYS - 1)
        print(f"  [4/6] Periods ......... {NUM_DAYS} ({START_DATE} → {end_date})")

        # ── 5. Fact KPI ───────────────────────────────────────────────────────
        fact_count = [0]   # Mutable container for nonlocal counter in nested fn

        def seed_facts(leaves, kpi_tuples, domain_id):
            for loc in leaves:
                for kpi, base_mean, base_std, lo, hi in kpi_tuples:
                    # Apply a small location-level mean offset (±0.5σ), reproducible
                    loc_mean = clamp(base_mean + random.gauss(0, base_std * 0.5), lo, hi)
                    loc_std  = base_std

                    # Override with exact demo parameters for primary demo KPIs
                    # so Z-scores match Demo_Case_Studies_OmniKPI.md specifications.
                    if (loc.location_name == "District Bandung Timur"
                            and kpi.kpi_name == "Network Availability"):
                        loc_mean, loc_std = 99.6, 0.15

                    # 29 normal historical data points
                    normal_vals = gauss_series(loc_mean, loc_std, NUM_DAYS - 1, lo, hi)
                    hist_mu, hist_sigma = compute_stats(normal_vals)

                    # Day 30: inject anomaly if this (location, KPI) is a demo scenario;
                    # otherwise generate another normal value.
                    key     = (loc.location_name, kpi.kpi_name)
                    day_30  = ANOMALY_OVERRIDES.get(
                        key, clamp(random.gauss(loc_mean, loc_std), lo, hi)
                    )
                    all_vals = normal_vals + [day_30]

                    for idx, (period, val) in enumerate(zip(periods, all_vals)):
                        z                        = compute_z(val, hist_mu, hist_sigma)
                        is_anom, reason, st      = status_from_z(z, idx)

                        db.add(FactKPI(
                            kpi_id=kpi.kpi_id,
                            location_id=loc.location_id,
                            period_id=period.period_id,
                            domain_id=domain_id,
                            actual_value=round(val, 4),
                            target_value=kpi.target_threshold,
                            z_score=round(z, 4),
                            is_anomaly=is_anom,
                            anomaly_reason=reason,
                            status=st,
                        ))
                        fact_count[0] += 1

        seed_facts(telco_leaves, t_kpis, domain_id=1)
        db.flush()
        print(f"  [5/6] Fact KPI rows ... {fact_count[0]}")

        # ── 6. Shift Logs ─────────────────────────────────────────────────────
        # Inserted into shift_logs → FTS5 trigger auto-indexes each row.
        logs = [
            # ── Scenario 1: Fiber cut (Telco / District Bandung Timur) ──────
            ShiftLog(
                location_id=l_bdgt.location_id, domain_id=1,
                timestamp="2026-08-20 03:14:00",
                kpi_id=t_kpi_id["Network Availability"],
                log_text=(
                    "Lokasi: District Bandung Timur. Deteksi fiber cut pada jalur backbone "
                    "segmen Cicaheum-Ujungberung akibat proyek galian kabel PDAM. "
                    "Tim OSP dikerahkan."
                ),
            ),
            ShiftLog(
                location_id=l_bdgt.location_id, domain_id=1,
                timestamp="2026-08-20 04:02:00",
                kpi_id=t_kpi_id["Network Availability"],
                log_text=(
                    "Lokasi: District Bandung Timur. BTS cluster (12 site) failover ke "
                    "jalur redundant, namun kapasitas redundant hanya menopang 60% "
                    "traffic normal."
                ),
            ),
            ShiftLog(
                location_id=l_bdgt.location_id, domain_id=1,
                timestamp="2026-08-19 14:30:00",
                kpi_id=None,
                log_text=(
                    "Lokasi: District Bandung Timur. Maintenance terjadwal pada core "
                    "router — tidak berkaitan dengan insiden hari ini, dicatat sebagai "
                    "baseline."
                ),
            ),
        ]
        db.add_all(logs)
        db.flush()
        print(f"  [6/6] Shift logs ...... {len(logs)} (FTS5 auto-indexed via trigger)")

        db.commit()
        print(f"\n[OK] Seeding complete!")
        print(f"   DB path  : {db_path}")
        print(f"   Domains  : 1")
        print(f"   Locations: 7 (telco)")
        print(f"   KPIs     : 15 (telco)")
        print(f"   Facts    : {fact_count[0]}")
        print(f"   Logs     : {len(logs)}")
        print()
        print("   [!] Anomalies injected on Day 30 (2026-08-25):")
        print("       Telco -> District Bandung Timur   (5 RED KPIs, fiber cut)")

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

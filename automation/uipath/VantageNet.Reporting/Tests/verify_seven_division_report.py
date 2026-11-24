"""Reconcile a robot aggregate and final PowerPoint against the independent XLSX."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from openpyxl import load_workbook


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def reference_rows(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        values = iter(wb["Expected readings"].values)
        assert next(values) == ("Submitting unit", "KPI", "Location", "Reporting date", "Unit", "Direction",
                                "Actual", "Target", "Achievement %", "Expected status", "Source file", "Source row")
        return list(values)
    finally:
        wb.close()


def equivalent(expected, actual):
    if isinstance(expected, (int, float)) and not isinstance(expected, bool) and isinstance(actual, (int, float)):
        return math.isclose(expected, actual, abs_tol=1e-9)
    return expected == actual


def verify(output, reference, *, check_pptx=True):
    bundle_path = output / "aggregate-bundle.json"
    bundle = load(bundle_path)
    expected = reference_rows(reference)
    readings = bundle["readings"]
    actual = {(r["division"], r["kpi_name"], r["location_name"], r["date"]): r for r in readings}
    assert len(actual) == len(readings) == len(expected) == 180
    assert len({r["fact_id"] for r in readings}) == 180
    status = {"Meeting target": "GREEN", "Below target": "RED", "GREEN": "GREEN", "RED": "RED"}
    source = {s["submission_id"]: s for s in bundle["submissions"]}
    counts = Counter()
    for division, kpi, location, day, unit, direction, value, target, attainment, label, filename, row in expected:
        r = actual[division, kpi, location, day]
        pairs = {"unit": unit, "higher_is_better": direction == "Higher better", "actual_value": value,
                 "target_value": target, "attainment_pct": attainment, "status": status[label],
                 "source_file": filename, "source_row": row}
        for field, expected_value in pairs.items():
            assert equivalent(expected_value, r[field]), (division, kpi, location, field, expected_value, r[field])
        sid = r["submission_id"]
        assert (source[sid]["division"], source[sid]["filename"], source[sid]["report_date"]) == (division, filename, day)
        counts[sid] += 1
    assert len(counts) == 7 and all(counts[sid] == s["row_count"] for sid, s in source.items())
    assert Counter(r["status"] for r in readings) == {"GREEN": 121, "RED": 59}
    assert len({r["kpi_id"] for r in readings}) == 90
    assert len({r["location_id"] for r in readings}) == 2
    assert {g["fact_id"] for g in bundle["gaps"]} == {r["fact_id"] for r in readings if r["status"] == "RED"}
    receipt = None
    if check_pptx:
        receipt = load(output / "report" / "generation-receipt.json")
        pptx = output / "report" / receipt["filename"]
        assert hashlib.sha256(pptx.read_bytes()).hexdigest() == receipt["pptx_sha256"]
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        with ZipFile(pptx) as archive:
            slides = ["\n".join(el.text or "" for el in ET.fromstring(archive.read(f"ppt/slides/slide{i}.xml")).findall(".//a:t", ns))
                      for i in range(1, 8)]
        assert all(value in slides[0] for value in ("121 of 180", "90 KPIs", "7 divisions", "2 locations", "59 readings"))
        assert all(value in slides[2] for value in ("121", "59", "Demo North", "Demo South"))
        assert all(s["filename"] in slides[6] and sid in slides[6] for sid, s in source.items())
        if bundle["narrative"]["evidence_status"] == "ai_draft":
            assert bundle["narrative"]["root_cause"] in slides[4]
            assert bundle["narrative"]["prescriptive_action"] in slides[5]
    return {"reference": reference.name, "workbook_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
            "bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(), "submissions": counts,
            "totals": bundle["totals"], "evidence_status": bundle["narrative"]["evidence_status"], "receipt": receipt}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.output, args.reference), indent=2))

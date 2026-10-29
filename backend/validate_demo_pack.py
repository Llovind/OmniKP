"""Independent reference: parse exported fixture cells without importing app services."""
import hashlib
import json
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
pack = ROOT/'frontend/public/demo/divisions'
manifest = json.loads((pack/'manifest.json').read_text())
reference = []
checksums = {}
for entry in manifest:
    path = pack/entry['filename']
    checksums[entry['filename']] = hashlib.sha256(path.read_bytes()).hexdigest()
    book = load_workbook(path, data_only=True, read_only=True)
    for source_row, values in enumerate(book['Report'].iter_rows(min_row=5, values_only=True), 5):
        name, unit, direction, target = values[:4]
        if not name:
            continue
        higher = direction == 'HIGHER BETTER'
        pairs = [('Demo North', values[4]), ('Demo South', values[6])] if entry['layout'] == 'Location columns' else [(values[4], values[5])]
        for location, actual in pairs:
            met = actual >= target if higher else actual <= target
            denominator = target if higher else actual
            achievement = ((actual if higher else target) / denominator * 100) if denominator else (100 if actual == target else None)
            reference.append(dict(division=entry['division'], kpi_name=name, location_name=location, date=entry['report_date'], unit=unit, higher_is_better=higher, actual_value=actual, target_value=target, status='GREEN' if met else 'RED', attainment_pct=None if achievement is None else round(achievement,2), source_file=entry['filename'], source_row=source_row))
    book.close()
assert len(reference) == 180
assert len({(r['kpi_name'], r['location_name'], r['date']) for r in reference}) == 180
expected = json.loads((ROOT/'backend/evidence/division-demo/expected.json').read_text())
for original, actual in zip(expected, reference):
    assert all(actual[k] == v for k,v in original.items()), (original,actual)
summary = {e['division']: {'kpis':e['kpis'], 'readings':e['readings'], 'meeting':sum(r['status']=='GREEN' for r in reference if r['division']==e['division']), 'missing':sum(r['status']=='RED' for r in reference if r['division']==e['division'])} for e in manifest}
(pack/'expected-readings.json').write_text(json.dumps(reference,indent=2),encoding='utf-8')
(pack/'validation-summary.json').write_text(json.dumps({'synthetic':True,'date':'2026-06-30','readings':180,'kpis':90,'units':summary,'sha256':checksums},indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))

"""Extract only KPI ownership/definitions; never copy operational readings or targets."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
groups = json.loads((ROOT/'backend/evidence/division-demo/ownership.json').read_text(encoding='utf-8'))
assert sum(map(len, groups.values())) == 90
out = ROOT / 'frontend/public/demo/divisions'
out.mkdir(parents=True, exist_ok=True)
manifest = []
expected = []
for index, (division, definitions) in enumerate(groups.items()):
    slug = division.lower().replace(' & ', '-').replace(' ', '-')
    wide = index % 2 == 1
    columns = (['KPI WISA', 'SATUAN', 'FORMULA', 'TGT', 'Demo North | REAL', 'Demo North | ACH', 'Demo South | REAL', 'Demo South | ACH'] if wide else
               ['KPI WISA', 'SATUAN', 'FORMULA', 'TGT', 'Lokasi', 'Realisasi', 'Keterangan'])
    rows = []
    for n, definition in enumerate(definitions):
        unit, higher = definition['unit'], definition['higher']
        target = {'%': ([98.5, 99.2, 96, 92, 95][n % 5] if higher else [2.5, 3, 4][n % 3]), 'Jam': [4, 6, 8, 12][n % 4], 'Port': [1200, 850, 600][n % 3], 'Site': n % 3, 'Gangguan': 2 + n % 3}[unit]
        base = [definition['name'], unit, 'HIGHER BETTER' if higher else 'LOWER BETTER', target]
        values = []
        for loc_index, location in enumerate(['Demo North', 'Demo South']):
            miss = (n + loc_index) % 3 == 0
            if unit == '%':
                gap = [0.7, 1.3, 2.1, 0.4][(n + loc_index) % 4]
                actual = round(max(0, min(100, target + (gap if miss != higher else -gap))), 2)
            elif unit == 'Port':
                actual = int(target * (0.91 if miss else 1.04))
            elif unit == 'Jam':
                actual = round(target * (1.25 if miss else 0.8), 2)
            else:
                actual = target + 1 if miss else max(0, target - 1)
            values.append(actual)
            explanations = {
                'ED': 'SYNTHETIC DEMO: deployment completion was delayed by a rescheduled site access window. Proposed action: confirm the revised access schedule.',
                'NETOP OSP': 'SYNTHETIC DEMO: the field team reports repeated cable repair visits. Proposed action: inspect the affected synthetic route and verify repair records.',
                'FBB': 'SYNTHETIC DEMO: provisioning orders waited for installation slots. Proposed action: review the pending-order queue.',
                'DEFA': 'SYNTHETIC DEMO: a scheduled infrastructure maintenance window reduced availability. Proposed action: verify the maintenance duration.'}
            feedback = explanations.get(division, '') if miss and not wide and n % 2 == 0 else ''
            expected.append(dict(division=division, kpi_name=definition['name'], location_name=location, actual_value=actual, target_value=target, unit=unit, higher_is_better=higher, date='2026-06-30'))
            if not wide:
                rows.append(base + [location, actual, feedback])
        if wide:
            rows.append(base + [values[0], None, values[1], None])
    manifest.append(dict(division=division, kpis=len(definitions), readings=2*len(definitions), filename=slug+'.xlsx', sheet='Report', header_row=4, header_depth=1, report_date='2026-06-30', layout='Location columns' if wide else 'Rows per location', columns=columns, rows=rows, definitions=definitions))
(out/'manifest.json').write_text(json.dumps([{k:v for k,v in entry.items() if k not in ('rows','columns','definitions')} for entry in manifest], indent=2), encoding='utf-8')
evidence = ROOT / 'backend/evidence/division-demo'
evidence.mkdir(parents=True, exist_ok=True)
(evidence/'build-data.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(evidence/'expected.json').write_text(json.dumps(expected, indent=2), encoding='utf-8')
(evidence/'ownership.json').write_text(json.dumps({k:v for k,v in groups.items()}, indent=2), encoding='utf-8')
print('Seven groups, 90 KPIs, 180 synthetic readings. No operational values copied.')

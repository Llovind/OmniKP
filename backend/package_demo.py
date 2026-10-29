"""Package only explicitly listed synthetic fixtures and references."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
directory = Path(__file__).resolve().parents[1]/'frontend/public/demo/divisions'
manifest = json.loads((directory/'manifest.json').read_text())
names = [e['filename'] for e in manifest] + ['manifest.json','expected-consolidated.xlsx','expected-readings.json','validation-summary.json','VALIDATE.md','missing-value.xlsx','duplicate-reading.xlsx','changed-headers.xlsx']
with ZipFile(directory/'validation-pack.zip','w',ZIP_DEFLATED) as archive:
    for name in names:
        archive.write(directory/name,name)
print(f'Packaged {len(names)} approved files.')

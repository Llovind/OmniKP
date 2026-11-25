"""Compare a manual Excel consolidation with the read-only synthetic reference."""
import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import sys

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "frontend/public/demo/divisions/expected-consolidated.xlsx"
ALIASES = {
    "division": ("submitting unit", "division", "divisi"),
    "kpi": ("kpi", "nama kpi"),
    "date": ("reporting date", "tanggal laporan", "tanggal"),
    "location": ("location", "lokasi"),
    "actual": ("actual", "realisasi", "nilai", "nilai aktual"),
    "target": ("target",),
    "file": ("source file", "berkas sumber", "file sumber"),
    "row": ("source row", "baris sumber"),
    "unit": ("unit", "satuan"),
}
KEY = ("division", "kpi", "date")
SCORED = {"actual": "nilai salah", "target": "target salah", "location": "lokasi salah"}
REQUIRED = set(KEY) | SCORED.keys()


@dataclass
class Reading:
    excel_row: int
    values: dict
    cells: dict
    formats: dict

    @property
    def provenance(self):
        name, row = self.values.get("file"), self.values.get("row")
        return (str(name).strip(), str(row).strip()) if name is not None and row is not None else None


def clean(value):
    return value.strip() if isinstance(value, str) else value


def day(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value).strip()).isoformat()


def columns(headers):
    result = {}
    for index, value in enumerate(headers):
        name = value.strip().casefold() if isinstance(value, str) else ""
        for key, aliases in ALIASES.items():
            if name in aliases:
                if key in result:
                    raise ValueError(f"Header ganda untuk {key}: {value}")
                result[key] = index
    return result


def load(path, sheet_name, division):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name:
            sheets = [book[sheet_name]]
        elif "Expected readings" in book.sheetnames:
            sheets = [book["Expected readings"]]
        else:
            sheets = [sheet for sheet in book if sheet.sheet_state == "visible"]
        candidates = []
        for sheet in sheets:
            header = next(sheet.iter_rows(max_row=1, values_only=True), ())
            fields = columns(header)
            if REQUIRED <= fields.keys():
                candidates.append((sheet, fields))
        if len(candidates) != 1:
            raise ValueError(
                "Pilih satu sheet dengan --sheet. Baris 1 harus punya Submitting unit, KPI, "
                "Reporting date, Location, Actual, Target (alias Indonesia didukung)."
            )
        sheet, fields = candidates[0]
        readings = defaultdict(list)
        for index, row in enumerate(sheet.iter_rows(min_row=2, max_col=max(fields.values()) + 1), 2):
            values = {key: clean(row[col].value) for key, col in fields.items()}
            if all(value is None or value == "" for value in values.values()):
                continue
            if any(values[field] in (None, "") for field in KEY):
                raise ValueError(f"Identitas reading kosong pada {sheet.title}!{index} (unit, KPI, tanggal).")
            if division and str(values["division"]).casefold() != division.casefold():
                continue
            values["division"] = str(values["division"]).casefold()
            values["kpi"] = str(values["kpi"])
            try:
                values["date"] = day(values["date"])
            except ValueError as error:
                raise ValueError(f"Tanggal perlu YYYY-MM-DD atau tanggal Excel pada {sheet.title}!{index}.") from error
            readings[tuple(values[k] for k in KEY)].append(Reading(index, values, {
                key: f"{sheet.title}!{get_column_letter(col + 1)}{index}" for key, col in fields.items()
            }, {key: getattr(row[col], "number_format", "") or "" for key, col in fields.items()}))
        return sheet.title, readings
    finally:
        book.close()


def numeric(value, cell_format="", unit=None):
    if value is None or isinstance(value, bool):
        return None
    string = str(value).strip().removesuffix("%").strip().replace(",", ".")
    try:
        number = Decimal(string)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if not isinstance(value, str) and unit == "%" and "%" in cell_format:
        number *= 100
    return number


def same(expected, observed, field):
    if field == "location":
        return expected.values[field] == observed.values[field]
    unit = expected.values.get("unit")
    value = numeric(observed.values[field], observed.formats[field], unit)
    return value is not None and value == numeric(expected.values[field], expected.formats[field], unit)


def pair(expected, observed):
    missing, extras = expected.copy(), observed.copy()
    pairs = []

    def resolve(candidates):
        for ref in missing.copy():
            possible = [row for row in extras if candidates(ref, row)]
            if len(possible) == 1 and sum(candidates(other, possible[0]) for other in missing) == 1:
                row = possible[0]
                pairs.append((ref, row))
                missing.remove(ref)
                extras.remove(row)

    resolve(lambda a, b: a.provenance is not None and a.provenance == b.provenance)
    resolve(lambda a, b: a.values["location"] not in (None, "") and a.values["location"] == b.values["location"])
    resolve(lambda a, b: same(a, b, "actual") and same(a, b, "target"))
    if len(missing) == len(extras) == 1:
        pairs.append((missing.pop(), extras.pop()))
    return pairs, missing, extras


def score(expected, observed):
    errors, unexpected, ambiguous = [], [], []
    for key in sorted(expected.keys() | observed.keys()):
        pairs, missing, extras = pair(expected.get(key, []), observed.get(key, []))
        if missing and extras:
            ambiguous.append(dict(key=key, expected_rows=[row.excel_row for row in missing],
                                  manual_rows=[row.excel_row for row in extras]))
            missing, extras = [], []
        pairs.extend((row, None) for row in missing)
        for ref, row in pairs:
            for field, category in SCORED.items():
                value = row.values[field] if row else None
                if value in (None, ""):
                    category = "hilang"
                elif same(ref, row, field):
                    continue
                errors.append(dict(kategori=category, field=field, expected_cell=ref.cells[field],
                    expected_value=ref.values[field], manual_cell=row.cells[field] if row else None,
                    manual_value=value))
        unexpected.extend(dict(key=key, manual_row=row.excel_row, cells=row.cells) for row in extras)
    return errors, unexpected, ambiguous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--sheet", help="Nama sheet konsolidasi manual.")
    parser.add_argument("--division", help="Batasi kedua workbook ke satu divisi, misalnya ED.")
    args = parser.parse_args()
    try:
        reference_sheet, refs = load(REFERENCE, "Expected readings", args.division)
        manual_sheet, readings = load(args.workbook, args.sheet, args.division)
        if not refs:
            raise ValueError("Tidak ada reading referensi untuk lingkup divisi yang diberikan.")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"{error}\n")
    errors, extras, unclear = score(refs, readings)
    counts = {name: sum(error["kategori"] == name for error in errors)
              for name in ("hilang", "nilai salah", "target salah", "lokasi salah")}
    print(json.dumps(dict(
        command=[sys.executable, *sys.argv], timestamp_utc=datetime.now(timezone.utc).isoformat(),
        status="TIDAK TERUKUR" if unclear else "TERUKUR",
        scope=args.division or "semua divisi pada referensi sintetis",
        expected_path=str(REFERENCE), expected_sha256=sha256(REFERENCE.read_bytes()).hexdigest(),
        expected_sheet=reference_sheet, manual_path=str(args.workbook.resolve()),
        manual_sha256=sha256(args.workbook.read_bytes()).hexdigest(), manual_sheet=manual_sheet,
        expected_readings=sum(map(len, refs.values())), manual_readings=sum(map(len, readings.values())),
        jumlah_sel_salah=None if unclear else len(errors),
        per_kategori=None if unclear else counts, daftar_sel=errors,
        baris_tambahan=extras, pairing_ambigu=unclear,
    ), ensure_ascii=False, indent=2, default=str))
    return 2 if unclear else int(bool(errors or extras))


if __name__ == "__main__":
    sys.exit(main())

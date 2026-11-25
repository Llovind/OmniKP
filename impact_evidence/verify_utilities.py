"""Verify analysis utilities on temporary synthetic inputs, never manual timings."""
from collections import Counter
from hashlib import sha256
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

from openpyxl import load_workbook

from run_checks import capture, now, RAW, ROBOT, ROOT
from score_manual import REFERENCE, load, score


def main():
    start = now()
    original_hash = sha256(REFERENCE.read_bytes()).hexdigest()
    sheet_name, refs = load(REFERENCE, "Expected readings", None)
    with TemporaryDirectory(prefix="verify-impact-", dir=RAW) as temp:
        directory = Path(temp)
        manual_path = directory / "synthetic-manual.xlsx"
        book = load_workbook(REFERENCE)
        sheet = book[sheet_name]
        sheet["G2"] = float(sheet["G2"].value) + 1
        sheet["H3"] = float(sheet["H3"].value) + 1
        sheet["C4"] = "Sintetis lokasi keliru"
        sheet["G5"] = None
        book.save(manual_path)
        book.close()
        _, rows = load(manual_path, None, None)
        errors, unexpected, ambiguous = score(refs, rows)
        assert not unexpected and not ambiguous
        assert len(errors) == 4 and set(Counter(row["kategori"] for row in errors).values()) == {1}
        assert {row["manual_cell"] for row in errors} == {
            f"{sheet_name}!G2", f"{sheet_name}!H3", f"{sheet_name}!C4", f"{sheet_name}!G5"
        }
        complete = subprocess.run([sys.executable, "impact_evidence/score_manual.py", str(REFERENCE)],
                                  cwd=ROOT, capture_output=True, check=True, encoding="utf-8")
        import json
        assert json.loads(complete.stdout)["jumlah_sel_salah"] == 0

        # Functional test values remain in memory, separate from impact measurements.
        cli = [sys.executable, "impact_evidence/cost_model.py"]
        cost = subprocess.run([*cli, "--jam_manual", "1", "--jam_gerbang", "0",
            "--tarif_per_jam", "3", "--biaya_llm_per_siklus", "0",
            "--biaya_tetap_per_bulan", "1", "--siklus_per_bulan", "1",
            "--sensitivitas", "jam_manual", "0", "1", "0.5"],
            cwd=ROOT, capture_output=True, check=True, encoding="utf-8")
        assert "1/3 (eksak)" in cost.stdout and "tidak tercapai" in cost.stdout
        missing = subprocess.run(cli, cwd=ROOT, capture_output=True)
        assert missing.returncode == 2

        robot = directory / ROBOT
        (robot / "Tests").mkdir(parents=True)
        for name in ("test_narrative_pptx.py", "cli_support.py"):
            (robot / "Tests" / name).write_bytes((ROOT / ROBOT / "Tests" / name).read_bytes())
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(str(path) for path in
            (ROOT / "output/deck-style/deps", ROOT / ".local/pitch-python"))
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["UIPATH_CLI_DISABLE_AUTOINSTALL"] = "true"
        env["UIPATH_CLI_DISABLE_VERSION_SYNC"] = "true"
        capture("test_narrative_pptx_retry",
                [sys.executable, str(ROBOT / "Tests/test_narrative_pptx.py")],
                directory, env, [
                    (ROBOT / "Tests/test_narrative_pptx.py").as_posix(),
                    "output/deck-style/deps", ".local/pitch-python"
                ])
    assert sha256(REFERENCE.read_bytes()).hexdigest() == original_hash
    print("command:", sys.executable, "impact_evidence/verify_utilities.py")
    print("start_utc:", start, "end_utc:", now())
    print("source:", REFERENCE.relative_to(ROOT), "sha256:", original_hash)
    print("OK score_manual.py: identical input, four error categories and cell addresses")
    print("OK cost_model.py: required inputs, exact fractional breakeven, sensitivity and nonpositive saving")
    print("No manual baseline was measured by these checks.")


if __name__ == "__main__":
    main()

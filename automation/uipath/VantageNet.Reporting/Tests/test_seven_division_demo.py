"""Opt-in end-to-end acceptance against the installed UiPath CLI and a fresh live backend."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from cli_support import CLI
from verify_seven_division_report import load, verify


PROJECT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT.parents[2] / "frontend" / "public" / "demo" / "divisions"
EXPECTED_MAPPING = dict(zip(
    ("KPI WISA", "SATUAN", "FORMULA", "TGT", "Lokasi", "Realisasi", "Keterangan",
     "Demo North | REAL", "Demo North | ACH", "Demo South | REAL", "Demo South | ACH",
     "KPI", "Unit", "Direction", "Target", "Location", "Actual"),
    ("kpi_name", "unit", "higher_is_better", "target_value", "location_name", "actual_value", "notes",
     "location:Demo North", "ignore", "location:Demo South", "ignore",
     "kpi_name", "unit", "higher_is_better", "target_value", "location_name", "actual_value"),
))


class Acceptance:
    def __init__(self, config_path, report_only=False):
        self.config_path = config_path
        self.config = load(config_path)
        assert self.config["decision_mode"] == "automated-test"
        self.work = Path(self.config["work_root"])
        self.input = Path(self.config["input_root"])
        assert self.input.parent == self.work and self.input.name == "Input"
        self.logs = self.work / "Logs" / self.config["run_id"]
        self.output = self.work / "Output" / self.config["run_id"] / self.config["bundle_id"] / self.config["revision"]
        suffix = f"-{self.config['revision']}" if report_only else ""
        self.evidence = self.work / f"acceptance{suffix}"
        self.evidence.mkdir()
        self.events = []
        self.profile = "vantagenet-local-noauth"
        assert self.get("/_development/instance")["instance_id"] == self.config["expected_instance_id"]
        assert self.get("/api/v1/ai/status")["mode"] == "live"
        if report_only:
            assert len(self.get("/api/v1/domains/1/submissions")) == 7
        else:
            assert self.get("/api/v1/domains/1/submissions") == []
            assert self.get("/api/v1/domains/1/periods?dataset=all") == []

    def get(self, path):
        with urlopen(self.config["backend_origin"] + path, timeout=15) as response:
            return json.load(response)

    def robot(self, workflow="RunSevenDivisionDemo.cs", decision=None, fail=False, extra=None):
        params = dict(projectFolder=str(PROJECT), configPath=str(self.config_path)) if extra is None else extra
        if decision is not None:
            params["decisionPath"] = str(decision)
        argv = [CLI, "rpa", "run", "--file-path", workflow, "--project-dir", str(PROJECT),
                "--profile", self.profile, "--skip-build", "--output", "json"]
        for key, value in params.items():
            argv.extend(["--input-arguments", f"{key}={value}"])
        seq = len(self.events) + 1
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=210,
                                env={**os.environ, "UIPATH_CLI_DISABLE_AUTOINSTALL": "true", "UIPATH_CLI_DISABLE_VERSION_SYNC": "true"})
        (self.evidence / f"{seq:02d}-robot.txt").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        self.events.append({"workflow": workflow, "exit_code": result.returncode})
        (self.evidence / "steps.json").write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        assert (result.returncode != 0) == fail, (result.returncode, result.stdout, result.stderr)
        if workflow == "RunSevenDivisionDemo.cs" and not fail:
            manifest = load(self.logs / "run-manifest.json")
            return Path(manifest["pending_review"]) if manifest["pending_review"] else self.output / "narrative-review.html"

    def form(self, form):
        return json.loads(re.search(r"const data=(\{.*?\});\s*const", form.read_text(encoding="utf-8"), re.S)[1])

    def decision(self, data, action="approve", authorize=False, stale=False):
        request = data["request"]
        kind = request["kind"]
        body = {"request_sha256": "0" * 64 if stale else data["request_sha256"], "decision": action,
                "decision_mode": "automated-test", "reviewer": "AUTOMATED ACCEPTANCE TEST",
                "reason": "Scripted test decision for synthetic fixtures.", "authorize_confirm": authorize,
                "decided_at": datetime.now(timezone.utc).isoformat()}
        if kind == "mapping" and action == "approve":
            body["mapping"] = {col: EXPECTED_MAPPING.get(col, "ignore") for col in data["preview"]["columns"]}
            body["default_direction"] = None
            self.events[-1]["corrected_proposals"] = [col for col, field in body["mapping"].items()
                                                     if data["preview"]["column_mapping"][col]["target"] != field]
        path = self.evidence / f"{len(self.events):02d}-decision-{kind}-{action}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(body, stream, indent=2)
        return path

    def success(self, render):
        form = self.robot()
        submissions = []
        for index in range(7):
            data = self.form(form)
            assert data["request"]["kind"] == "mapping" and data["preview"]["ai_trace"]["mode"] == "live"
            sid = data["preview"]["submission_id"]
            form = self.robot(decision=self.decision(data))
            data = self.form(form)
            assert data["request"]["kind"] == "import" and data["validation"]["can_confirm"]
            if index == 0:
                self.robot(decision=self.decision(data), fail=True)
                assert self.get(f"/api/v1/domains/1/submissions/{sid}")["status"] == "draft"
            form = self.robot(decision=self.decision(data, authorize=True))
            ledger = self.get(f"/api/v1/domains/1/submissions/{sid}")
            assert ledger["status"] == "confirmed" and ledger["row_count"] == len(ledger["readings"])
            submissions.append(sid)
            if index == 0:
                # Route resume through persisted intent + ledger with a simulated lost local response.
                first = next((self.logs / "ED").iterdir())
                (first / "confirm-response.json").rename(self.evidence / "simulated-lost-confirm-response.json")
                assert self.robot() == form
                assert len(self.get("/api/v1/domains/1/submissions")) == 1
        bundle = load(self.output / "aggregate-bundle.json")
        assert bundle["narrative"]["evidence_status"] != "provider_unavailable", bundle["narrative"]
        assert len(self.get("/api/v1/domains/1/submissions")) == 7
        verify(self.output, FIXTURES / "expected-consolidated.xlsx", check_pptx=False)
        assert self.form(form)["request"]["kind"] == "narrative"
        self.robot("GenerateSevenDivisionPptx.cs", fail=True)
        data = self.form(form)
        self.robot(decision=self.decision(data, stale=True), fail=True)
        self.robot(decision=self.decision(data))
        self.robot("GenerateSevenDivisionPptx.cs")
        result = verify(self.output, FIXTURES / "expected-consolidated.xlsx")
        self.robot("GenerateSevenDivisionPptx.cs")
        assert result == verify(self.output, FIXTURES / "expected-consolidated.xlsx")
        assert {s["submission_id"] for s in self.get("/api/v1/domains/1/submissions")} == set(submissions)
        if render:
            self.render(result)
        return result

    def render(self, result):
        path = self.output / "report" / result["receipt"]["filename"]
        pdf = self.output / "report" / "report-proof.pdf"
        self.robot("RenderReportProof.cs", extra={"pptxPath": str(path), "pdfPath": str(pdf)})
        result["pdf_sha256"] = hashlib.sha256(pdf.read_bytes()).hexdigest()

    def report_revision(self, action, render):
        prior = self.get("/api/v1/domains/1/submissions")
        data = self.form(self.robot())
        assert data["request"]["kind"] == "narrative"
        self.robot(decision=self.decision(data, action=action))
        if action == "reject":
            self.robot("GenerateSevenDivisionPptx.cs", fail=True)
            assert not (self.output / "report").exists()
            result = {"narrative_decision": "reject", "pptx_generated": False, "unchanged_submissions": len(prior)}
        else:
            self.robot("GenerateSevenDivisionPptx.cs")
            result = verify(self.output, FIXTURES / "expected-consolidated.xlsx")
            if render:
                self.render(result)
        assert self.get("/api/v1/domains/1/submissions") == prior
        return result

    def failures(self):
        # An alternate manifest admits invalid test fixtures through the real backend.
        manifest_path = Path(self.config["division_manifest"])
        assert manifest_path.parent == self.work, "Use a disposable copy of manifest.json for failure tests."
        manifest = load(manifest_path)
        for entry in manifest:
            (self.input / Path(entry["filename"]).stem.upper() / entry["filename"]).rename(self.evidence / entry["filename"])
        manifest[0].update(filename="missing-value.xlsx", folder="ED", header_row=1)
        manifest[1].update(filename="duplicate-reading.xlsx", folder="BGES-OLO", header_row=1)
        manifest[2].update(folder="MISSING-NETOP-OSP")
        for (folder, filename) in [("ED", "missing-value.xlsx"), ("BGES-OLO", "duplicate-reading.xlsx")]:
            shutil.copyfile(FIXTURES / filename, self.input / folder / filename)
        (self.input / "FBB" / "fbb.xlsx").write_bytes(b"invalid XLSX for negative acceptance")
        shutil.copyfile(self.evidence / "ed.xlsx", self.input / "MBB" / "mbb.xlsx")
        shutil.copyfile(self.evidence / "ed.xlsx", self.input / "DEFA" / "defa.xlsx")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        form = self.robot()
        for division in ("ED", "BGES & OLO"):
            data = self.form(form)
            assert data["preview"]["division"] == division
            form = self.robot(decision=self.decision(data))
            data = self.form(form)
            assert data["request"]["kind"] == "mapping" and data["validation"]["can_confirm"] is False
            assert len(data["validation"]["issues"]) > 0
            form = self.robot(decision=self.decision(data, action="reject"))
        third = self.form(form)
        assert third["preview"]["division"] == "MBB"
        self.robot(decision=self.decision(third, action="reject"))
        statuses = load(self.logs / "run-manifest.json")["divisions"]
        assert statuses == {"ED": "rejected", "BGES & OLO": "rejected", "NETOP OSP": "division_folder_missing",
                            "AIM": "expected_workbook_missing", "FBB": "preview_http_422", "MBB": "rejected",
                            "DEFA": "duplicate_workbook_bytes"}, statuses
        self.robot(decision=self.decision(third), fail=True)
        assert self.get("/api/v1/domains/1/submissions") == []
        assert self.get("/api/v1/domains/1/periods?dataset=all") == []
        assert not self.output.exists()
        return {"division_status": statuses, "confirmed_submissions": 0, "readings": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    scenario = parser.add_mutually_exclusive_group()
    scenario.add_argument("--failures", action="store_true")
    scenario.add_argument("--report-revision", choices=("approve", "reject"))
    parser.add_argument("--render", action="store_true")
    options = parser.parse_args()
    run = Acceptance(options.config.resolve(), report_only=bool(options.report_revision))
    if options.report_revision:
        result = run.report_revision(options.report_revision, options.render)
    else:
        result = run.failures() if options.failures else run.success(options.render)
    (run.evidence / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

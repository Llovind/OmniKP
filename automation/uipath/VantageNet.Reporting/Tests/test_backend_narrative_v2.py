"""Native Phase 1C regression. All archive contents and decisions are fabricated test data."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid

import pypdfium2 as pdfium
from pptx import Presentation

from cli_support import CLI
from test_backend_bundle_v2 import fixture, seal

PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "Output"
REVIEW = "ReviewBackendNarrativeV2.cs"
GENERATE = "GenerateBackendNarrativePptxV2.cs"
EDIT = "Offline test edit: inspect the link [F11].\nDocument findings before changing routing."
ENV = {**os.environ, "UIPATH_CLI_DISABLE_AUTOINSTALL": "true", "UIPATH_CLI_DISABLE_VERSION_SYNC": "true"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def snapshot_case(bundle_id, revision, status="draft_ready", chart=True):
    bundle, _, _, selection = fixture(status, revision)
    bundle["bundle_id"] = bundle_id
    scope = bundle["snapshot"]
    scope["run_id"] = bundle_id + "-" + revision
    row = scope["reading"]
    row.update(actual_value=90.25, target_value=99.0 if chart else None,
               chart_supported=chart, kpi_name="Uplink availability", location_name="North",
               source_file="ed.xlsx")
    if not chart:
        row.update(status="Target unavailable", status_code="YELLOW", attainment_pct=None)
    if status == "draft_ready":
        n = scope["narrative"]
        n["cited_feedback_ids"] = n["grounding"]["cited_feedback_ids"] = ["2", "11"]
        n["references"] = [
            {"id": "F2", "feedback_id": "2", "origin": "fixture-worksheet-notes", "text": "Worksheet reported a link event."},
            {"id": "F11", "feedback_id": "11", "origin": "operator-api", "text": "Operator observed packet loss. Proposed action: Inspect the link."},
        ]
        feedback = scope["feedback"]
        feedback["records"][0]["explanation"] = "Worksheet reported a link event."
        feedback["records"][1]["explanation"] = "Operator observed packet loss."
        feedback["text"] = "[F2] Worksheet reported a link event. | [F11] Operator observed packet loss."
    seal(bundle)
    data = encode(bundle)
    producer = bundle["producer"]
    binding = {
        "contract": bundle["contract"], "schema_version": 2, "bundle_id": bundle_id, "revision": revision,
        "backend_origin": selection["origin"] + "/", "backend_database": selection["database"],
        "producer_instance_id": producer["instance_id"], "domain_id": producer["domain_id"],
        "submission_id": scope["submission_id"], "submission_fingerprint": producer["submission_fingerprint"],
        "fact_id": scope["reading"]["fact_id"], "captured_at": producer["captured_at"],
        "reading_sha256": producer["reading_sha256"], "bundle_sha256": sha(data),
    }
    snapshot = encode({**scope, "bundle_binding": binding}) if status == "draft_ready" else None
    n = scope["narrative"]
    state = {
        "run_id": scope["run_id"], "state": "eligible_for_narrative_review" if snapshot else "blocked_" + status,
        "eligible_for_review": snapshot is not None, "evidence_status": status,
        "provider_status": n["provider_status"], "provider_error_code": n["provider_error_code"],
        "ai_invoked": bundle["ai_invoked"], "live_provider_verified": False, "notification_delivery": "disabled",
        "snapshot_sha256": sha(snapshot) if snapshot else None, "binding": binding,
    }
    parent = OUTPUT / "BackendReportBundlesV2" / ("case-" + bundle_id)
    stage = parent / revision
    stage.mkdir(parents=True)
    (parent / ".admission.lock").touch()
    (stage / "bundle.json").write_bytes(data)
    (stage / "state.json").write_bytes(encode(state))
    if snapshot:
        (stage / "snapshot.json").write_bytes(snapshot)
    return stage


class BackendNarrativeV2Tests(unittest.TestCase):
    def setUp(self):
        self.case = "phase1c-" + uuid.uuid4().hex[:12]
        self.revision = "v1"
        self.stage = snapshot_case(self.case, self.revision)
        self.folder = OUTPUT / "BackendNarrativeReviewV2" / ("case-" + self.case) / self.revision
        directory = tempfile.TemporaryDirectory(prefix="vantagenet-narrative-decisions-")
        self.addCleanup(directory.cleanup)
        self.inputs = Path(directory.name)

    def run_workflow(self, file, expected=None, **params):
        args = [CLI, "rpa", "run", "--project-dir", str(PROJECT), "--file-path", file,
                "--skip-build", "--profile", "vantagenet-local-noauth", "--output", "json"]
        for key, value in params.items():
            args += ["--input-arguments", f"{key}={value}"]
        result = subprocess.run(args, env=ENV, capture_output=True, encoding="utf-8", errors="replace", timeout=150)
        logs = result.stdout + result.stderr
        if expected:
            self.assertIn(expected, logs)
            self.assertIn('"Result": "Failure"', logs)
        else:
            self.assertIn('"hasErrors": false', logs)
            self.assertIn('"errorMessage": null', logs)

    def review(self, expected=None, **overrides):
        self.run_workflow(REVIEW, expected, **{
            "projectFolder": PROJECT, "bundleId": self.case, "revision": self.revision,
            **overrides,
        })

    def generate(self, expected=None, **overrides):
        self.run_workflow(GENERATE, expected, **{
            "projectFolder": PROJECT, "bundleId": self.case, "revision": self.revision,
            **overrides,
        })

    def prepare(self):
        self.review()
        return self.folder / "request.json"

    def decision(self, action="approve", **overrides):
        request_path = self.folder / "request.json"
        request = read(request_path)
        data = {
            "binding": request["binding"], "request_id": request["request_id"],
            "request_sha256": sha(request_path.read_bytes()), "reviewer": "Offline regression reviewer",
            "reason": "Fabricated decision for deterministic workflow tests.",
            "decision": action, "decided_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_narrative": EDIT, "reviewed_narrative_sha256": sha(EDIT.encode()),
            **overrides,
        }
        path = self.inputs / ("fixture-" + uuid.uuid4().hex[:8] + ".json")
        path.write_bytes(encode(data))
        return path

    def approve(self):
        self.prepare()
        decision = self.decision()
        self.review(decisionPath=decision)
        return decision

    def test_prepare_valid_snapshot_and_form_binding(self):
        before = {f.name: sha(f.read_bytes()) for f in self.stage.iterdir()}
        request_path = self.prepare()
        form = self.folder / "narrative-review.html"
        request = read(request_path)
        self.assertEqual(request["binding"]["fact_id"], "41")
        self.assertEqual(request["binding"]["bundle_sha256"], before["bundle.json"])
        self.assertEqual(request["binding"]["snapshot_sha256"], before["snapshot.json"])
        subprocess.run(["node", str(Path(__file__).with_name("test_backend_narrative_form_v2.mjs")), str(form)],
                       env=ENV, check=True, timeout=30)
        self.review()
        self.assertEqual(request, read(request_path))
        self.assertEqual(before, {f.name: sha(f.read_bytes()) for f in self.stage.iterdir()})

    def test_blocked_admission(self):
        snapshot_case(self.case, "v2", "awaiting_feedback")
        self.review("Admission is blocked", revision="v2")

    def test_missing_staged_snapshot(self):
        (self.stage / "snapshot.json").rename(self.stage / "fixture-withheld.json")
        self.review("Missing required file: snapshot.json")

    def test_altered_bundle_bytes(self):
        with (self.stage / "bundle.json").open("ab") as file:
            file.write(b" ")
        self.review("Staged bundle hash mismatch")

    def test_altered_snapshot_bytes(self):
        with (self.stage / "snapshot.json").open("ab") as file:
            file.write(b" ")
        self.review("Staged snapshot hash mismatch")

    def test_wrong_case_binding(self):
        state = self.stage / "state.json"
        obj = read(state)
        obj["binding"]["bundle_id"] = "another-case"
        state.write_bytes(encode(obj))
        self.review("Staged case or revision identity mismatch")

    def test_wrong_revision_and_escaping_case(self):
        self.review("Requested revision is missing or superseded", revision="v44")
        self.review("Invalid case or revision", bundleId="..\\escape")

    def test_superseded_approval_and_new_revision(self):
        approved = self.approve()
        snapshot_case(self.case, "v2", "awaiting_feedback")
        self.generate("Requested revision is missing or superseded")
        snapshot_case(self.case, "v3")
        self.review(revision="v3")
        self.review("different review request or revision", revision="v3", decisionPath=approved)

    def test_no_approval(self):
        self.prepare()
        self.generate("Missing recorded narrative decision.")

    def test_reject_and_request_revision_are_terminal(self):
        self.prepare()
        self.review(decisionPath=self.decision("reject"))
        self.generate("Explicit approval is required")
        self.review("terminal decision already exists", decisionPath=self.decision())
        self.revision = "v2"
        self.folder = self.folder.parent / "v2"
        snapshot_case(self.case, "v2")
        self.prepare()
        self.review(decisionPath=self.decision("request_revision"))
        self.generate("Explicit approval is required")

    def test_invalid_reviewer_and_missing_choice(self):
        self.prepare()
        self.review("Valid reviewer identity", decisionPath=self.decision(reviewer=" "))
        self.review("Explicit narrative decision required", decisionPath=self.decision(""))

    def test_draft_and_edited_hash_binding(self):
        request = read(self.prepare())
        binding = {**request["binding"], "narrative_sha256": "0" * 64}
        self.review("different review request or revision", decisionPath=self.decision(binding=binding))
        self.review("Reviewed narrative hash mismatch", decisionPath=self.decision(reviewed_narrative="Changed without matching hash."))
        self.review("expired or its timestamp", decisionPath=self.decision(
            decided_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat()))

    def test_template_hash_mismatch(self):
        request = read(self.prepare())
        binding = {**request["binding"], "template_sha256": "0" * 64}
        self.review("different review request or revision", decisionPath=self.decision(binding=binding))

    def test_approval_replay_archives_exact_bytes(self):
        decision = self.approve()
        folder = self.folder / "decision"
        before = {f.name: (sha(f.read_bytes()), f.stat().st_mtime_ns) for f in folder.iterdir()}
        self.assertEqual((folder / "decision.json").read_bytes(), decision.read_bytes())
        self.review(decisionPath=decision)
        self.assertEqual(before, {f.name: (sha(f.read_bytes()), f.stat().st_mtime_ns) for f in folder.iterdir()})

    def test_altered_recorded_decision_blocks_generation(self):
        self.approve()
        with (self.folder / "decision" / "decision.json").open("ab") as file:
            file.write(b" ")
        self.generate("Archived decision hash changed")

    def test_unrepresentable_chart_fails_without_a_report(self):
        self.revision = "v2"
        self.folder = self.folder.parent / "v2"
        snapshot_case(self.case, "v2", chart=False)
        self.approve()
        self.generate("unsupported by the provisional chart")
        self.assertFalse((self.folder / "report").exists())

    def test_pptx_receipt_replay_and_powerpoint_render(self):
        decision = self.approve()
        snapshot = read(self.stage / "snapshot.json")
        self.generate()
        report = self.folder / "report"
        pptx, = report.glob("*.pptx")
        receipt = read(report / "generation-receipt.json")
        self.assertEqual(receipt["pptx_sha256"], sha(pptx.read_bytes()))
        self.assertEqual(receipt["decision_sha256"], sha(decision.read_bytes()))
        self.assertEqual(receipt["reviewed_narrative_sha256"], sha(EDIT.encode()))
        self.assertEqual(receipt["binding"], read(self.folder / "request.json")["binding"])
        self.assertEqual(receipt["output_path"], str(pptx))

        deck = Presentation(pptx)
        self.assertEqual(len(deck.slides), 3)
        shapes = {shape.name: shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame}
        self.assertEqual(shapes["Narrative"], EDIT)
        self.assertNotIn(snapshot["narrative"]["draft"], shapes["Narrative"])
        self.assertIn("Actual 90.25 %", shapes["Comparison"])
        self.assertIn("Target 99.0 %", shapes["Comparison"])
        bars = [line for line in shapes["Comparison"].splitlines() if "■" in line]
        self.assertEqual(list(map(len, bars)), [31, 34])
        self.assertIn("Below target", shapes["KPI"])
        self.assertIn("Workbook ed.xlsx | Row 5", shapes["Source"])
        self.assertIn("F2 | Worksheet-derived note", shapes["References"])
        self.assertIn("F11 | Operator API feedback", shapes["References"])
        for slide in deck.slides:
            text = "\n".join(shape.text for shape in slide.shapes if shape.has_text_frame)
            self.assertIn("BACKEND-CONFIRMED READING", text)
            self.assertNotIn("SYNTHETIC DATA", text)

        pdf = self.folder / "report-proof.pdf"
        self.run_workflow("RenderReportProof.cs", pptxPath=pptx, pdfPath=pdf)
        document = pdfium.PdfDocument(str(pdf))
        self.assertEqual(len(document), 3)
        pages = [" ".join(page.get_textpage().get_text_range().split()) for page in document]
        self.assertIn("Actual 90.25 %", pages[0])
        self.assertIn("Target 99.0 %", pages[0])
        self.assertIn(" ".join(EDIT.split()), pages[1])
        self.assertIn("F2 | Worksheet-derived note", pages[2])
        self.assertIn("F11 | Operator API feedback", pages[2])
        self.assertIn("Inspect the link.", pages[2])
        self.assertTrue(all("SYNTHETIC DATA" not in page for page in pages))
        for index, page in enumerate(document, 1):
            page.render(scale=1.3).to_pil().save(self.folder / f"render-{index}.png")
        document.close()
        before = {file.name: sha(file.read_bytes()) for file in report.iterdir()}
        self.generate()
        self.assertEqual(before, {file.name: sha(file.read_bytes()) for file in report.iterdir()})
        shutil.copyfile(pptx, self.folder / "report-proof.pptx")
        with pptx.open("ab") as file:
            file.write(b"changed")
        self.generate("Final PPTX or generation receipt changed")
        print(f"\nPowerPoint render proof (regression fixture): {pdf}", flush=True)

    def test_synthetic_f6_reference_and_proposal1_render(self):
        syn_case = "phase1c-f6-" + uuid.uuid4().hex[:8]
        bundle, _, _, selection = fixture("draft_ready", "v1")
        bundle["bundle_id"] = syn_case
        scope = bundle["snapshot"]
        scope["run_id"] = syn_case + "-v1"
        row = scope["reading"]
        row.update(actual_value=546.0, target_value=600.0, unit="Port", chart_supported=True,
                   kpi_name="DEP-WHF-Deployment Alpro", location_name="Demo South",
                   source_file="ed.xlsx", source_row=16)
        explanation = (
            "SYNTHETIC ACCEPTANCE SCENARIO — This is hypothetical test input, not a verified operational observation.\n\n"
            "The Demo South deployment count is below its reporting target. For this test scenario, "
            "assume that several planned deployment activities are awaiting site-access coordination."
        )
        action = (
            "Review the pending deployment list, identify activities awaiting access approval, "
            "and coordinate revised execution schedules with the responsible teams."
        )
        draft = (
            "In this synthetic acceptance scenario, based on the hypothetical assumption in [F6], "
            "the Demo South deployment count is below target because several planned deployment activities "
            "are awaiting site-access coordination. Recommended action: Review the pending deployment list, "
            "identify activities awaiting access approval, and coordinate revised execution schedules with the responsible teams [F6]."
        )
        scope["feedback"]["count"] = 1
        scope["feedback"]["origin"] = "operator-api"
        scope["feedback"]["records"] = [{
            "feedback_id": "6", "reference": "F6", "fact_id": row["fact_id"], "division": scope["division"],
            "explanation": explanation, "corrective_action": action,
            "origin": "operator-api", "created_at": "2026-11-23T07:35:24+00:00",
        }]
        scope["feedback"]["text"] = f"[F6] {explanation}"
        n = scope["narrative"]
        n["cited_feedback_ids"] = n["grounding"]["cited_feedback_ids"] = ["6"]
        n["root_cause"] = draft.split(" Recommended action: ")[0]
        n["prescriptive_action"] = draft.split(" Recommended action: ")[1]
        n["draft"] = draft
        n["references"] = [{
            "id": "F6", "feedback_id": "6", "origin": "operator-api",
            "text": f"{explanation} Proposed action: {action}",
        }]
        seal(bundle)
        data = encode(bundle)
        producer = bundle["producer"]
        binding = {
            "contract": bundle["contract"], "schema_version": 2, "bundle_id": syn_case, "revision": "v1",
            "backend_origin": selection["origin"] + "/", "backend_database": selection["database"],
            "producer_instance_id": producer["instance_id"], "domain_id": producer["domain_id"],
            "submission_id": scope["submission_id"], "submission_fingerprint": producer["submission_fingerprint"],
            "fact_id": row["fact_id"], "captured_at": producer["captured_at"],
            "reading_sha256": producer["reading_sha256"], "bundle_sha256": sha(data),
        }
        snapshot = encode({**scope, "bundle_binding": binding})
        state = {
            "run_id": scope["run_id"], "state": "eligible_for_narrative_review",
            "eligible_for_review": True, "evidence_status": "draft_ready",
            "provider_status": n["provider_status"], "provider_error_code": None,
            "ai_invoked": True, "live_provider_verified": False, "notification_delivery": "disabled",
            "snapshot_sha256": sha(snapshot), "binding": binding,
        }
        parent = OUTPUT / "BackendReportBundlesV2" / ("case-" + syn_case)
        stage = parent / "v1"
        stage.mkdir(parents=True)
        (parent / ".admission.lock").touch()
        (stage / "bundle.json").write_bytes(data)
        (stage / "state.json").write_bytes(encode(state))
        (stage / "snapshot.json").write_bytes(snapshot)

        self.run_workflow(REVIEW, projectFolder=PROJECT, bundleId=syn_case, revision="v1")
        folder = OUTPUT / "BackendNarrativeReviewV2" / ("case-" + syn_case) / "v1"
        request = read(folder / "request.json")
        self.assertEqual(request["binding"]["narrative_sha256"], sha(draft.encode()))
        dec_path = self.inputs / ("f6-" + uuid.uuid4().hex[:8] + ".json")
        dec_path.write_bytes(encode({
            "binding": request["binding"], "request_id": request["request_id"],
            "request_sha256": sha((folder / "request.json").read_bytes()),
            "reviewer": "Offline F6 regression reviewer",
            "reason": "Proposal 1 zero-edit approval for full F6 reference layout test.",
            "decision": "approve", "decided_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_narrative": draft, "reviewed_narrative_sha256": sha(draft.encode()),
        }))
        self.run_workflow(REVIEW, projectFolder=PROJECT, bundleId=syn_case, revision="v1", decisionPath=dec_path)
        self.run_workflow(GENERATE, projectFolder=PROJECT, bundleId=syn_case, revision="v1")

        report = folder / "report"
        pptx, = report.glob("*.pptx")
        deck = Presentation(pptx)
        shapes = {shape.name: shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame}
        self.assertEqual(shapes["Narrative"], draft)
        self.assertIn("SYNTHETIC ACCEPTANCE SCENARIO", shapes["References"])
        self.assertIn("Proposed action: Review the pending deployment list", shapes["References"])

        pdf = folder / "report-proof.pdf"
        self.run_workflow("RenderReportProof.cs", pptxPath=pptx, pdfPath=pdf)
        document = pdfium.PdfDocument(str(pdf))
        self.assertEqual(len(document), 3)
        pages = [" ".join(page.get_textpage().get_text_range().split()) for page in document]
        document.close()
        self.assertIn("Actual 546.0 Port", pages[0])
        self.assertIn("In this synthetic acceptance scenario,", pages[1])
        self.assertIn("SYNTHETIC ACCEPTANCE SCENARIO", pages[2])
        self.assertIn("coordinate revised execution schedules with the responsible teams.", pages[2])


if __name__ == "__main__":
    unittest.main()

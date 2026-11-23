"""Offline Phase 1B regressions. The .NET harness uses an in-process HTTP mock only."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
PROJECT_ID = "a5ddfe29-5288-4542-85a4-72e9a6156a5d"
SUBMISSION = "76558bb9-4597-43a4-95b0-0d6dca59e45d"
FINGERPRINT = "a" * 64
TIMESTAMP = "2026-11-21T08:30:00.123456+00:00"
SOURCES = ("BackendBundleV2Admission.cs", "BackendBundleV2Contract.cs", "BackendBundleV2Digest.cs")


def wire(value):
    return json.dumps(value, ensure_ascii=True, indent=1).encode("utf-8")


def digest(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reading_payload(bundle):
    return {
        "submission_fingerprint": bundle["producer"]["submission_fingerprint"],
        "reading": bundle["snapshot"]["reading"],
        "feedback": bundle["snapshot"]["feedback"]["records"],
    }


def seal(bundle):
    bundle["producer"]["reading_sha256"] = digest(reading_payload(bundle))


def fixture(status="draft_ready", revision="v1", provider="response_accepted", error_code=None):
    records = [] if status == "awaiting_feedback" else [
        dict(feedback_id="2", reference="F2", fact_id="41", division="ED",
             explanation="Worksheet note with é, 東京, 📶, and a line\nbreak.",
             corrective_action="", origin="fixture-worksheet-notes", created_at=TIMESTAMP),
        dict(feedback_id="11", reference="F11", fact_id="41", division="ED",
             explanation="Operator recorded a link loss \u2028 during testing.",
             corrective_action="Inspect the link.", origin="operator-api", created_at=TIMESTAMP),
    ]
    ready = status == "draft_ready"
    no_feedback = status == "awaiting_feedback"
    failed = status == "provider_unavailable"
    if no_feedback:
        provider = "not_attempted"
    cited = ["11"] if ready else []
    invoked = provider != "not_attempted"
    source_records = records[1:] if ready else records if status == "insufficient_evidence" else []
    references = [
        dict(id=row["reference"], feedback_id=row["feedback_id"], origin=row["origin"],
             text=row["explanation"] + (f" Proposed action: {row['corrective_action']}" if row["corrective_action"] else ""))
        for row in source_records
    ]
    root = None if failed else "Bukti tidak cukup" if not ready else "Division reports a link loss [F011]."
    action = None if failed else "Inspect the link [F11]." if ready else "Ask for specific observations."
    reading = dict(
        fact_id="41", kpi_id="23", location_id="12", kpi_name='Disponibilité "réseau"',
        kpi_archetype="Availability", location_name="東京 📶", date="2026-06-30", division="ED",
        actual_value=9e-7, target_value=None if no_feedback else 99.0, unit="%", higher_is_better=True,
        attainment_pct=None if no_feedback else -0.0, source_file="édition.xlsx", source_row=5,
        status_code="YELLOW" if no_feedback else "RED",
        status="Target unavailable" if no_feedback else "Below target", chart_supported=not no_feedback,
    )
    scope = dict(division="ED", report_date="2026-06-30", submission_id=SUBMISSION)
    feedback_text = " | ".join(f"[{row['reference']}] {row['explanation']}" for row in records)
    bundle = dict(
        contract="vantagenet.report-bundle", schema_version=2, bundle_id="ed-case", revision=revision,
        source_kind="backend-read-bundle", dataset="submitted", ai_invoked=invoked, evidence_status=status,
        producer=dict(domain_id=1, disposable=True, instance_id="disposable-ed-acceptance-01",
                      captured_at=TIMESTAMP, submission_fingerprint=FINGERPRINT, reading_sha256=""),
        scope={**scope, "fact_id": "41"},
        snapshot=dict(schema_version=2, origin="backend-confirmed-submission", run_id="ed-case-" + revision,
                      **scope, reading=reading,
                      feedback=dict(fact_id="41", count=len(records), origin="mixed" if records else "none",
                                    records=records, text=feedback_text or "No division feedback recorded for this reading."),
                      narrative=dict(
                          origin="provider-error" if failed else "backend-deterministic-gate" if no_feedback else "live-provider-rca",
                          backend_evidence_status="provider_error" if failed else "ai_draft" if ready else status,
                          llm_model="not available" if failed else "not called" if no_feedback else "Mock Model",
                          ai_invoked=invoked, provider_status=provider, provider_error_code=error_code,
                          grounding=dict(cited_feedback_ids=cited.copy(), structural_check=ready, citation_verified=ready),
                          cited_feedback_ids=cited, root_cause=root, prescriptive_action=action,
                          draft=f"{root} Recommended action: {action}" if ready else None,
                          references=references, error="Provider did not complete drafting." if failed else None,
                      )),
    )
    seal(bundle)
    row = {key: value for key, value in reading.items() if key not in ("status_code", "chart_supported")}
    row.update(fact_id=41, kpi_id=23, location_id=12, submission_id=SUBMISSION, status=reading["status_code"])
    ledger = dict(domain_id=1, status="confirmed", **scope, filename=reading["source_file"],
                  fingerprint=FINGERPRINT, confirmed_at=TIMESTAMP, row_count=1, readings=[row])
    instance = dict(app="VantageNet", disposable=True, domain_id=1,
                    instance_id="disposable-ed-acceptance-01", database="sqlite:disposable_test.db")
    selection = dict(origin="http://127.0.0.1:8187", domain=1, instance=instance["instance_id"],
                     database=instance["database"], submission=SUBMISSION, fact=41, bundle_id="ed-case", revision=revision)
    return bundle, ledger, instance, selection


class BackendBundleV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dotnet = os.environ.get("VANTAGENET_DOTNET") or shutil.which("dotnet")
        if not cls.dotnet:
            raise RuntimeError("An existing .NET 10 SDK is required. Set VANTAGENET_DOTNET.")
        cls.compiler = tempfile.TemporaryDirectory(prefix="vantagenet-v2-build-")
        cls.addClassCleanup(cls.compiler.cleanup)
        build = Path(cls.compiler.name)
        cls.environment = {**os.environ, "DOTNET_CLI_HOME": str(build), "DOTNET_NOLOGO": "1",
                           "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_ADD_GLOBAL_TOOLS_TO_PATH": "0"}
        (build / "Harness.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
            '<TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable>'
            '<TreatWarningsAsErrors>true</TreatWarningsAsErrors><NuGetAudit>false</NuGetAudit>'
            '</PropertyGroup></Project>', encoding="utf-8")
        (build / "NuGet.Config").write_text(
            "<configuration><packageSources><clear /></packageSources></configuration>", encoding="utf-8")
        for name in SOURCES:
            shutil.copyfile(PROJECT / name, build / name)
        shutil.copyfile(Path(__file__).with_name("BackendBundleV2Harness.cs.txt"), build / "Program.cs")
        result = subprocess.run([cls.dotnet, "build", "--nologo", str(build / "Harness.csproj")],
                                cwd=build, env=cls.environment, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.harness = build / "bin" / "Debug" / "net10.0" / "Harness.dll"

    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="vantagenet-v2-fixture-")
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.project = self.folder / "project"
        self.project.mkdir()
        (self.project / "project.json").write_bytes(wire(dict(projectId=PROJECT_ID)))
        self.report_case = self.project / "Output" / "BackendReportBundlesV2" / "case-ed-case"
        self.bundle, self.ledger, self.instance, self.selection = fixture()

    def execute(self, *args):
        process = subprocess.run([self.dotnet, str(self.harness), *map(str, args)],
                                 env=self.environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return process.stdout

    def admit(self, raw=None):
        for name, value in (("selection", self.selection), ("instance", self.instance), ("ledger", self.ledger)):
            (self.folder / (name + ".json")).write_bytes(wire(value))
        (self.folder / "bundle-wire.json").write_bytes(raw if raw is not None else wire(self.bundle))
        return json.loads(self.execute("admit", self.folder))

    def rejected(self, message, calls=3, raw=None, previously_published=False):
        result = self.admit(raw=raw)
        self.assertFalse(result["accepted"], result)
        self.assertIn(message, result["error"], result)
        self.assertEqual(result["calls"], calls, result)
        if not previously_published:
            self.assertFalse((self.project / "Output").exists())
        return result

    def accepted(self):
        result = self.admit()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["calls"], 3)
        path = Path(result["path"])
        return path, json.loads(path.read_bytes())

    def test_valid_v2_archive_and_binding(self):
        path, state = self.accepted()
        self.assertEqual(path, self.report_case / "v1" / "state.json")
        self.assertTrue(state["eligible_for_review"])
        self.assertEqual(state["state"], "eligible_for_narrative_review")
        self.assertFalse(state["live_provider_verified"])
        self.assertEqual(state["notification_delivery"], "disabled")
        self.assertEqual(state["provider_status"], "response_accepted")
        binding = state["binding"]
        archive = (path.parent / "bundle.json").read_bytes()
        self.assertEqual(archive, wire(self.bundle))
        self.assertEqual(binding["bundle_sha256"], hashlib.sha256(archive).hexdigest())
        snapshot = (path.parent / "snapshot.json").read_bytes()
        self.assertEqual(state["snapshot_sha256"], hashlib.sha256(snapshot).hexdigest())
        self.assertEqual(json.loads(snapshot)["bundle_binding"], binding)
        self.assertEqual(binding["reading_sha256"], self.bundle["producer"]["reading_sha256"])
        self.assertEqual(binding["fact_id"], "41")

    def test_wrong_envelope_version(self):
        self.bundle["schema_version"] = 1
        self.rejected("Unsupported v2")

    def test_wrong_snapshot_version(self):
        self.bundle["snapshot"]["schema_version"] = 1
        self.rejected("Invalid v2 snapshot")

    def test_wrong_source_kind(self):
        self.bundle["source_kind"] = "synthetic-fixture"
        self.rejected("Expected a submitted backend")

    def test_wrong_dataset(self):
        self.bundle["dataset"] = "demo"
        self.rejected("Expected a submitted backend")

    def test_instance_mismatch_stops_before_ledger_and_export(self):
        self.instance["instance_id"] = "unexpected-instance"
        self.rejected("Disposable backend identity mismatch", calls=1)

    def test_producer_mismatch(self):
        self.bundle["producer"]["instance_id"] = "different-reported-instance"
        self.rejected("Bundle producer identity mismatch")

    def test_producer_domain_and_disposable_mismatch(self):
        for field, value in (("domain_id", 2), ("disposable", False)):
            with self.subTest(field=field):
                original = self.bundle["producer"][field]
                self.bundle["producer"][field] = value
                self.rejected("Bundle producer identity mismatch")
                self.bundle["producer"][field] = original

    def test_non_disposable_database_configuration(self):
        self.selection["database"] = "sqlite:omnikpi.db"
        self.rejected("explicit disposable", calls=0)

    def test_preflight_expected_database_and_disposable(self):
        for field, bad in (("database", "sqlite:omnikpi.db"), ("disposable", False)):
            with self.subTest(field=field):
                original = self.instance[field]
                self.instance[field] = bad
                self.rejected("Disposable backend identity mismatch", calls=1)
                self.instance[field] = original

    def test_non_pinned_origin_refused(self):
        for origin in ("https://127.0.0.1:8187", "http://localhost:8187", "http://127.0.0.1:8187/path",
                       "http://127.0.0.1:8187/?q=1", "http://127.0.0.1:8187@other.invalid"):
            with self.subTest(origin=origin):
                self.selection["origin"] = origin
                self.rejected("pinned HTTP IPv4 loopback", calls=0)

    def test_redirect_refused(self):
        (self.folder / "instance.json.status").write_text("307", encoding="ascii")
        self.rejected("HTTP 307", calls=1)

    def test_wrong_submission_and_unconfirmed_ledger(self):
        self.ledger["status"] = "draft"
        self.rejected("independently confirmed submission", calls=2)
        self.ledger["status"] = "confirmed"
        self.bundle["scope"]["submission_id"] = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        self.bundle["snapshot"]["submission_id"] = self.bundle["scope"]["submission_id"]
        self.rejected("scope differs from the confirmed ledger")

    def test_wrong_fact_rejected_against_ledger_and_scope(self):
        self.ledger["readings"][0]["fact_id"] = 99
        self.rejected("Exact fact must belong", calls=2)
        self.ledger["readings"][0]["fact_id"] = 41
        self.bundle["scope"]["fact_id"] = "99"
        self.rejected("fact differs from the confirmed fact")

    def test_wrong_kpi_location_source_and_value_even_with_valid_digest(self):
        for field, value, message in (
            ("kpi_id", "99", "Reading identity mismatch"),
            ("location_id", "99", "Reading identity mismatch"),
            ("source_file", "other.xlsx", "Reading provenance mismatch"),
            ("source_row", 99, "Reading source row mismatch"),
            ("actual_value", 42.0, "Reading value differs"),
            ("target_value", 50.0, "Reading value differs"),
        ):
            with self.subTest(field=field):
                row = self.bundle["snapshot"]["reading"]
                original = row[field]
                row[field] = value
                seal(self.bundle)
                self.rejected(message)
                row[field] = original

    def test_wrong_fingerprint_even_with_recomputed_digest(self):
        self.bundle["producer"]["submission_fingerprint"] = "b" * 64
        seal(self.bundle)
        self.rejected("fingerprint does not match the ledger")

    def test_missing_and_invalid_capture_timestamp(self):
        for value in ("", "2026-11-20T08:30:00+00:00"):
            with self.subTest(value=value):
                self.bundle["producer"]["captured_at"] = value
                self.rejected("timestamp" if not value else "predates confirmation")

    def test_wrong_feedback_fact_origin_or_division(self):
        row = self.bundle["snapshot"]["feedback"]["records"][0]
        for field, value, message in (
            ("fact_id", "99", "Feedback fact or reference mismatch"),
            ("origin", "genuine-human", "Unknown feedback origin"),
            ("division", "MBB", "Feedback fact or reference mismatch"),
        ):
            with self.subTest(field=field):
                original = row[field]
                row[field] = value
                seal(self.bundle)
                self.rejected(message)
                row[field] = original

    def test_duplicate_and_out_of_order_feedback(self):
        records = self.bundle["snapshot"]["feedback"]["records"]
        records.reverse()
        seal(self.bundle)
        self.rejected("Feedback IDs must be unique and ordered")
        records.reverse()
        records[1]["feedback_id"] = records[0]["feedback_id"]
        seal(self.bundle)
        self.rejected("Feedback IDs must be unique and ordered")

    def test_unresolved_declared_and_inline_citation(self):
        narrative = self.bundle["snapshot"]["narrative"]
        narrative["references"][0]["feedback_id"] = "999"
        self.rejected("Unresolved citation")
        narrative["references"][0]["feedback_id"] = "11"
        narrative["root_cause"] = "Cross-fact citation [F discussion [F999]."
        narrative["draft"] = narrative["root_cause"] + " Recommended action: " + narrative["prescriptive_action"]
        self.rejected("Unresolved inline")

    def test_reference_origin_cannot_relabel_operator_or_fixture(self):
        self.bundle["snapshot"]["narrative"]["references"][0]["origin"] = "fixture-worksheet-notes"
        self.rejected("Reference metadata differs")

    def test_grounding_consistency(self):
        grounding = self.bundle["snapshot"]["narrative"]["grounding"]
        grounding["citation_verified"] = False
        self.rejected("Invalid grounding metadata")
        grounding["citation_verified"] = True
        grounding["cited_feedback_ids"] = ["2"]
        self.rejected("Invalid grounding metadata")

    def test_reading_digest_mismatch_with_matching_ledger(self):
        self.bundle["snapshot"]["reading"]["actual_value"] = 42.0
        self.ledger["readings"][0]["actual_value"] = 42.0
        self.rejected("Reading digest mismatch")

    def test_feedback_digest_mismatch_with_matching_summary(self):
        feedback = self.bundle["snapshot"]["feedback"]
        original = feedback["records"][0]["explanation"]
        feedback["records"][0]["explanation"] = "Changed worksheet observation."
        feedback["text"] = feedback["text"].replace(original, "Changed worksheet observation.")
        self.rejected("Reading digest mismatch")

    def test_fingerprint_digest_mismatch_with_matching_ledger(self):
        self.bundle["producer"]["submission_fingerprint"] = "b" * 64
        self.ledger["fingerprint"] = "b" * 64
        self.rejected("Reading digest mismatch")

    def test_cross_language_python_digest_parity(self):
        label = '"\\/\u0000\b\t\n\f\r\u001f\u007f\u0085\u2028\u2029é 東京 📶'
        numbers = [0, -1, 10**100, 0.0, -0.0, 1.0, -2.5, 1e-4, 1e-5, 1e15, 1e16, 1e20,
                   1e23, 1e-100, float.fromhex("0x0.0000000000001p-1022"),
                   float.fromhex("0x1.fffffffffffffp+1023")]
        rng = random.Random(4317)
        for _ in range(10000):
            number = struct.unpack(">d", rng.getrandbits(64).to_bytes(8, "big"))[0]
            if math.isfinite(number):
                numbers.append(number)
        vectors = [
            dict(submission_fingerprint=FINGERPRINT,
                 reading=dict(unicode=label, numeric=number, nullable=None, flag=False),
                 feedback=[] if index % 2 else [dict(feedback_id="2"), dict(feedback_id="11")])
            for index, number in enumerate(numbers)
        ]
        filename = self.folder / "vectors.json"
        filename.write_text(json.dumps(vectors, ensure_ascii=True, allow_nan=False), encoding="utf-8")
        actual = self.execute("digests", filename).splitlines()
        expected = list(map(digest, vectors))
        self.assertEqual(len(actual), len(expected))
        for index, (got, wanted) in enumerate(zip(actual, expected, strict=True)):
            self.assertEqual(got, wanted, f"Python digest mismatch for {numbers[index]!r}")
        print(f"\nPython/.NET parity: {len(vectors)} vectors", flush=True)

    def test_noncanonical_wire_numbers_recompute_python_digest(self):
        wire_data = wire(self.bundle).replace(b"9e-07", b"9.000000e-7").replace(b"99.0", b"9.9e+1")
        self.assertNotEqual(wire_data, wire(self.bundle))
        result = self.admit(raw=wire_data)
        self.assertTrue(result["accepted"], result)

    def test_blocked_statuses_preserve_metadata_without_snapshot(self):
        statuses = [
            ("awaiting_feedback", "not_attempted", None),
            ("insufficient_evidence", "response_accepted", None),
            ("provider_unavailable", "not_attempted", "missing_configuration"),
            ("provider_unavailable", "attempted_unconfirmed", "timeout"),
            ("provider_unavailable", "attempted_unconfirmed", "request_failed"),
            ("provider_unavailable", "response_rejected", "invalid_response"),
            ("provider_unavailable", "response_rejected", "invalid_citations"),
        ]
        for index, (status, provider, code) in enumerate(statuses, start=1):
            with self.subTest(status=status, provider=provider, code=code):
                self.bundle, self.ledger, self.instance, self.selection = fixture(status, f"v{index}", provider, code)
                path, state = self.accepted()
                self.assertEqual(state["state"], "blocked_" + status)
                self.assertEqual(state["provider_status"], provider)
                self.assertEqual(state["provider_error_code"], code)
                self.assertFalse(state["eligible_for_review"])
                self.assertIsNone(state["snapshot_sha256"])
                self.assertFalse((path.parent / "snapshot.json").exists())
                self.assertEqual((path.parent / "bundle.json").read_bytes(), wire(self.bundle))

    def test_invalid_provider_combinations_and_blocked_draft(self):
        narrative = self.bundle["snapshot"]["narrative"]
        narrative["provider_status"] = "attempted_unconfirmed"
        self.rejected("Invalid evidence status or provider metadata")
        narrative["provider_status"] = "response_accepted"
        narrative["ai_invoked"] = False
        self.rejected("invocation flags disagree")
        self.bundle, self.ledger, self.instance, self.selection = fixture("awaiting_feedback")
        self.bundle["snapshot"]["narrative"]["draft"] = "An invented draft"
        self.rejected("Blocked status cannot supply a draft")

    def test_same_byte_replay_is_immutable(self):
        path, before = self.accepted()
        times = {item.name: item.stat().st_mtime_ns for item in path.parent.iterdir()}
        replay, after = self.accepted()
        self.assertEqual((replay, after), (path, before))
        self.assertEqual({item.name: item.stat().st_mtime_ns for item in path.parent.iterdir()}, times)
        self.assertEqual(len(list(self.report_case.glob("v*"))), 1)

    def test_changed_bytes_same_revision_rejected(self):
        path, _ = self.accepted()
        self.rejected("different bytes", raw=wire(self.bundle) + b"\n", previously_published=True)
        self.assertEqual((path.parent / "bundle.json").read_bytes(), wire(self.bundle))

    def test_superseded_revision_is_rejected_even_after_blocked_revision(self):
        old = copy.deepcopy(self.bundle), copy.deepcopy(self.selection)
        self.accepted()
        self.bundle, self.ledger, self.instance, self.selection = fixture(
            "provider_unavailable", "v10", "attempted_unconfirmed", "timeout")
        self.accepted()
        self.bundle, self.selection = old
        self.rejected("superseded", calls=0, previously_published=True)
        self.assertTrue((self.report_case / "v1" / "snapshot.json").is_file())

    def test_case_cannot_be_rebound_to_another_producer(self):
        self.accepted()
        self.bundle, self.ledger, self.instance, self.selection = fixture(revision="v2")
        self.bundle["producer"]["instance_id"] = "disposable-other-01"
        self.instance["instance_id"] = self.selection["instance"] = "disposable-other-01"
        self.rejected("pinned to a different reading or producer", previously_published=True)
        self.assertFalse((self.report_case / "v2").exists())

    def test_staged_snapshot_tampering_blocks_replay(self):
        path, _ = self.accepted()
        (path.parent / "snapshot.json").write_bytes(b"edited")
        self.rejected("Staged snapshot changed", previously_published=True)

    def test_failed_publication_leaves_no_partial_revision(self):
        self.report_case.mkdir(parents=True)
        destination = self.report_case / "v1"
        destination.write_bytes(b"preregistered collision")
        result = self.admit()
        self.assertFalse(result["accepted"], result)
        self.assertEqual(destination.read_bytes(), b"preregistered collision")
        self.assertEqual(list(self.report_case.glob(".preparing-*")), [])
        self.assertFalse((destination / "state.json").exists())

    def test_duplicate_json_never_publishes(self):
        raw = wire(self.bundle).replace(b'"schema_version": 2', b'"schema_version": 1, "schema_version": 2', 1)
        self.rejected("Duplicate JSON property", raw=raw)

    def test_synthetic_v1_cannot_enter_v2_path(self):
        self.rejected("Unexpected or missing v2 field",
                      raw=(PROJECT / "Data" / "s43-report-bundle.synthetic.json").read_bytes())


if __name__ == "__main__":
    unittest.main()

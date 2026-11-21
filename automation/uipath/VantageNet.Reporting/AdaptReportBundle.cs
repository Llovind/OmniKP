#nullable enable
using System;
using System.IO;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using System.Text.Json.Nodes;
using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class AdaptReportBundle : CodedWorkflow
    {
        [Workflow]
        public string Execute(string bundlePath, string expectedInstanceId = "")
        {
            bundlePath = Path.GetFullPath(bundlePath);
            var project = new DirectoryInfo(Path.GetDirectoryName(bundlePath)!);
            while (project != null && !File.Exists(Path.Combine(project.FullName, "project.json"))) project = project.Parent;
            NarrativeState.Require(project != null, "Bundle must be inside the existing UiPath project.");
            var b = NarrativeState.Read(bundlePath);
            var version = b["schema_version"]!.GetValue<int>();
            NarrativeState.Require(NarrativeState.Text(b, "contract") == "vantagenet.report-bundle" && (version == 1 || version == 2), "Unsupported report bundle version.");
            var backend = version == 2;
            NarrativeState.Require(backend ? NarrativeState.Text(b, "source_kind") == "backend-read-bundle" :
                NarrativeState.Text(b, "source_kind") == "synthetic-fixture" && !b["ai_invoked"]!.GetValue<bool>(), "Report bundle source does not match its version.");
            NarrativeState.Require(NarrativeState.Text(b, "dataset") == "submitted", "Explicit submitted dataset required; latest/all/demo are not supported.");
            var id = NarrativeState.Text(b, "bundle_id");
            var revision = NarrativeState.Text(b, "revision");
            NarrativeState.Require(Regex.IsMatch(id, "^[A-Za-z0-9_-]{1,48}$") && Regex.IsMatch(revision, "^v[1-9][0-9]{0,5}$"), "Invalid bundle ID or revision.");
            var run = id + "-" + revision;
            var s = b["snapshot"]!;
            var scope = b["scope"]!;
            NarrativeState.Require(NarrativeState.Text(s, "run_id") == run && s["schema_version"]!.GetValue<int>() == version &&
                NarrativeState.Text(s, "origin") == (backend ? "backend-confirmed-submission" : "synthetic-local-fixture"), "Snapshot version, run or source mismatch.");
            foreach (var key in new[] { "division", "report_date", "submission_id" })
                NarrativeState.Require(!string.IsNullOrWhiteSpace(NarrativeState.Text(scope, key)) && NarrativeState.Text(scope, key) == NarrativeState.Text(s, key), "Report scope mismatch: " + key);
            NarrativeState.Require(DateTime.TryParseExact(NarrativeState.Text(scope, "report_date"), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out _), "Explicit report date required.");
            var k = s["reading"]!;
            foreach (var key in new[] { "fact_id", "kpi_name", "location_name", "status", "source_file" })
                NarrativeState.Require(!string.IsNullOrWhiteSpace(NarrativeState.Text(k, key)), "Missing reading field: " + key);
            NarrativeState.Require(backend ? k["unit"] != null : !string.IsNullOrWhiteSpace(NarrativeState.Text(k, "unit")), "Missing reading unit.");
            NarrativeState.Require(k["source_row"]!.GetValue<int>() > 0 && NarrativeState.Text(k, "division") == NarrativeState.Text(scope, "division") && NarrativeState.Text(k, "date") == NarrativeState.Text(scope, "report_date"), "Reading provenance/scope mismatch.");
            var status = NarrativeState.Text(b, "evidence_status");
            NarrativeState.Require(status == "draft_ready" || status == "awaiting_feedback" || status == "insufficient_evidence" || status == "provider_unavailable", "Unknown evidence status.");
            NarrativeState.Require(NarrativeState.Text(s["feedback"]!, "fact_id") == NarrativeState.Text(k, "fact_id"), "Feedback reading mismatch.");
            if (backend)
                ValidateBackend(b, expectedInstanceId, status == "draft_ready");
            else
                NarrativeState.Require(NarrativeState.Text(s["feedback"]!, "origin") == "synthetic-fixture-not-human-feedback" &&
                    NarrativeState.Text(s["narrative"]!, "origin") == "synthetic-script-not-live-RCA", "Synthetic fixture provenance mismatch.");
            if (!backend || status == "draft_ready")
                NarrativeState.Require(double.IsFinite(k["actual_value"]!.GetValue<double>()) && k["target_value"] != null &&
                    double.IsFinite(k["target_value"]!.GetValue<double>()) && k["actual_value"]!.GetValue<double>() >= 0 &&
                    k["target_value"]!.GetValue<double>() > 0, "Values unsupported by provisional chart.");
            if (status == "draft_ready")
            {
                var draft = NarrativeState.Text(s["narrative"]!, "draft");
                NarrativeState.Require(!string.IsNullOrWhiteSpace(draft) && (backend || draft.Length <= 600) && s["narrative"]!["references"]!.AsArray().Count > 0, "Narrative text/references required for review readiness.");
            }
            var root = Path.Combine(project!.FullName, "Output", "ReportBundles");
            Directory.CreateDirectory(root);
            using var gate = new FileStream(Path.Combine(root, run + ".lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var folder = Path.Combine(root, run);
            var hash = NarrativeState.FileHash(bundlePath);
            if (Directory.Exists(folder))
            {
                var prior = NarrativeState.Read(Path.Combine(folder, "state.json"));
                NarrativeState.Require(NarrativeState.Text(prior, "bundle_sha256") == hash && NarrativeState.FileHash(Path.Combine(folder, "bundle.json")) == hash, "Bundle revision changed; publish a new revision and obtain new review.");
                if (prior["snapshot_sha256"] != null) NarrativeState.Require(NarrativeState.FileHash(Path.Combine(folder, "snapshot.json")) == NarrativeState.Text(prior, "snapshot_sha256"), "Staged snapshot changed; reconcile manually.");
                return Path.Combine(folder, "state.json");
            }
            var staging = folder + ".preparing";
            NarrativeState.Require(!Directory.Exists(staging), "Incomplete adapter staging; inspect before recovery.");
            Directory.CreateDirectory(staging);
            File.Copy(bundlePath, Path.Combine(staging, "bundle.json"));
            var readyState = backend ? "backend_snapshot_staged_requires_new_human_review" : "synthetic_snapshot_staged_requires_new_human_review";
            var state = new JsonObject { ["run_id"] = run, ["bundle_sha256"] = hash, ["evidence_status"] = status, ["state"] = status == "draft_ready" ? readyState : "blocked_" + status, ["notification_delivery"] = "disabled", ["backend_contract_verified"] = false };
            if (status == "draft_ready")
            {
                var snapshot = s.DeepClone();
                snapshot["bundle_binding"] = new JsonObject { ["contract"] = $"vantagenet.report-bundle/{version}", ["revision"] = revision, ["bundle_sha256"] = hash };
                if (backend) snapshot["producer"] = b["producer"]!.DeepClone();
                NarrativeState.SaveNew(Path.Combine(staging, "snapshot.json"), snapshot);
                state["snapshot_sha256"] = NarrativeState.FileHash(Path.Combine(staging, "snapshot.json"));
            }
            NarrativeState.SaveNew(Path.Combine(staging, "state.json"), state);
            Directory.Move(staging, folder);
            return Path.Combine(folder, "state.json");
        }

        private static void ValidateBackend(JsonNode bundle, string expectedInstanceId, bool ready)
        {
            var producer = bundle["producer"]!;
            NarrativeState.Require(!string.IsNullOrWhiteSpace(expectedInstanceId) && producer["disposable"]!.GetValue<bool>() &&
                producer["domain_id"]!.GetValue<int>() == 1 && NarrativeState.Text(producer, "instance_id") == expectedInstanceId,
                "Bundle must come from the designated disposable backend.");
            foreach (var field in new[] { "submission_fingerprint", "reading_sha256" })
                NarrativeState.Require(Regex.IsMatch(NarrativeState.Text(producer, field), "^[a-f0-9]{64}$"), "Invalid producer digest: " + field);
            var snapshot = bundle["snapshot"]!;
            var reading = snapshot["reading"]!;
            var factId = NarrativeState.Text(reading, "fact_id");
            NarrativeState.Require(factId == NarrativeState.Text(bundle["scope"]!, "fact_id"), "Bundle selected reading mismatch.");
            var feedback = snapshot["feedback"]!;
            var records = feedback["records"]!.AsArray();
            NarrativeState.Require(records.Count == feedback["count"]!.GetValue<int>(), "Feedback count mismatch.");
            var byId = records.ToDictionary(record => NarrativeState.Text(record!, "feedback_id"));
            foreach (var record in records)
            {
                var id = NarrativeState.Text(record!, "feedback_id");
                var origin = NarrativeState.Text(record!, "origin");
                NarrativeState.Require(NarrativeState.Text(record!, "fact_id") == factId &&
                    NarrativeState.Text(record!, "reference") == "F" + id &&
                    (origin == "fixture-worksheet-notes" || origin == "operator-api"), "Feedback record identity or provenance mismatch.");
            }
            var narrative = snapshot["narrative"]!;
            if (!ready)
            {
                NarrativeState.Require(narrative["draft"] == null, "Blocked report bundle contains a draft.");
                return;
            }
            NarrativeState.Require(bundle["ai_invoked"]!.GetValue<bool>() && narrative["ai_invoked"]!.GetValue<bool>() &&
                NarrativeState.Text(narrative, "origin") == "live-provider-rca" && narrative["grounding"]!["citation_verified"]!.GetValue<bool>() &&
                reading["chart_supported"]!.GetValue<bool>(), "Report requires a grounded draft and chartable values.");
            var cited = narrative["cited_feedback_ids"]!.AsArray().Select(id => id!.GetValue<string>()).ToHashSet();
            var references = narrative["references"]!.AsArray();
            NarrativeState.Require(cited.Count > 0 && cited.SetEquals(references.Select(reference => NarrativeState.Text(reference!, "feedback_id"))),
                "Narrative citations and references differ.");
            foreach (var reference in references)
            {
                var id = NarrativeState.Text(reference!, "feedback_id");
                NarrativeState.Require(byId.TryGetValue(id, out var record) &&
                    NarrativeState.Text(reference!, "id") == NarrativeState.Text(record!, "reference") &&
                    NarrativeState.Text(reference!, "origin") == NarrativeState.Text(record!, "origin"),
                    "Narrative reference must resolve to feedback for the selected reading.");
            }
        }
    }
}

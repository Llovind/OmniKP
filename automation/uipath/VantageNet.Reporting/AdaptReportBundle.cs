#nullable enable
using System;
using System.IO;
using System.Globalization;
using System.Text.RegularExpressions;
using System.Text.Json.Nodes;
using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class AdaptReportBundle : CodedWorkflow
    {
        // Robot-local proposed bundle boundary, NOT a new backend API or live integration.
        [Workflow]
        public string Execute(string bundlePath)
        {
            bundlePath = Path.GetFullPath(bundlePath);
            var project = new DirectoryInfo(Path.GetDirectoryName(bundlePath)!);
            while (project != null && !File.Exists(Path.Combine(project.FullName, "project.json"))) project = project.Parent;
            NarrativeState.Require(project != null, "Bundle must be inside the existing UiPath project.");
            var b = NarrativeState.Read(bundlePath);
            NarrativeState.Require(NarrativeState.Text(b, "contract") == "vantagenet.report-bundle" && b["schema_version"]!.GetValue<int>() == 1, "Unsupported report bundle version.");
            NarrativeState.Require(NarrativeState.Text(b, "source_kind") == "synthetic-fixture" && !b["ai_invoked"]!.GetValue<bool>(), "Live backend/AI bundle admission is not verified; no synthetic relabeling allowed.");
            NarrativeState.Require(NarrativeState.Text(b, "dataset") == "submitted", "Explicit submitted dataset required; latest/all/demo are not supported.");
            var id = NarrativeState.Text(b, "bundle_id");
            var revision = NarrativeState.Text(b, "revision");
            NarrativeState.Require(Regex.IsMatch(id, "^[A-Za-z0-9_-]{1,48}$") && Regex.IsMatch(revision, "^v[1-9][0-9]{0,5}$"), "Invalid bundle ID or revision.");
            var run = id + "-" + revision;
            var s = b["snapshot"]!;
            var scope = b["scope"]!;
            NarrativeState.Require(NarrativeState.Text(s, "run_id") == run && s["schema_version"]!.GetValue<int>() == 1 && NarrativeState.Text(s, "origin") == "synthetic-local-fixture", "Bundle must name a distinct versioned synthetic run.");
            foreach (var key in new[] { "division", "report_date", "submission_id" })
                NarrativeState.Require(!string.IsNullOrWhiteSpace(NarrativeState.Text(scope, key)) && NarrativeState.Text(scope, key) == NarrativeState.Text(s, key), "Report scope mismatch: " + key);
            NarrativeState.Require(DateTime.TryParseExact(NarrativeState.Text(scope, "report_date"), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out _), "Explicit report date required.");
            var k = s["reading"]!;
            foreach (var key in new[] { "fact_id", "kpi_name", "location_name", "unit", "status", "source_file" })
                NarrativeState.Require(!string.IsNullOrWhiteSpace(NarrativeState.Text(k, key)), "Missing reading field: " + key);
            NarrativeState.Require(k["source_row"]!.GetValue<int>() > 0 && NarrativeState.Text(k, "division") == NarrativeState.Text(scope, "division") && NarrativeState.Text(k, "date") == NarrativeState.Text(scope, "report_date"), "Reading provenance/scope mismatch.");
            NarrativeState.Require(double.IsFinite(k["actual_value"]!.GetValue<double>()) && double.IsFinite(k["target_value"]!.GetValue<double>()) && k["actual_value"]!.GetValue<double>() >= 0 && k["target_value"]!.GetValue<double>() > 0, "Values unsupported by provisional chart.");
            NarrativeState.Require(NarrativeState.Text(s["feedback"]!, "fact_id") == NarrativeState.Text(k, "fact_id") && NarrativeState.Text(s["feedback"]!, "origin") == "synthetic-fixture-not-human-feedback", "Feedback identity/provenance mismatch.");
            NarrativeState.Require(NarrativeState.Text(s["narrative"]!, "origin") == "synthetic-script-not-live-RCA", "No fabricated live RCA provenance allowed.");
            var status = NarrativeState.Text(b, "evidence_status");
            NarrativeState.Require(status == "draft_ready" || status == "awaiting_feedback" || status == "insufficient_evidence" || status == "provider_unavailable", "Unknown evidence status.");
            if (status == "draft_ready")
            {
                var draft = NarrativeState.Text(s["narrative"]!, "draft");
                NarrativeState.Require(!string.IsNullOrWhiteSpace(draft) && draft.Length <= 600 && s["narrative"]!["references"]!.AsArray().Count > 0, "Narrative text/references required for review readiness.");
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
            var state = new JsonObject { ["run_id"] = run, ["bundle_sha256"] = hash, ["evidence_status"] = status, ["state"] = status == "draft_ready" ? "synthetic_snapshot_staged_requires_new_human_review" : "blocked_" + status, ["notification_delivery"] = "disabled", ["backend_contract_verified"] = false };
            if (status == "draft_ready")
            {
                var snapshot = s.DeepClone();
                snapshot["bundle_binding"] = new JsonObject { ["contract"] = "vantagenet.report-bundle/1", ["revision"] = revision, ["bundle_sha256"] = hash };
                NarrativeState.SaveNew(Path.Combine(staging, "snapshot.json"), snapshot);
                state["snapshot_sha256"] = NarrativeState.FileHash(Path.Combine(staging, "snapshot.json"));
            }
            NarrativeState.SaveNew(Path.Combine(staging, "state.json"), state);
            Directory.Move(staging, folder);
            return Path.Combine(folder, "state.json");
        }
    }
}

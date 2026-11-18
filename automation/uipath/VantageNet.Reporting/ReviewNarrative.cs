#nullable enable
using System;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class ReviewNarrative : CodedWorkflow
    {
        [Workflow]
        public string Execute(string snapshotPath, string templatePath, string decisionPath = "")
        {
            snapshotPath = Path.GetFullPath(snapshotPath);
            templatePath = Path.GetFullPath(templatePath);
            var project = new DirectoryInfo(Path.GetDirectoryName(snapshotPath)!);
            while (project != null && !File.Exists(Path.Combine(project.FullName, "project.json"))) project = project.Parent;
            NarrativeState.Require(project != null, "Snapshot must be within the existing project.");
            var s = NarrativeState.Read(snapshotPath);
            NarrativeState.Require(NarrativeState.Text(s, "origin") == "synthetic-local-fixture" && NarrativeState.Text(s["narrative"]!, "origin") == "synthetic-script-not-live-RCA", "Only labeled synthetic report snapshots supported.");
            var run = NarrativeState.Text(s, "run_id");
            NarrativeState.Require(Regex.IsMatch(run, "^[A-Za-z0-9_-]{1,80}$"), "Invalid narrative run ID.");
            var reading = s["reading"]!;
            NarrativeState.Require(NarrativeState.Text(reading, "division") == NarrativeState.Text(s, "division") && NarrativeState.Text(reading, "date") == NarrativeState.Text(s, "report_date"), "Reading/report scope mismatch.");
            var folder = Path.Combine(project!.FullName, "Output", "NarrativeReview", run);
            Directory.CreateDirectory(folder);
            using var gate = new FileStream(Path.Combine(folder, "review.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var requestPath = Path.Combine(folder, "request.json");
            if (!File.Exists(requestPath))
            {
                NarrativeState.Require(string.IsNullOrWhiteSpace(decisionPath), "Prepare narrative review before submitting a decision.");
                NarrativeState.Require(!File.Exists(Path.Combine(folder, "snapshot.json")), "Incomplete preparation; preserve and reconcile this run.");
                File.Copy(snapshotPath, Path.Combine(folder, "snapshot.json"));
                NarrativeState.SaveNew(requestPath, new JsonObject { ["run_id"] = run, ["submission_id"] = s["submission_id"]!.DeepClone(), ["snapshot_path"] = snapshotPath, ["snapshot_sha256"] = NarrativeState.FileHash(snapshotPath), ["narrative_sha256"] = MappingReview.Hash(NarrativeState.Text(s["narrative"]!, "draft")), ["template_path"] = templatePath, ["template_sha256"] = NarrativeState.FileHash(templatePath), ["created_at"] = DateTimeOffset.UtcNow.ToString("O") });
            }
            var r = NarrativeState.CheckRequest(requestPath);
            NarrativeState.Require(NarrativeState.Text(r, "snapshot_path") == snapshotPath && NarrativeState.Text(r, "template_path") == templatePath, "Prepared paths differ from requested paths.");
            if (string.IsNullOrWhiteSpace(decisionPath))
            {
                NarrativeState.CheckTerminal(folder);
                var html = Path.Combine(folder, "narrative-review.html");
                var data = JsonSerializer.Serialize(new { request = r, snapshot = s });
                var content = File.ReadAllText(Path.Combine(project.FullName, "Data", "narrative-review.html")).Replace("/*NARRATIVE_DATA*/null", data);
                if (!File.Exists(html)) File.WriteAllText(html, content, new UTF8Encoding(false));
                return html;
            }
            NarrativeState.Require(!File.Exists(Path.Combine(folder, "generation-intent.json")), "Generation already attempted; reconcile it before changing narrative decisions.");
            var d = NarrativeState.CheckDecision(r, decisionPath);
            var hash = NarrativeState.FileHash(decisionPath);
            var attempts = Path.Combine(folder, "decisions");
            var attempt = Path.Combine(attempts, hash);
            NarrativeState.CheckTerminal(folder);
            if (File.Exists(Path.Combine(attempt, "result.json"))) return Path.Combine(attempt, "result.json");
            NarrativeState.Require(!Directory.Exists(attempt), "Incomplete decision archive; inspect before retrying.");
            Directory.CreateDirectory(attempt);
            File.Copy(decisionPath, Path.Combine(attempt, "decision.json"));
            NarrativeState.SaveNew(Path.Combine(attempt, "result.json"), new JsonObject { ["state"] = d["decision"]!.DeepClone(), ["decision_sha256"] = hash, ["snapshot_sha256"] = r["snapshot_sha256"]!.DeepClone(), ["approved_narrative_sha256"] = MappingReview.Hash(NarrativeState.Text(d, "reviewed_narrative")), ["recorded_at"] = DateTimeOffset.UtcNow.ToString("O") });
            return Path.Combine(attempt, "result.json");
        }
    }
}

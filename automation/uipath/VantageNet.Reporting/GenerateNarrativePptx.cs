#nullable enable
using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using UiPath.CodedWorkflows;
using UiPath.Presentations.Activities.API;

namespace VantageNet.Reporting
{
    public class GenerateNarrativePptx : CodedWorkflow
    {
        [Workflow]
        public string Execute(string requestPath, string decisionPath)
        {
            var folder = Path.GetDirectoryName(Path.GetFullPath(requestPath))!;
            using var gate = new FileStream(Path.Combine(folder, "review.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            NarrativeState.Require(File.Exists(decisionPath), "Missing narrative approval.");
            var r = NarrativeState.CheckRequest(requestPath);
            var d = NarrativeState.CheckDecision(r, decisionPath);
            NarrativeState.Require(NarrativeState.Text(d, "decision") == "approve", "Narrative approval required; rejected/revision decisions cannot generate PPTX.");
            NarrativeState.CheckTerminal(folder);
            var hash = NarrativeState.FileHash(decisionPath);
            var attempt = Path.Combine(folder, "decisions", hash);
            NarrativeState.Require(File.Exists(Path.Combine(attempt, "result.json")) && File.Exists(Path.Combine(attempt, "decision.json")), "Resume narrative review before generating PPTX.");
            NarrativeState.Require(File.ReadAllBytes(decisionPath).SequenceEqual(File.ReadAllBytes(Path.Combine(attempt, "decision.json"))), "Approval archive differs from supplied decision.");
            var result = NarrativeState.Read(Path.Combine(attempt, "result.json"));
            NarrativeState.Require(NarrativeState.Text(result, "state") == "approve" && NarrativeState.Text(result, "decision_sha256") == hash && NarrativeState.Text(result, "snapshot_sha256") == NarrativeState.Text(r, "snapshot_sha256") && NarrativeState.Text(result, "approved_narrative_sha256") == MappingReview.Hash(NarrativeState.Text(d, "reviewed_narrative")), "Approval integrity mismatch.");
            foreach (var other in Directory.GetFiles(Path.Combine(folder, "decisions"), "decision.json", SearchOption.AllDirectories))
                NarrativeState.Require(Path.GetDirectoryName(other) == attempt || File.GetLastWriteTimeUtc(other) <= File.GetLastWriteTimeUtc(Path.Combine(attempt, "decision.json")), "Narrative approval was superseded.");
            var run = NarrativeState.Text(r, "run_id");
            var output = Path.Combine(folder, run + ".pptx");
            var receipt = Path.Combine(folder, "generation-receipt.json");
            if (File.Exists(receipt))
            {
                var prior = NarrativeState.Read(receipt);
                NarrativeState.Require(NarrativeState.Text(prior, "decision_sha256") == hash && NarrativeState.FileHash(output) == NarrativeState.Text(prior, "pptx_sha256"), "Final report/approval mismatch; reconcile manually.");
                return output;
            }
            NarrativeState.Require(!File.Exists(Path.Combine(folder, "generation-intent.json")) && !File.Exists(output), "Incomplete or uncertain generation; inspect retained artifacts, do not overwrite.");
            var s = NarrativeState.Read(Path.Combine(folder, "snapshot.json"));
            var backend = NarrativeState.Text(s, "origin") == "backend-confirmed-submission";
            var k = s["reading"]!;
            var text = NarrativeState.Text(d, "reviewed_narrative");
            NarrativeState.SaveNew(Path.Combine(folder, "generation-intent.json"), new JsonObject { ["decision_sha256"] = hash, ["snapshot_sha256"] = r["snapshot_sha256"]!.DeepClone(), ["template_sha256"] = r["template_sha256"]!.DeepClone() });
            var temporary = Path.Combine(folder, run + ".preparing.pptx");
            File.Copy(NarrativeState.Text(r, "template_path"), temporary);
            using (var ppt = powerpoint.UsePresentationDocument(temporary, false))
            {
                if (backend)
                    for (var slide = 1; slide <= 3; slide++)
                        ppt.AddTextToSlide(slide, "TestLabel", "PROVISIONAL REPORT | DISPOSABLE BACKEND", true);
                var scope = backend ? "One selected confirmed reading" : "one selected synthetic reading; not the 26-reading imported dataset";
                var statusLabel = backend ? "Target status" : "Fixture shortfall label";
                ppt.AddTextToSlide(1, "Scope", $"Period: {s["report_date"]} | Division: {s["division"]}\nRun: {run}\nSubmission: {s["submission_id"]}\nScope: {scope}", true);
                ppt.AddTextToSlide(1, "KPI", $"{k["kpi_name"]}\nFact ID: {k["fact_id"]} | Location: {k["location_name"]}\n{statusLabel}: {k["status"]}", true);
                var actual = k["actual_value"]!.GetValue<double>();
                var target = k["target_value"]!.GetValue<double>();
                NarrativeState.Require(double.IsFinite(actual) && double.IsFinite(target) && actual >= 0 && target > 0, "Provisional chart supports finite nonnegative values and positive target only.");
                var scale = Math.Max(actual, target);
                string Bar(double value) => new string('■', (int)Math.Round(34 * value / scale));
                ppt.AddTextToSlide(1, "Comparison", $"Actual {actual} {k["unit"]}\n{Bar(actual)}\nTarget {target} {k["unit"]}\n{Bar(target)}\nBars share a zero baseline and common scale", true);
                ppt.AddTextToSlide(2, "Narrative", text, true);
                ppt.AddTextToSlide(2, "Decision", $"Human-reviewed text; edits are not independently AI-validated.\nReviewer: {d["reviewer"]} | {d["decided_at"]}\nRationale: {d["reason"]}", true);
                ppt.AddTextToSlide(3, "Source", $"{k["source_file"]}, row {k["source_row"]}\n{ k["division"]} | {k["date"]} | {k["location_name"]}\nSnapshot SHA-256: {r["snapshot_sha256"]}\nApproval SHA-256: {hash}", true);
                var references = backend
                    ? string.Join("\n", s["narrative"]!["references"]!.AsArray().Select(reference => $"{reference!["id"]} · {reference["origin"]}")) + $"\nBundle revision: {s["bundle_binding"]!["revision"]}"
                    : s["narrative"]!["references"]!.ToJsonString() + "\nFeedback: " + s["feedback"]!.ToJsonString();
                ppt.AddTextToSlide(3, "References", references, true);
            }
            File.Move(temporary, output);
            NarrativeState.SaveNew(receipt, new JsonObject { ["decision_sha256"] = hash, ["snapshot_sha256"] = r["snapshot_sha256"]!.DeepClone(), ["template_sha256"] = r["template_sha256"]!.DeepClone(), ["pptx_sha256"] = NarrativeState.FileHash(output), ["state"] = "generated_local_only", ["output_path"] = output });
            return output;
        }
    }
}

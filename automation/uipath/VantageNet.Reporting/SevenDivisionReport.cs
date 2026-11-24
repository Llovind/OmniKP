#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;

namespace VantageNet.Reporting
{
    internal sealed partial class SevenDivisionRun
    {
        internal string ReportTemplate => Path.Combine(project, "Data", "seven-division-template.pptx");
        internal string ReportFolder => output;

        private string PrepareReport(List<JsonNode> completed, JsonNode? decision)
        {
            Directory.CreateDirectory(output);
            var bundlePath = Path.Combine(output, "aggregate-bundle.json");
            var intent = Path.Combine(output, "capture-intent.json");
            if (!File.Exists(intent))
            {
                Need(decision == null, "Prepare the aggregate review before submitting a decision.");
                var request = Node(new { submission_ids = completed.Select(row => S(row, "submission_id")), report_date = day,
                    bundle_id = bundleId, revision });
                WriteNew(intent, request);
                using var body = Body(request);
                RecordPost(Api + "aggregate-report", body, bundlePath, Path.Combine(output, "capture-error.json"));
            }
            if (!File.Exists(bundlePath))
            {
                Need(decision == null, "No narrative decision can be applied without a captured report.");
                return File.Exists(Path.Combine(output, "capture-error.json")) ? Path.Combine(output, "capture-error.json") : intent;
            }
            var bundle = Read(bundlePath);
            var reconciliationPath = Path.Combine(output, "reconciliation.json");
            if (!File.Exists(reconciliationPath)) VerifyReport(bundle, completed, reconciliationPath);
            else Need(S(Read(reconciliationPath), "bundle_sha256") == HashFile(bundlePath), "Aggregate bundle changed after reconciliation.");
            var narrative = bundle["narrative"]!;
            if (S(narrative, "evidence_status") == "provider_unavailable")
            {
                Need(decision == null, "A provider error cannot be approved as a narrative.");
                return bundlePath;
            }
            var requestPath = Path.Combine(output, "narrative-request.json");
            var binding = Node(new { kind = "narrative", run_id = runId, bundle_id = bundleId, revision, report_date = day,
                decision_mode = mode, identity, bundle_sha256 = HashFile(bundlePath), template_sha256 = HashFile(ReportTemplate) });
            if (!File.Exists(requestPath)) WriteNew(requestPath, binding);
            else Need(JsonNode.DeepEquals(Read(requestPath), binding), "Narrative request binding changed.");
            var hash = HashFile(requestPath);
            var approval = Path.Combine(output, "narrative-decision.json");
            if (decision != null)
            {
                CheckDecision(decision, hash);
                if (File.Exists(approval)) Need(JsonNode.DeepEquals(Read(approval), decision), "Narrative decision already recorded.");
                else WriteNew(approval, decision);
            }
            if (File.Exists(approval)) return approval;
            var form = Path.Combine(output, "narrative-review.html");
            RenderForm(form, Node(new { request = binding, request_sha256 = hash, bundle }));
            return form;
        }

        internal (JsonNode Bundle, JsonNode Decision, string RequestHash) ApprovedReport()
        {
            var requestPath = Path.Combine(output, "narrative-request.json");
            var request = Read(requestPath);
            var bundlePath = Path.Combine(output, "aggregate-bundle.json");
            Need(S(request, "bundle_sha256") == HashFile(bundlePath) &&
                S(request, "template_sha256") == HashFile(ReportTemplate) && S(request, "run_id") == runId &&
                S(request, "bundle_id") == bundleId && S(request, "revision") == revision && S(request, "decision_mode") == mode &&
                JsonNode.DeepEquals(request["identity"], identity), "Bundle, PowerPoint template or run binding changed after review.");
            var hash = HashFile(requestPath);
            var decision = Read(Path.Combine(output, "narrative-decision.json"));
            CheckDecision(decision, hash);
            Need(S(decision, "decision") == "approve", "Narrative was rejected. Final PowerPoint is blocked.");
            return (Read(bundlePath), decision, hash);
        }

        private void VerifyReport(JsonNode bundle, List<JsonNode> ledgers, string resultPath)
        {
            Need(S(bundle, "contract") == "vantagenet.aggregate-report" && N(bundle, "version") == 1 &&
                B(bundle, "synthetic") && S(bundle, "dataset") == "submitted" && JsonNode.DeepEquals(bundle["identity"], identity) &&
                S(bundle, "bundle_id") == bundleId && S(bundle, "revision") == revision && S(bundle, "report_date") == day,
                "Aggregate report scope does not match the run.");
            var submissions = Items(bundle["submissions"]!).ToDictionary(row => S(row, "submission_id"));
            Need(submissions.Count == 7 && ledgers.All(row => submissions.TryGetValue(S(row, "submission_id"), out var source) &&
                new[] { "division", "filename", "sheet_name", "report_date", "row_count", "fingerprint", "confirmed_at" }
                    .All(key => JsonNode.DeepEquals(row[key], source[key]))), "Aggregate submission provenance differs from the ledger.");
            var listed = Items(Get(Api + "submissions"));
            Need(listed.Select(row => S(row, "submission_id")).ToHashSet().SetEquals(submissions.Keys), "Disposable ledger contains submissions outside this batch.");
            var rows = Items(bundle["readings"]!).ToDictionary(row => N(row, "fact_id"));
            var confirmed = ledgers.SelectMany(row => Items(row["readings"]!)).ToDictionary(row => N(row, "fact_id"));
            Need(rows.Count == confirmed.Count && rows.All(pair => confirmed.TryGetValue(pair.Key, out var row) && JsonNode.DeepEquals(pair.Value, row)),
                "Aggregate readings differ from the confirmed submission details.");

            var query = "?dataset=submitted&date=" + day;
            var heatmap = Get(Api + "heatmap" + query);
            var heatmapRows = Items(heatmap["locations"]!).SelectMany(location => Items(location["kpis"]!)).ToArray();
            Need(S(heatmap, "date") == day && heatmapRows.Length == rows.Count && heatmapRows.All(item =>
                rows.TryGetValue(N(item, "fact_id"), out var row) && new[] { "actual_value", "target_value", "status", "source_file", "source_row" }
                    .All(key => JsonNode.DeepEquals(item[key], row[key]))) && heatmapRows.Select(row => N(row, "fact_id")).Distinct().Count() == rows.Count,
                "Aggregate readings differ from the dashboard heatmap.");
            var anomalies = Get(Api + "anomalies" + query);
            var gaps = Items(bundle["gaps"]!).Select(row => N(row, "fact_id")).ToArray();
            Need(S(anomalies, "date") == day && N(anomalies, "total_anomalies") == gaps.Length &&
                Items(anomalies["anomalies"]!).Select(row => N(row, "fact_id")).ToHashSet().SetEquals(gaps),
                "Aggregate shortfalls differ from the anomalies endpoint.");

            (string, string, string, string) Key(JsonNode row) => (S(row, "division"), S(row, "kpi_name"), S(row, "location_name"), S(row, "date"));
            var expected = Items(Read(referencePath)).ToDictionary(Key);
            var actual = rows.Values.ToDictionary(Key);
            var fields = new[] { "actual_value", "target_value", "unit", "higher_is_better", "status", "attainment_pct", "source_file", "source_row" };
            Need(expected.Count == actual.Count && expected.All(pair => actual.TryGetValue(pair.Key, out var row) &&
                fields.All(key => JsonNode.DeepEquals(pair.Value[key], row[key]))), "Aggregate readings differ from the independent synthetic reference.");
            var totals = bundle["totals"]!;
            Need(N(totals, "kpis") == divisions.Sum(division => division.Kpis) && N(totals, "readings") == expected.Count &&
                N(totals, "locations") == expected.Values.Select(row => S(row, "location_name")).Distinct().Count() &&
                N(totals, "meeting") == expected.Values.Count(row => S(row, "status") == "GREEN") &&
                N(totals, "below_target") == gaps.Length && N(totals, "target_unavailable") == 0,
                "Aggregate totals differ from the independent synthetic reference.");

            var narrative = bundle["narrative"]!;
            if (S(narrative, "evidence_status") == "ai_draft")
            {
                var fact = N(narrative, "fact_id");
                var evidence = Items(bundle["feedback"]!).Where(item => N(item, "fact_id") == fact).ToDictionary(item => N(item, "feedback_id"));
                var cited = Items(narrative["cited_feedback_ids"]!).Select(value => value.GetValue<int>()).ToArray();
                Need(gaps.Contains(fact) && B(narrative, "ai_invoked") && B(narrative["grounding"]!, "citation_verified") &&
                    cited.Length > 0 && cited.All(evidence.ContainsKey) && Items(narrative["evidence"]!).All(item =>
                        evidence.TryGetValue(N(item, "feedback_id"), out var source) && JsonNode.DeepEquals(item, source)),
                    "Narrative citations do not resolve to the exact gap reading.");
            }
            else Need(S(narrative, "evidence_status") is "insufficient_evidence" or "provider_unavailable", "Unsupported narrative status.");
            WriteNew(resultPath, Node(new { bundle_sha256 = HashFile(Path.Combine(output, "aggregate-bundle.json")),
                reference_sha256 = HashFile(referencePath), matched_readings = rows.Count, matched_submissions = submissions.Count,
                matched_heatmap_readings = heatmapRows.Length, matched_anomalies = gaps.Length, totals }));
        }
    }
}

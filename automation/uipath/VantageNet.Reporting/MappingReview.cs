#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public static class MappingReview
    {
        public static readonly string[] Fields = { "ignore", "kpi_name", "unit", "higher_is_better", "target_value", "location_name", "actual_value", "notes", "date", "kpi_archetype" };
        public static string Hash(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text))).ToLowerInvariant();
        private static void Save(string path, object data)
        {
            var tmp = path + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true }), new UTF8Encoding(false));
            File.Move(tmp, path, true);
        }

        public static string Run(string manifestPath, string baseUrl, string decisionPath)
        {
            var api = new Uri(baseUrl);
            if (api.Scheme != "http" || api.Host != "127.0.0.1" || api.AbsolutePath != "/" || api.Query != "" || api.Fragment != "" || api.UserInfo != "")
                throw new BusinessRuleException("Use an HTTP 127.0.0.1 disposable backend base URL.");
            var folder = Path.GetDirectoryName(Path.GetFullPath(manifestPath))!;
            // Serialize review operations and preserve all prior attempts.
            using var gate = new FileStream(Path.Combine(folder, "review.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            if (File.Exists(Path.Combine(folder, "confirm-journal.json")))
                throw new BusinessRuleException("Confirmation was attempted. Reconcile it before changing decisions.");
            var manifest = JsonNode.Parse(File.ReadAllText(manifestPath))!.AsObject();
            if (manifest["confirmed"]!.GetValue<bool>() || manifest["state"]!.GetValue<string>() != "awaiting_human_review")
                throw new BusinessRuleException("Only an unconfirmed preview awaiting human review may be reviewed.");
            var raw = File.ReadAllText(Path.Combine(folder, "preview.json"));
            var preview = JsonNode.Parse(raw)!.AsObject();
            var submission = preview["submission_id"]!.GetValue<string>();
            if (submission != manifest["submission_id"]!.GetValue<string>()) throw new BusinessRuleException("Submission mismatch.");
            var binding = Hash(raw);
            var requestFile = Path.Combine(folder, "review-request.json");
            if (!File.Exists(requestFile))
                Save(requestFile, new { run_id = manifest["run_id"]!.GetValue<string>(), submission_id = submission, preview_sha256 = binding, base_url = api.AbsoluteUri });
            var request = JsonNode.Parse(File.ReadAllText(requestFile))!;
            if (request["preview_sha256"]!.GetValue<string>() != binding || request["base_url"]!.GetValue<string>() != api.AbsoluteUri)
                throw new BusinessRuleException("Preview or backend changed since review preparation. Reconcile the run.");
            var htmlPath = Path.Combine(folder, "mapping-review.html");
            if (string.IsNullOrWhiteSpace(decisionPath))
            {
                var reviews = Path.Combine(folder, "reviews");
                var latest = Directory.Exists(reviews) ? Directory.EnumerateFiles(reviews, "decision.json", SearchOption.AllDirectories).OrderByDescending(File.GetLastWriteTimeUtc).FirstOrDefault() : null;
                JsonNode? latestReview = null, validatedPayload = null, approvalContext = null;
                if (latest != null)
                {
                    var priorRaw = File.ReadAllText(latest);
                    var priorDecision = JsonNode.Parse(priorRaw)!;
                    if (priorDecision["decision"]!.GetValue<string>() == "reject" || Directory.EnumerateFiles(reviews, "decision.json", SearchOption.AllDirectories).Any(f => JsonNode.Parse(File.ReadAllText(f))!["decision"]!.GetValue<string>() == "reject"))
                        throw new BusinessRuleException("This proposal was rejected; stage a new submission for reconsideration.");
                    var priorFolder = Path.GetDirectoryName(latest)!;
                    var resultPath = Path.Combine(priorFolder, "result.json");
                    if (!File.Exists(resultPath)) throw new BusinessRuleException("Incomplete prior review: reconcile before preparing another decision.");
                    var priorResult = JsonNode.Parse(File.ReadAllText(resultPath))!;
                    var responsePath = Path.Combine(priorFolder, "review-response.json");
                    latestReview = File.Exists(responsePath) ? JsonNode.Parse(File.ReadAllText(responsePath)) : null;
                    var state = priorResult["state"]!.GetValue<string>();
                    if (state == "correction_validated_needs_approval" || state == "mapping_approved_confirm_disabled")
                    {
                        if (Path.GetFileName(priorFolder) != Hash(priorRaw) || priorResult["decision_sha256"]!.GetValue<string>() != Hash(priorRaw) || priorResult["preview_sha256"]!.GetValue<string>() != binding || priorDecision["preview_sha256"]!.GetValue<string>() != binding || priorResult["submission_id"]!.GetValue<string>() != submission || priorDecision["submission_id"]!.GetValue<string>() != submission || priorDecision["run_id"]!.GetValue<string>() != request["run_id"]!.GetValue<string>() || priorResult["run_id"]!.GetValue<string>() != request["run_id"]!.GetValue<string>() || priorDecision["base_url"]!.GetValue<string>() != api.AbsoluteUri)
                            throw new BusinessRuleException("Stored review integrity mismatch; do not prepare approval.");
                        validatedPayload = JsonNode.Parse(File.ReadAllText(Path.Combine(priorFolder, "review-payload.json")))!;
                        var priorPayload = new JsonObject { ["mapping"] = priorDecision["mapping"]!.DeepClone(), ["default_direction"] = priorDecision["default_direction"]?.DeepClone() };
                        if (!JsonNode.DeepEquals(validatedPayload, priorPayload) || latestReview == null || !latestReview["can_confirm"]!.GetValue<bool>() || latestReview["issues"]!.AsArray().Count != 0 || latestReview["conflicts"]!.AsArray().Count != 0 || latestReview["conflict_count"]!.GetValue<int>() != 0 || priorResult["http_status"]!.GetValue<int>() != 200)
                            throw new BusinessRuleException("Stored mapping lacks a matching clean validation.");
                        using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false };
                        using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
                        var instance = JsonNode.Parse(client.GetStringAsync(new Uri(api, "_development/instance")).GetAwaiter().GetResult())!;
                        if (!instance["disposable"]!.GetValue<bool>() || string.IsNullOrWhiteSpace(instance["instance_id"]!.GetValue<string>()))
                            throw new BusinessRuleException("Approval preparation requires an identified disposable backend.");
                        approvalContext = new JsonObject { ["state"] = state, ["decision_sha256"] = Hash(priorRaw), ["payload_sha256"] = Hash(validatedPayload.ToJsonString()), ["backend_instance_id"] = instance["instance_id"]!.DeepClone(), ["base_url"] = api.AbsoluteUri, ["expected_readings"] = latestReview["valid_readings"]!.DeepClone() };
                    }
                }
                var data = JsonSerializer.Serialize(new { request, preview, manifest, fields = Fields, latest_review = latestReview, validated_payload = validatedPayload, approval_context = approvalContext });
                // System.Text.Json escapes HTML-sensitive characters, including closing script tags.
                var root = new DirectoryInfo(folder);
                while (root != null && !File.Exists(Path.Combine(root.FullName, "project.json"))) root = root.Parent;
                if (root == null) throw new BusinessRuleException("Run folder must be inside the existing UiPath project.");
                var template = File.ReadAllText(Path.Combine(root.FullName, "Data", "mapping-review.html"));
                File.WriteAllText(htmlPath, template.Replace("/*REVIEW_DATA*/null", data), new UTF8Encoding(false));
                return htmlPath;
            }
            var decisionRaw = File.ReadAllText(decisionPath);
            var d = JsonNode.Parse(decisionRaw)!.AsObject();
            if (d["submission_id"]!.GetValue<string>() != submission || d["run_id"]!.GetValue<string>() != request["run_id"]!.GetValue<string>() || d["preview_sha256"]!.GetValue<string>() != binding)
                throw new BusinessRuleException("Stale or cross-submission decision rejected.");
            var action = d["decision"]!.GetValue<string>();
            if (!new[] { "approve", "correct", "reject" }.Contains(action) || string.IsNullOrWhiteSpace(d["reviewer"]?.GetValue<string>()) || string.IsNullOrWhiteSpace(d["reason"]?.GetValue<string>()))
                throw new BusinessRuleException("Explicit decision, reviewer and rationale required.");
            var attempts = Path.Combine(folder, "reviews");
            Directory.CreateDirectory(attempts);
            var attempt = Path.Combine(attempts, Hash(decisionRaw));
            var resultFile = Path.Combine(attempt, "result.json");
            // A rejection is terminal for this proposal, even if an older approval is replayed.
            if (Directory.EnumerateFiles(attempts, "decision.json", SearchOption.AllDirectories).Any(f => Path.GetDirectoryName(f) != attempt && JsonNode.Parse(File.ReadAllText(f))!["decision"]!.GetValue<string>() == "reject"))
                throw new BusinessRuleException("This proposal was rejected; stage a new submission for reconsideration.");
            if (File.Exists(resultFile)) return resultFile; // exact replay never repeats HTTP
            if (Directory.Exists(attempt)) throw new BusinessRuleException("Incomplete prior attempt: inspect before retrying.");
            Directory.CreateDirectory(attempt);
            File.WriteAllText(Path.Combine(attempt, "decision.json"), decisionRaw, new UTF8Encoding(false));
            void Result(string state, int? status = null) => Save(resultFile, new { submission_id = submission, run_id = request["run_id"]!.GetValue<string>(), preview_sha256 = binding, decision_sha256 = Hash(decisionRaw), state, http_status = status, confirm_authorized = false, confirmed = false, updated_at = DateTime.UtcNow.ToString("O") });
            if (action == "reject") { Result("rejected"); return resultFile; }
            try
            {
                var mapping = d["mapping"]!.AsObject();
                var columns = preview["columns"]!.AsArray().Select(c => c!.GetValue<string>()).ToArray();
                if (mapping.Count != columns.Length || !columns.All(mapping.ContainsKey)) throw new BusinessRuleException("Mapping must contain every original column exactly once.");
                foreach (var pair in mapping)
                {
                    var field = pair.Value!.GetValue<string>();
                    if (!Fields.Contains(field) && !(field.StartsWith("location:", StringComparison.Ordinal) && field.Substring(9).Trim().Length is > 0 and <= 200))
                        throw new BusinessRuleException("Unsupported mapping target.");
                }
                var payload = new JsonObject { ["mapping"] = mapping.DeepClone(), ["default_direction"] = d["default_direction"]?.DeepClone() };
                Save(Path.Combine(attempt, "review-payload.json"), payload);
                using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false };
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };
                using var content = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json");
                using var response = client.PostAsync(new Uri(api, "api/v1/domains/1/submissions/" + Uri.EscapeDataString(submission) + "/review"), content).GetAwaiter().GetResult();
                var body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                if (!response.IsSuccessStatusCode) { Result("review_http_failed", (int)response.StatusCode); throw new HttpRequestException("Review endpoint rejected request. Inspect local backend."); }
                var result = JsonNode.Parse(body)!;
                var allowed = result["can_confirm"]!.GetValue<bool>() && result["issues"]!.AsArray().Count == 0 && result["conflicts"]!.AsArray().Count == 0 && result["conflict_count"]!.GetValue<int>() == 0;
                Save(Path.Combine(attempt, "review-response.json"), result);
                Result(!allowed ? "mapping_invalid" : action == "approve" ? "mapping_approved_confirm_disabled" : "correction_validated_needs_approval", (int)response.StatusCode);
                return resultFile;
            }
            catch
            {
                if (!File.Exists(resultFile)) Result("review_failed");
                throw;
            }
        }
    }
}

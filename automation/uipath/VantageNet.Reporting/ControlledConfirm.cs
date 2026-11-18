#nullable enable
using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json.Nodes;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public static class ControlledConfirm
    {
        private static JsonNode Read(string path) => JsonNode.Parse(File.ReadAllText(path))!;
        private static string Text(JsonNode n, string key) => n[key]!.GetValue<string>();
        private static void Require(bool condition, string message) { if (!condition) throw new BusinessRuleException(message); }
        private static bool Valid(JsonNode r) => r["can_confirm"]!.GetValue<bool>() && r["issues"]!.AsArray().Count == 0 && r["conflicts"]!.AsArray().Count == 0 && r["conflict_count"]!.GetValue<int>() == 0;
        private static void Save(string path, JsonNode data)
        {
            using (var file = new FileStream(path + ".tmp", FileMode.Create, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                var bytes = Encoding.UTF8.GetBytes(data.ToJsonString());
                file.Write(bytes, 0, bytes.Length);
                file.Flush(true);
            }
            File.Move(path + ".tmp", path, true);
        }

        public static string Run(string manifestPath, string baseUrl, string approvalPath)
        {
            var api = new Uri(baseUrl);
            Require(api.Scheme == "http" && api.Host == "127.0.0.1" && api.AbsolutePath == "/" && api.Query == "" && api.Fragment == "" && api.UserInfo == "", "Only a loopback disposable backend is allowed.");
            var folder = Path.GetDirectoryName(Path.GetFullPath(manifestPath))!;
            using var gate = new FileStream(Path.Combine(folder, "review.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var m = Read(manifestPath);
            var dRaw = File.ReadAllText(approvalPath);
            var d = JsonNode.Parse(dRaw)!;
            var request = Read(Path.Combine(folder, "review-request.json"));
            var previewRaw = File.ReadAllText(Path.Combine(folder, "preview.json"));
            var preview = JsonNode.Parse(previewRaw)!;
            var id = Text(m, "submission_id");
            var hash = MappingReview.Hash(dRaw);
            Require(Text(d, "decision") == "approve" && d["authorize_confirm"]!.GetValue<bool>() && !string.IsNullOrWhiteSpace(Text(d, "reviewer")) && !string.IsNullOrWhiteSpace(Text(d, "reason")), "Explicit human import authorization is missing.");
            Require(Text(m, "state") == "awaiting_human_review" && !m["confirmed"]!.GetValue<bool>(), "Intake is not eligible.");
            Require(Text(d, "submission_id") == id && Text(preview, "submission_id") == id && Text(request, "submission_id") == id && Text(d, "run_id") == Text(m, "run_id") && Text(request, "run_id") == Text(m, "run_id"), "Submission/run mismatch.");
            Require(Text(request, "base_url") == api.AbsoluteUri && Text(d, "preview_sha256") == MappingReview.Hash(previewRaw) && Text(request, "preview_sha256") == Text(d, "preview_sha256"), "Stale proposal or backend mismatch.");
            Require(Text(m, "division") == "ED" && Text(m, "report_date") == "2026-06-30" && Text(m, "sha256") == "8f35c686bb3f27521637787694d061660f657ac9a2a87ba4aeaedd77d9d3a498", "This controlled import supports only the pinned synthetic ED fixture.");
            var attempt = Path.Combine(folder, "reviews", hash);
            Require(File.ReadAllText(Path.Combine(attempt, "decision.json")) == dRaw, "Approval differs from reviewed decision.");
            foreach (var other in Directory.EnumerateFiles(Path.Combine(folder, "reviews"), "decision.json", SearchOption.AllDirectories))
                Require(Text(Read(other), "decision") != "reject" && (Path.GetDirectoryName(other) == attempt || File.GetLastWriteTimeUtc(other) <= File.GetLastWriteTimeUtc(Path.Combine(attempt, "decision.json"))), "Approval rejected or superseded by another decision.");
            var prior = Read(Path.Combine(attempt, "result.json"));
            Require(Text(prior, "state") == "mapping_approved_confirm_disabled" && Text(prior, "decision_sha256") == hash && Text(prior, "preview_sha256") == Text(d, "preview_sha256") && Text(prior, "submission_id") == id, "Successful matching review required.");
            Require(Valid(Read(Path.Combine(attempt, "review-response.json"))), "Prior review is invalid.");
            var payload = Read(Path.Combine(attempt, "review-payload.json"));
            var approvedPayload = new JsonObject { ["mapping"] = d["mapping"]!.DeepClone(), ["default_direction"] = d["default_direction"]?.DeepClone() };
            Require(JsonNode.DeepEquals(payload, approvedPayload), "Approved mapping differs from validated payload.");
            using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false };
            using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
            JsonNode Get(string path) => JsonNode.Parse(client.GetStringAsync(new Uri(api, path)).GetAwaiter().GetResult())!;
            var instance = Get("_development/instance");
            Require(instance["disposable"]!.GetValue<bool>() && Text(instance, "instance_id") == Text(d, "backend_instance_id"), "Disposable backend instance authorization mismatch.");
            var endpoint = "api/v1/domains/1/submissions/" + Uri.EscapeDataString(id);
            var journalPath = Path.Combine(folder, "confirm-journal.json");
            JsonNode journal = File.Exists(journalPath) ? Read(journalPath) : new JsonObject { ["submission_id"] = id, ["approval_sha256"] = hash, ["payload"] = payload.DeepClone(), ["backend_instance_id"] = Text(d, "backend_instance_id") };
            Require(Text(journal, "approval_sha256") == hash && Text(journal, "submission_id") == id && Text(journal, "backend_instance_id") == Text(d, "backend_instance_id") && JsonNode.DeepEquals(journal["payload"], payload), "Confirmation journal mismatch.");
            void State(string state) { journal["state"] = state; journal["updated_at"] = DateTime.UtcNow.ToString("O"); Save(journalPath, journal); }
            bool Verify()
            {
                var detail = Get(endpoint);
                Save(Path.Combine(folder, "confirm-ledger.json"), detail);
                if (Text(detail, "status") != "confirmed") return false;
                Require(Text(detail, "submission_id") == id && Text(detail, "division") == "ED" && Text(detail, "filename") == Text(m, "filename") && Text(detail, "report_date") == Text(m, "report_date") && JsonNode.DeepEquals(detail["mapping"], payload["mapping"]), "Confirmed ledger mapping/scope mismatch.");
                Require(Text(detail, "fingerprint") == "9ce70be76344f7839cb405c2053cd9e2b5ce750794ff53d84c61793903bd5b1c", "Backend source fingerprint does not match the ED fixture and metadata.");
                var rows = detail["readings"]!.AsArray();
                Require(rows.Count == 26 && rows.All(r => Text(r!, "submission_id") == id && Text(r!, "division") == "ED" && Text(r!, "source_file") == Text(m, "filename") && Text(r!, "date") == "2026-06-30" && r!["source_row"]!.GetValue<int>() > 4) && rows.Select(r => r!["fact_id"]!.GetValue<int>()).Distinct().Count() == 26, "Expected 26 ED readings with provenance.");
                State("verified_confirmed");
                return true;
            }
            // Once a journal exists, recovery is GET-only regardless of its last state.
            if (File.Exists(journalPath)) { Require(Verify(), "Prior write remains uncertain or conflicted. No POST retried; reconcile manually."); return journalPath; }
            var decided = DateTimeOffset.Parse(Text(d, "decided_at"), System.Globalization.CultureInfo.InvariantCulture);
            Require(decided >= DateTimeOffset.UtcNow.AddHours(-24) && decided <= DateTimeOffset.UtcNow.AddMinutes(5), "Approval expired or timestamp is in the future.");
            Require(!Verify(), "Submission is already confirmed.");
            using var reviewContent = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json");
            using var review = client.PostAsync(new Uri(api, endpoint + "/review"), reviewContent).GetAwaiter().GetResult();
            review.EnsureSuccessStatusCode();
            var fresh = JsonNode.Parse(review.Content.ReadAsStringAsync().GetAwaiter().GetResult())!;
            Save(Path.Combine(folder, "confirm-review.json"), fresh);
            Require(Valid(fresh), "Fresh review disallows confirmation.");
            Require(fresh["valid_readings"]!.GetValue<int>() == 26, "Fresh review must contain exactly 26 ED readings.");
            State("write_intent"); // durable BEFORE attempting a non-idempotent POST
            try
            {
                using var content = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json");
                using var response = client.PostAsync(new Uri(api, endpoint + "/confirm"), content).GetAwaiter().GetResult();
                journal["http_status"] = (int)response.StatusCode;
                if ((int)response.StatusCode == 409) { State("conflict_requires_reconciliation"); throw new BusinessRuleException("Confirm HTTP 409; do not retry."); }
                response.EnsureSuccessStatusCode();
                Save(Path.Combine(folder, "confirm-response.json"), JsonNode.Parse(response.Content.ReadAsStringAsync().GetAwaiter().GetResult())!);
                State("response_received_verification_pending");
                Require(Verify(), "Confirm response received but ledger is not confirmed.");
                return journalPath;
            }
            catch
            {
                if (Text(journal, "state") == "write_intent") State("uncertain_write");
                throw;
            }
        }
    }
}

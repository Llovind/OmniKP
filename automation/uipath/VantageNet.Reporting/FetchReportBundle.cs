#nullable enable
using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class FetchReportBundle : CodedWorkflow
    {
        [Workflow]
        public string Execute(string manifestPath, int factId, string revision = "v1")
        {
            var folder = Path.GetDirectoryName(Path.GetFullPath(manifestPath))!;
            using var gate = new FileStream(Path.Combine(folder, "review.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var manifest = NarrativeState.Read(manifestPath);
            var request = NarrativeState.Read(Path.Combine(folder, "review-request.json"));
            var journal = NarrativeState.Read(Path.Combine(folder, "confirm-journal.json"));
            var ledger = NarrativeState.Read(Path.Combine(folder, "confirm-ledger.json"));
            var submission = NarrativeState.Text(manifest, "submission_id");
            var instanceId = NarrativeState.Text(journal, "backend_instance_id");
            NarrativeState.Require(NarrativeState.Text(journal, "state") == "verified_confirmed" &&
                NarrativeState.Text(ledger, "status") == "confirmed" && new[] { request, journal, ledger }
                    .All(record => NarrativeState.Text(record, "submission_id") == submission), "A confirmed UiPath import is required.");
            var selected = ledger["readings"]!.AsArray().SingleOrDefault(row => row!["fact_id"]!.GetValue<int>() == factId);
            NarrativeState.Require(selected != null && NarrativeState.Text(selected, "status") == "RED",
                "Select a KPI shortfall from this confirmed import.");
            NarrativeState.Require(Regex.IsMatch(revision, "^v[1-9][0-9]{0,5}$"), "Invalid report revision.");
            NarrativeState.Require(Guid.TryParse(submission, out var submissionGuid), "Invalid submission ID.");
            var bundleId = $"ed-{submissionGuid:N}-{factId}";
            NarrativeState.Require(bundleId.Length <= 48, "Report bundle ID exceeds the supported length.");

            var api = new Uri(NarrativeState.Text(request, "base_url"));
            NarrativeState.Require(api.Scheme == "http" && api.Host == "127.0.0.1" && api.AbsolutePath == "/" &&
                api.Query == "" && api.Fragment == "" && api.UserInfo == "", "Only a loopback disposable backend is allowed.");
            using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false };
            using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
            var instance = JsonNode.Parse(client.GetStringAsync(new Uri(api, "_development/instance")).GetAwaiter().GetResult())!;
            NarrativeState.Require(instance["disposable"]!.GetValue<bool>() && instance["domain_id"]!.GetValue<int>() == 1 &&
                !string.IsNullOrWhiteSpace(instanceId) && NarrativeState.Text(instance, "instance_id") == instanceId, "Backend instance differs from the confirmed import.");

            var path = Path.Combine(folder, $"report-{factId}-{revision}.json");
            if (File.Exists(path)) return path;
            var payload = new JsonObject { ["submission_id"] = submission, ["fact_id"] = factId, ["bundle_id"] = bundleId, ["revision"] = revision };
            using var content = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json");
            using var response = client.PostAsync(new Uri(api, "api/v1/domains/1/report-bundles"), content).GetAwaiter().GetResult();
            response.EnsureSuccessStatusCode();
            var bundle = JsonNode.Parse(response.Content.ReadAsStringAsync().GetAwaiter().GetResult())!;
            var scope = bundle["scope"]!;
            var producer = bundle["producer"]!;
            NarrativeState.Require(NarrativeState.Text(scope, "submission_id") == submission &&
                NarrativeState.Text(scope, "fact_id") == factId.ToString(System.Globalization.CultureInfo.InvariantCulture) &&
                NarrativeState.Text(producer, "instance_id") == instanceId &&
                NarrativeState.Text(producer, "submission_fingerprint") == NarrativeState.Text(ledger, "fingerprint") &&
                NarrativeState.Text(bundle, "bundle_id") == bundleId && NarrativeState.Text(bundle, "revision") == revision,
                "The backend report does not match the confirmed reading and requested revision.");
            NarrativeState.SaveNew(path + ".preparing", bundle);
            File.Move(path + ".preparing", path);
            return path;
        }
    }
}

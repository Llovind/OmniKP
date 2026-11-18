#nullable enable
using System;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using System.Security.Cryptography;
using System.Linq;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public static class NarrativeState
    {
        public static JsonNode Read(string path) => JsonNode.Parse(File.ReadAllText(path))!;
        public static string Text(JsonNode n, string key) => n[key]!.GetValue<string>();
        public static string FileHash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
        public static void Require(bool ok, string reason) { if (!ok) throw new BusinessRuleException(reason); }
        public static void SaveNew(string path, JsonNode data)
        {
            using var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            var bytes = Encoding.UTF8.GetBytes(data.ToJsonString());
            file.Write(bytes, 0, bytes.Length);
            file.Flush(true);
        }
        public static JsonNode CheckRequest(string requestPath)
        {
            var r = Read(requestPath);
            var folder = Path.GetDirectoryName(Path.GetFullPath(requestPath))!;
            Require(FileHash(Text(r, "snapshot_path")) == Text(r, "snapshot_sha256") && FileHash(Path.Combine(folder, "snapshot.json")) == Text(r, "snapshot_sha256"), "Snapshot changed; prior narrative approval is stale.");
            Require(FileHash(Text(r, "template_path")) == Text(r, "template_sha256"), "Template changed; review again with a new run.");
            var snapshot = Read(Path.Combine(folder, "snapshot.json"));
            Require(MappingReview.Hash(Text(snapshot["narrative"]!, "draft")) == Text(r, "narrative_sha256"), "Narrative version mismatch.");
            return r;
        }
        public static JsonNode CheckDecision(JsonNode r, string decisionPath)
        {
            var d = Read(decisionPath);
            foreach (var key in new[] { "run_id", "submission_id", "snapshot_sha256", "narrative_sha256", "template_sha256" })
                Require(Text(r, key) == Text(d, key), "Stale or mismatched narrative decision: " + key);
            Require(!string.IsNullOrWhiteSpace(Text(d, "reviewer")) && !string.IsNullOrWhiteSpace(Text(d, "reason")), "Reviewer and rationale are required.");
            Require(Text(d, "reviewer").Length <= 60 && !Text(d, "reviewer").Contains('\n') && Text(d, "reason").Length <= 200 && !Text(d, "reason").Contains('\n'), "Provisional template requires reviewer <=60 and rationale <=200 characters on one line.");
            var at = DateTimeOffset.Parse(Text(d, "decided_at"), System.Globalization.CultureInfo.InvariantCulture);
            Require(at >= DateTimeOffset.UtcNow.AddHours(-24) && at <= DateTimeOffset.UtcNow.AddMinutes(5) && at >= DateTimeOffset.Parse(Text(r, "created_at")), "Narrative decision is expired or has an invalid timestamp.");
            var action = Text(d, "decision");
            Require(action == "approve" || action == "request_revision" || action == "reject", "Explicit narrative decision required.");
            var narrative = Text(d, "reviewed_narrative");
            Require(narrative.Trim().Length > 0 && narrative.Length <= 600 && narrative.Split('\n').Sum(line => Math.Max(1, (int)Math.Ceiling(line.Length / 60.0))) <= 10, "Reviewed narrative exceeds provisional template capacity: use 1–600 characters and at most 10 wrapped lines.");
            return d;
        }
        public static void CheckTerminal(string folder)
        {
            foreach (var path in Directory.GetFiles(folder, "result.json", SearchOption.AllDirectories))
            {
                var state = Text(Read(path), "state");
                Require(state != "reject" && state != "request_revision", "Narrative rejected or revision requested; prepare a new version/run.");
            }
        }
    }
}

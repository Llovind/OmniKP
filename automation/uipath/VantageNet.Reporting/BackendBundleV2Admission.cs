#nullable enable
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using static VantageNet.Reporting.BackendBundleV2Contract;

namespace VantageNet.Reporting
{
    internal sealed class BackendBundleV2Selection
    {
        internal Uri Origin { get; }
        internal int DomainId { get; }
        internal string InstanceId { get; }
        internal string Database { get; }
        internal string SubmissionId { get; }
        internal long FactId { get; }
        internal string BundleId { get; }
        internal string Revision { get; }

        internal BackendBundleV2Selection(string backendOrigin, int domainId, string instanceId, string database,
            string submissionId, long factId, string bundleId, string revision)
        {
            if (!Regex.IsMatch(backendOrigin, @"\Ahttp://127\.0\.0\.1:[1-9][0-9]{0,4}/?\z")
                || !Uri.TryCreate(backendOrigin, UriKind.Absolute, out var origin))
                throw new InvalidDataException("Use a pinned HTTP IPv4 loopback origin with explicit port.");
            Require(domainId == 1 && Regex.IsMatch(instanceId, @"\A[A-Za-z0-9_-]{8,80}\z")
                && !string.Equals(instanceId, "disposable-local-test", StringComparison.OrdinalIgnoreCase)
                && Regex.IsMatch(database, @"\Asqlite:disposable[-_][A-Za-z0-9_-]{1,64}\.db\z"),
                "Configure an explicit disposable instance ID, database label, and domain 1.");
            Require(Guid.TryParseExact(submissionId, "D", out _) && factId > 0, "Select an exact submission UUID and fact ID.");
            Require(Regex.IsMatch(bundleId, @"\A[A-Za-z0-9_-]{1,48}\z") && IsRevision(revision),
                "Invalid bundle ID or revision.");

            Origin = origin;
            DomainId = domainId;
            InstanceId = instanceId;
            Database = database;
            SubmissionId = submissionId;
            FactId = factId;
            BundleId = bundleId;
            Revision = revision;
        }

        internal static bool IsRevision(string revision) => Regex.IsMatch(revision, @"\Av[1-9][0-9]{0,5}\z");
        internal static int RevisionNumber(string revision) => int.Parse(revision.AsSpan(1), CultureInfo.InvariantCulture);
    }

    internal static class BackendBundleV2Admission
    {
        private const int MaxResponseBytes = 4 * 1024 * 1024;
        internal const string OutputNamespace = "BackendReportBundlesV2";

        internal static HttpClientHandler CreateTransport() => new HttpClientHandler
        {
            AllowAutoRedirect = false,
            UseProxy = false,
            UseCookies = false,
        };

        internal static async Task<string> FetchAndStage(HttpClient client, BackendBundleV2Selection selection,
            string projectFolder, CancellationToken cancellation)
        {
            projectFolder = Path.GetFullPath(projectFolder);
            RejectReparsePoint(projectFolder);
            var projectFile = Path.Combine(projectFolder, "project.json");
            RejectReparsePoint(projectFile);
            Require(Text(Parse(File.ReadAllBytes(projectFile)), "projectId") == "a5ddfe29-5288-4542-85a4-72e9a6156a5d",
                "Use the VantageNet.Reporting project folder.");
            var existingOutput = Path.Combine(projectFolder, "Output");
            var existingRoot = Path.Combine(existingOutput, OutputNamespace);
            var existingCase = Path.Combine(existingRoot, "case-" + selection.BundleId);
            foreach (var path in new[] { existingOutput, existingRoot, existingCase }) RejectReparsePoint(path);
            if (Directory.Exists(existingCase)) RequireCurrentRevision(selection, LatestRevision(existingCase));

            using var preflight = new HttpRequestMessage(HttpMethod.Get, new Uri(selection.Origin, "/_development/instance"));
            CheckInstance(Parse(await ReadResponse(client, preflight, cancellation).ConfigureAwait(false)), selection);
            var domain = "/api/v1/domains/" + selection.DomainId.ToString(CultureInfo.InvariantCulture);
            using var ledgerRequest = new HttpRequestMessage(HttpMethod.Get,
                new Uri(selection.Origin, domain + "/submissions/" + selection.SubmissionId));
            var ledger = CheckLedger(Parse(await ReadResponse(client, ledgerRequest, cancellation).ConfigureAwait(false)), selection);

            using var request = new HttpRequestMessage(HttpMethod.Post, new Uri(selection.Origin, domain + "/report-bundles"));
            request.Content = new StringContent(JsonSerializer.Serialize(new
            {
                submission_id = selection.SubmissionId,
                fact_id = selection.FactId,
                bundle_id = selection.BundleId,
                revision = selection.Revision,
            }), Encoding.UTF8, "application/json");
            var bytes = await ReadResponse(client, request, cancellation).ConfigureAwait(false);
            var bundle = Parse(bytes);
            var status = Validate(bundle, selection, ledger);
            return Stage(projectFolder, selection, ledger, bundle, bytes, status);
        }

        private static async Task<byte[]> ReadResponse(HttpClient client, HttpRequestMessage request,
            CancellationToken cancellation)
        {
            using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellation).ConfigureAwait(false);
            Require(response.IsSuccessStatusCode, "Pinned backend request failed with HTTP " + (int)response.StatusCode + ".");
            Require(response.Content.Headers.ContentType?.MediaType == "application/json", "Pinned backend must return JSON.");
            Require(response.Content.Headers.ContentLength is null or <= MaxResponseBytes, "Pinned backend response exceeds the size limit.");
            using var stream = await response.Content.ReadAsStreamAsync(cancellation).ConfigureAwait(false);
            using var result = new MemoryStream();
            var chunk = new byte[8192];
            int count;
            while ((count = await stream.ReadAsync(chunk.AsMemory(), cancellation).ConfigureAwait(false)) > 0)
            {
                Require(result.Length + count <= MaxResponseBytes, "Pinned backend response exceeds the size limit.");
                result.Write(chunk, 0, count);
            }
            return result.ToArray();
        }

        private static string Stage(string projectFolder, BackendBundleV2Selection selection, BackendBundleV2Ledger ledger,
            JsonElement bundle, byte[] bytes, string status)
        {
            var snapshot = Field(bundle, "snapshot");
            var producer = Field(bundle, "producer");
            var binding = new JsonObject
            {
                ["contract"] = Name, ["schema_version"] = 2,
                ["bundle_id"] = selection.BundleId, ["revision"] = selection.Revision,
                ["backend_origin"] = selection.Origin.AbsoluteUri, ["backend_database"] = selection.Database,
                ["producer_instance_id"] = selection.InstanceId, ["domain_id"] = selection.DomainId,
                ["submission_id"] = selection.SubmissionId, ["submission_fingerprint"] = ledger.Fingerprint,
                ["fact_id"] = selection.FactId.ToString(CultureInfo.InvariantCulture),
                ["captured_at"] = Text(producer, "captured_at"), ["reading_sha256"] = Text(producer, "reading_sha256"),
                ["bundle_sha256"] = BackendBundleV2Digest.Sha256(bytes),
            };
            var ready = status == "draft_ready";
            byte[]? stagedSnapshot = null;
            if (ready)
            {
                var snapshotObject = JsonNode.Parse(snapshot.GetRawText())!.AsObject();
                snapshotObject["bundle_binding"] = binding.DeepClone();
                stagedSnapshot = JsonSerializer.SerializeToUtf8Bytes(snapshotObject);
            }
            var narrative = Field(snapshot, "narrative");
            var state = new JsonObject
            {
                ["run_id"] = Text(snapshot, "run_id"),
                ["state"] = ready ? "eligible_for_narrative_review" : "blocked_" + status,
                ["eligible_for_review"] = ready, ["evidence_status"] = status,
                ["provider_status"] = Text(narrative, "provider_status"),
                ["provider_error_code"] = JsonNode.Parse(Field(narrative, "provider_error_code").GetRawText()),
                ["ai_invoked"] = Boolean(bundle, "ai_invoked"),
                ["live_provider_verified"] = false, ["notification_delivery"] = "disabled",
                ["snapshot_sha256"] = stagedSnapshot is null ? null : BackendBundleV2Digest.Sha256(stagedSnapshot),
                ["binding"] = binding,
            };
            var stateBytes = JsonSerializer.SerializeToUtf8Bytes(state);

            var output = CreateSafeDirectory(projectFolder, "Output");
            var root = CreateSafeDirectory(output, OutputNamespace);
            var reportCase = CreateSafeDirectory(root, "case-" + selection.BundleId);
            var lockPath = Path.Combine(reportCase, ".admission.lock");
            RejectReparsePoint(lockPath);
            using var gate = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var latest = LatestRevision(reportCase);
            RequireCurrentRevision(selection, latest);
            var folder = Path.Combine(reportCase, selection.Revision);
            var statePath = Path.Combine(folder, "state.json");
            if (latest is not null)
            {
                var priorFolder = Path.Combine(reportCase, latest);
                var prior = CheckPublished(priorFolder);
                var priorBinding = Field(prior, "binding");
                foreach (var key in new[] { "bundle_id", "backend_origin", "backend_database", "producer_instance_id",
                    "submission_id", "submission_fingerprint", "fact_id" })
                    Require(Text(priorBinding, key) == binding[key]!.GetValue<string>(), "Report case is pinned to a different reading or producer.");
                Require(Integer(priorBinding, "domain_id") == selection.DomainId
                    && Text(priorBinding, "revision") == latest, "Staged report identity mismatch.");
                if (latest == selection.Revision)
                {
                    Require(File.ReadAllBytes(Path.Combine(folder, "bundle.json")).SequenceEqual(bytes),
                        "Bundle revision already exists with different bytes.");
                    Require(File.ReadAllBytes(statePath).SequenceEqual(stateBytes),
                        "Stored admission state differs from validated replay.");
                    return statePath;
                }
            }

            var staging = Path.Combine(reportCase, ".preparing-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(staging);
            try
            {
                WriteNew(Path.Combine(staging, "bundle.json"), bytes);
                if (stagedSnapshot is not null) WriteNew(Path.Combine(staging, "snapshot.json"), stagedSnapshot);
                WriteNew(Path.Combine(staging, "state.json"), stateBytes);
                Directory.Move(staging, folder);
            }
            finally
            {
                // Only this call's unpublished directory may be removed.
                if (Directory.Exists(staging))
                {
                    foreach (var name in new[] { "bundle.json", "snapshot.json", "state.json" })
                        File.Delete(Path.Combine(staging, name));
                    Directory.Delete(staging);
                }
            }
            return statePath;
        }

        private static string? LatestRevision(string reportCase) => Directory.EnumerateDirectories(reportCase)
            .Select(Path.GetFileName).OfType<string>().Where(BackendBundleV2Selection.IsRevision)
            .OrderByDescending(BackendBundleV2Selection.RevisionNumber).FirstOrDefault();

        private static void RequireCurrentRevision(BackendBundleV2Selection selection, string? latest) =>
            Require(latest is null || BackendBundleV2Selection.RevisionNumber(selection.Revision)
                >= BackendBundleV2Selection.RevisionNumber(latest), "Bundle revision has been superseded.");

        private static JsonElement CheckPublished(string folder)
        {
            RejectReparsePoint(folder);
            var state = Parse(ReadSafeFile(Path.Combine(folder, "state.json")));
            var bundleHash = Text(Field(state, "binding"), "bundle_sha256");
            Require(bundleHash == BackendBundleV2Digest.Sha256(ReadSafeFile(Path.Combine(folder, "bundle.json"))),
                "Staged bundle changed.");
            var snapshot = Path.Combine(folder, "snapshot.json");
            if (Boolean(state, "eligible_for_review"))
                Require(Text(state, "snapshot_sha256") == BackendBundleV2Digest.Sha256(ReadSafeFile(snapshot)),
                    "Staged snapshot changed.");
            else
                Require(!File.Exists(snapshot) && !Directory.Exists(snapshot)
                    && Field(state, "snapshot_sha256").ValueKind == JsonValueKind.Null, "Blocked admission contains a snapshot.");
            return state;
        }

        private static byte[] ReadSafeFile(string path)
        {
            RejectReparsePoint(path);
            return File.ReadAllBytes(path);
        }

        private static string CreateSafeDirectory(string parent, string name)
        {
            var path = Path.Combine(parent, name);
            RejectReparsePoint(path);
            Directory.CreateDirectory(path);
            return path;
        }

        private static void RejectReparsePoint(string path)
        {
            try
            {
                Require((File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0, "Reparse points are not allowed in admission paths.");
            }
            catch (FileNotFoundException) { }
            catch (DirectoryNotFoundException) { }
        }

        private static void WriteNew(string path, byte[] bytes)
        {
            using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            stream.Write(bytes);
            stream.Flush(true);
        }
    }
}

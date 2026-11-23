#nullable enable
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using static VantageNet.Reporting.BackendBundleV2Contract;

namespace VantageNet.Reporting
{
    internal sealed class BackendNarrativeV2 : IDisposable
    {
        private const string ReportTemplate = "provisional-report-template.pptx";
        private const string FormTemplate = "backend-narrative-review-v2.html";
        private const string ReviewNamespace = "BackendNarrativeReviewV2";
        private static readonly UTF8Encoding Utf8 = new(false, true);
        private readonly FileStream gate;
        internal JsonElement Snapshot { get; }
        internal JsonElement Reading => Field(Snapshot, "reading");
        internal JsonElement Narrative => Field(Snapshot, "narrative");
        internal JsonObject Binding { get; }
        internal byte[] TemplateBytes { get; }
        internal string Folder { get; }
        private string Form { get; }
        private string RequestPath => Path.Combine(Folder, "request.json");
        private string DecisionFolder => Path.Combine(Folder, "decision");

        internal BackendNarrativeV2(string projectFolder, string bundleId, string revision)
        {
            Require(Regex.IsMatch(bundleId, @"\A[A-Za-z0-9_-]{1,48}\z") && BackendBundleV2Selection.IsRevision(revision),
                "Invalid case or revision.");
            var project = Path.GetFullPath(projectFolder);
            Require(Text(Parse(Read(Path.Combine(project, "project.json"))), "projectId") == "a5ddfe29-5288-4542-85a4-72e9a6156a5d",
                "Expected the VantageNet.Reporting project folder.");
            var output = Path.Combine(project, "Output");
            var caseName = "case-" + bundleId;
            var admissionCase = Path.Combine(output, BackendBundleV2Admission.OutputNamespace, caseName);
            var lockPath = Path.Combine(admissionCase, ".admission.lock");
            SafePath(lockPath);
            Require(File.Exists(lockPath), "Missing staged admission case.");
            gate = new FileStream(lockPath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            try
            {
                var active = Directory.EnumerateDirectories(admissionCase).Select(Path.GetFileName).OfType<string>()
                    .Where(BackendBundleV2Selection.IsRevision).OrderByDescending(BackendBundleV2Selection.RevisionNumber)
                    .FirstOrDefault();
                Require(active == revision, "Requested revision is missing or superseded.");
                var staged = Path.Combine(admissionCase, revision);
                var stateBytes = Read(Path.Combine(staged, "state.json"));
                var state = Parse(stateBytes);
                var admitted = Field(state, "binding");
                Require(Text(admitted, "bundle_id") == bundleId && Text(admitted, "revision") == revision
                    && Text(state, "run_id") == bundleId + "-" + revision, "Staged case or revision identity mismatch.");
                Require(Boolean(state, "eligible_for_review") && Text(state, "state") == "eligible_for_narrative_review"
                    && Text(state, "evidence_status") == "draft_ready", "Admission is blocked or ineligible for narrative review.");
                var bundleHash = Text(admitted, "bundle_sha256");
                var snapshotHash = Text(state, "snapshot_sha256");
                var bundleBytes = ReadVerified(Path.Combine(staged, "bundle.json"), bundleHash, "Staged bundle hash mismatch.");
                var snapshotBytes = ReadVerified(Path.Combine(staged, "snapshot.json"), snapshotHash, "Staged snapshot hash mismatch.");
                var bundle = Parse(bundleBytes);
                Snapshot = Parse(snapshotBytes);
                CheckAdmission(state, admitted, bundle, bundleId, revision);

                var data = Path.Combine(project, "Data");
                TemplateBytes = Read(Path.Combine(data, ReportTemplate));
                var templateHash = BackendBundleV2Digest.Sha256(TemplateBytes);
                Require(templateHash == "ca657e395364e44fc731e1803aedf3a828ad2fa6d2ca996a06c1ecd1127eb0a8", "Report template changed or is unsupported.");
                var formBytes = Read(Path.Combine(data, FormTemplate));
                var syntheticFeedback = ContainsSyntheticOperatorFeedback(Snapshot);
                var form = Utf8.GetString(formBytes);
                Form = syntheticFeedback ? MarkSyntheticOperatorFeedback(form) : form;
                Folder = Path.Combine(output, ReviewNamespace, caseName, revision);
                SafePath(Folder);
                Binding = new JsonObject
                {
                    ["bundle_id"] = bundleId, ["revision"] = revision, ["run_id"] = Text(state, "run_id"),
                    ["submission_id"] = Text(admitted, "submission_id"), ["fact_id"] = Text(admitted, "fact_id"),
                    ["bundle_sha256"] = bundleHash, ["snapshot_sha256"] = snapshotHash,
                    ["admission_state_sha256"] = BackendBundleV2Digest.Sha256(stateBytes),
                    ["narrative_sha256"] = HashText(Text(Narrative, "draft")),
                    ["template_id"] = ReportTemplate, ["template_sha256"] = templateHash,
                    ["review_form_id"] = FormTemplate, ["review_form_sha256"] = BackendBundleV2Digest.Sha256(syntheticFeedback ? Utf8.GetBytes(Form) : formBytes),
                };
                if (syntheticFeedback)
                    Binding["scenario_label"] = OperatorFeedbackAcceptance.SyntheticLabel;
            }
            catch
            {
                gate.Dispose();
                throw;
            }
        }

        internal static bool ContainsSyntheticOperatorFeedback(JsonElement snapshot) =>
            Field(Field(snapshot, "feedback"), "records").EnumerateArray().Any(record =>
                Text(record, "origin") == "operator-api"
                && Text(record, "explanation").StartsWith(
                    OperatorFeedbackAcceptance.SyntheticLabel + " —", StringComparison.Ordinal));

        internal static string MarkSyntheticOperatorFeedback(string html)
        {
            const string heading = "<h1>Review backend report narrative</h1>";
            Require(html.Contains(heading, StringComparison.Ordinal), "Synthetic feedback review heading is missing.");
            return html.Replace(heading, heading + "\n<p><strong>" + OperatorFeedbackAcceptance.SyntheticLabel
                + "</strong> · This review includes hypothetical acceptance feedback.</p>", StringComparison.Ordinal);
        }

        public void Dispose() => gate.Dispose();

        private void CheckAdmission(JsonElement state, JsonElement binding, JsonElement bundle, string bundleId, string revision)
        {
            Require(Text(binding, "contract") == Name && Integer(binding, "schema_version") == 2
                && Integer(binding, "domain_id") == 1
                && Text(bundle, "contract") == Name && Integer(bundle, "schema_version") == 2
                && Text(bundle, "source_kind") == "backend-read-bundle" && Text(bundle, "dataset") == "submitted"
                && Text(bundle, "bundle_id") == bundleId && Text(bundle, "revision") == revision
                && Text(bundle, "evidence_status") == "draft_ready", "Invalid admitted backend bundle identity.");
            var producer = Field(bundle, "producer");
            Require(Boolean(producer, "disposable") && Integer(producer, "domain_id") == 1
                && Text(producer, "instance_id") == Text(binding, "producer_instance_id")
                && Text(producer, "captured_at") == Text(binding, "captured_at")
                && Text(producer, "submission_fingerprint") == Text(binding, "submission_fingerprint")
                && Text(producer, "reading_sha256") == Text(binding, "reading_sha256"), "Admitted producer binding mismatch.");
            // Recheck the shape of the persisted intake pins without calling the backend.
            Require(long.TryParse(Text(binding, "fact_id"), NumberStyles.None, CultureInfo.InvariantCulture, out var factId),
                "Invalid admitted fact ID.");
            _ = new BackendBundleV2Selection(Text(binding, "backend_origin"), 1, Text(binding, "producer_instance_id"),
                Text(binding, "backend_database"), Text(binding, "submission_id"), factId, bundleId, revision);

            Require(JsonElement.DeepEquals(Field(Snapshot, "bundle_binding"), binding), "Staged snapshot binding mismatch.");
            var original = JsonNode.Parse(Snapshot.GetRawText())!.AsObject();
            original.Remove("bundle_binding");
            Require(JsonElement.DeepEquals(JsonSerializer.SerializeToElement(original), Field(bundle, "snapshot")),
                "Staged snapshot differs from the archived bundle.");
            var scope = Field(bundle, "scope");
            var fact = Text(binding, "fact_id");
            Require(Integer(Snapshot, "schema_version") == 2 && Text(Snapshot, "origin") == "backend-confirmed-submission"
                && Text(Snapshot, "run_id") == Text(state, "run_id")
                && Text(Snapshot, "submission_id") == Text(binding, "submission_id")
                && Text(scope, "submission_id") == Text(binding, "submission_id")
                && Text(scope, "fact_id") == fact && Text(Reading, "fact_id") == fact
                && Text(Field(Snapshot, "feedback"), "fact_id") == fact
                && Text(scope, "division") == Text(Snapshot, "division") && Text(scope, "division") == Text(Reading, "division")
                && Text(scope, "report_date") == Text(Snapshot, "report_date") && Text(scope, "report_date") == Text(Reading, "date"),
                "Admitted submission, fact, or scope mismatch.");
            var digest = BackendBundleV2Digest.Reading(Text(binding, "submission_fingerprint"), Reading,
                Field(Field(Snapshot, "feedback"), "records"));
            Require(digest == Text(binding, "reading_sha256"), "Admitted reading digest mismatch.");
            var grounding = Field(Narrative, "grounding");
            Require(Boolean(bundle, "ai_invoked") && Boolean(state, "ai_invoked") && Boolean(Narrative, "ai_invoked")
                && Text(state, "provider_status") == "response_accepted" && Text(Narrative, "provider_status") == "response_accepted"
                && Field(state, "provider_error_code").ValueKind == JsonValueKind.Null
                && Field(Narrative, "provider_error_code").ValueKind == JsonValueKind.Null
                && Text(Narrative, "origin") == "live-provider-rca" && Text(Narrative, "backend_evidence_status") == "ai_draft"
                && Boolean(grounding, "structural_check") && Boolean(grounding, "citation_verified")
                && !string.IsNullOrWhiteSpace(Text(Narrative, "draft")) && !Boolean(state, "live_provider_verified")
                && Text(state, "notification_delivery") == "disabled", "Invalid eligible provider outcome.");
        }

        internal string Prepare()
        {
            var htmlPath = Path.Combine(Folder, "narrative-review.html");
            if (Directory.Exists(Folder))
            {
                _ = ReadRequest();
                Require(!Directory.Exists(DecisionFolder) && !File.Exists(Path.Combine(Folder, "generation-intent.json")),
                    "Review has a terminal decision or generation attempt.");
                return htmlPath;
            }

            var request = new JsonObject
            {
                ["binding"] = Binding.DeepClone(), ["request_id"] = Guid.NewGuid().ToString("D"),
                ["created_at"] = DateTimeOffset.UtcNow.ToString("O"),
            };
            var pending = Folder + ".preparing";
            CreatePending(pending);
            var requestBytes = JsonSerializer.SerializeToUtf8Bytes(request);
            Write(Path.Combine(pending, "request.json"), requestBytes);
            Write(Path.Combine(pending, "narrative-review.html"), RenderForm(Parse(requestBytes), BackendBundleV2Digest.Sha256(requestBytes)));
            Directory.Move(pending, Folder);
            return htmlPath;
        }

        private byte[] RenderForm(JsonElement request, string requestHash)
        {
            const string marker = "/*BACKEND_V2_REVIEW_DATA*/null";
            Require(Form.Contains(marker, StringComparison.Ordinal), "Review form template marker missing.");
            // Default encoder escapes HTML-significant characters before inserting JSON in a script.
            return Utf8.GetBytes(Form.Replace(marker, JsonSerializer.Serialize(new { request, request_sha256 = requestHash, snapshot = Snapshot }), StringComparison.Ordinal));
        }

        internal string Record(string decisionPath)
        {
            var (request, requestHash) = ReadRequest();
            var bytes = Read(Path.GetFullPath(decisionPath));
            var decision = CheckDecision(Parse(bytes), request, requestHash);
            var receipt = Path.Combine(DecisionFolder, "result.json");
            if (Directory.Exists(DecisionFolder))
            {
                _ = ReadDecision(request, requestHash);
                Require(Read(Path.Combine(DecisionFolder, "decision.json")).SequenceEqual(bytes),
                    "A terminal decision already exists for this revision.");
                return receipt;
            }
            Require(!File.Exists(Path.Combine(Folder, "generation-intent.json")), "Generation has already been attempted.");
            var pending = DecisionFolder + ".preparing";
            CreatePending(pending);
            Write(Path.Combine(pending, "decision.json"), bytes);
            NarrativeState.SaveNew(Path.Combine(pending, "result.json"), new JsonObject
            {
                ["binding"] = Binding.DeepClone(), ["request_sha256"] = requestHash, ["decision"] = Text(decision, "decision"),
                ["decision_sha256"] = BackendBundleV2Digest.Sha256(bytes),
                ["reviewed_narrative_sha256"] = Text(decision, "reviewed_narrative_sha256"),
            });
            Directory.Move(pending, DecisionFolder);
            return receipt;
        }

        internal (JsonElement Decision, string DecisionHash, string RequestHash) Approved()
        {
            var (request, hash) = ReadRequest();
            var (decision, decisionHash) = ReadDecision(request, hash);
            Require(Text(decision, "decision") == "approve", "Explicit approval is required; this revision was rejected or returned for revision.");
            return (decision, decisionHash, hash);
        }

        private (JsonElement Request, string Hash) ReadRequest()
        {
            var bytes = Read(RequestPath);
            var request = Parse(bytes);
            Require(JsonElement.DeepEquals(Field(request, "binding"), JsonSerializer.SerializeToElement(Binding)),
                "Review request binding changed.");
            Require(Guid.TryParseExact(Text(request, "request_id"), "D", out _), "Invalid review request identity.");
            _ = Timestamp(request, "created_at");
            var hash = BackendBundleV2Digest.Sha256(bytes);
            Require(Read(Path.Combine(Folder, "narrative-review.html")).SequenceEqual(RenderForm(request, hash)), "Prepared review form changed.");
            return (request, hash);
        }

        private (JsonElement Decision, string Hash) ReadDecision(JsonElement request, string requestHash)
        {
            Require(Directory.Exists(DecisionFolder), "Missing recorded narrative decision.");
            var bytes = Read(Path.Combine(DecisionFolder, "decision.json"));
            var hash = BackendBundleV2Digest.Sha256(bytes);
            var result = Parse(Read(Path.Combine(DecisionFolder, "result.json")));
            Require(Text(result, "decision_sha256") == hash, "Archived decision hash changed.");
            var decision = CheckDecision(Parse(bytes), request, requestHash);
            Require(Text(result, "request_sha256") == requestHash
                && JsonElement.DeepEquals(Field(result, "binding"), Field(request, "binding"))
                && Text(result, "decision") == Text(decision, "decision")
                && Text(result, "reviewed_narrative_sha256") == Text(decision, "reviewed_narrative_sha256"),
                "Recorded approval receipt binding changed.");
            return (decision, hash);
        }

        private JsonElement CheckDecision(JsonElement decision, JsonElement request, string requestHash)
        {
            Require(JsonElement.DeepEquals(Field(decision, "binding"), Field(request, "binding"))
                && Text(decision, "request_id") == Text(request, "request_id")
                && Text(decision, "request_sha256") == requestHash, "Decision belongs to a different review request or revision.");
            var action = Text(decision, "decision");
            Require(action is "approve" or "reject" or "request_revision", "Explicit narrative decision required.");
            var reviewer = Text(decision, "reviewer");
            Require(reviewer.Length is > 0 and <= 60 && reviewer == reviewer.Trim()
                && reviewer.Any(char.IsLetterOrDigit) && !reviewer.Any(char.IsControl), "Valid reviewer identity is required.");
            var reason = Text(decision, "reason");
            Require(reason.Length is > 0 and <= 120 && !string.IsNullOrWhiteSpace(reason) && !reason.Any(char.IsControl),
                "A one-line decision reason of up to 120 characters is required.");
            var time = Timestamp(decision, "decided_at");
            var now = DateTimeOffset.UtcNow;
            Require(time >= Timestamp(request, "created_at") && time >= now.AddHours(-24) && time <= now.AddMinutes(5),
                "Decision has expired or its timestamp is invalid.");
            var narrative = Text(decision, "reviewed_narrative");
            Require(HashText(narrative) == Text(decision, "reviewed_narrative_sha256"), "Reviewed narrative hash mismatch.");
            if (action == "approve")
                Require(!string.IsNullOrWhiteSpace(narrative) && narrative.Length <= 600
                    && Fits(narrative, 52, 9), "Approved narrative exceeds provisional template capacity or contains unsupported controls.");
            return decision;
        }

        internal static bool Fits(string text, int width, int rows) =>
            !text.Any(ch => char.IsControl(ch) && ch != '\n')
            && text.Split('\n').Sum(line => Math.Max(1, (line.Length + width - 1) / width)) <= rows;

        private static DateTimeOffset Timestamp(JsonElement value, string field)
        {
            var text = Text(value, field);
            if (Regex.IsMatch(text, @"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,7})?(Z|\+00:00)\z")
                && DateTimeOffset.TryParse(text, CultureInfo.InvariantCulture, DateTimeStyles.None, out var timestamp)) return timestamp;
            throw new InvalidDataException("Invalid UTC review timestamp.");
        }

        private static string HashText(string text) => BackendBundleV2Digest.Sha256(Utf8.GetBytes(text));

        private static byte[] ReadVerified(string path, string expected, string error)
        {
            var bytes = Read(path);
            Require(IsHash(expected) && BackendBundleV2Digest.Sha256(bytes) == expected, error);
            return bytes;
        }

        internal static byte[] Read(string path)
        {
            SafePath(path);
            Require(File.Exists(path), "Missing required file: " + Path.GetFileName(path));
            return File.ReadAllBytes(path);
        }

        internal static void CreatePending(string path)
        {
            SafePath(path);
            Require(!Directory.Exists(path) && !File.Exists(path), "Incomplete local operation; preserve its files and reconcile.");
            Directory.CreateDirectory(path);
        }

        internal static void Write(string path, byte[] bytes)
        {
            SafePath(path);
            using var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            file.Write(bytes);
            file.Flush(true);
        }

        internal static void SafePath(string path)
        {
            for (var part = Path.GetFullPath(path); part is not null; part = Path.GetDirectoryName(part))
            {
                try
                {
                    Require((File.GetAttributes(part) & FileAttributes.ReparsePoint) == 0, "Reparse points are not allowed in review paths.");
                }
                catch (FileNotFoundException) { }
                catch (DirectoryNotFoundException) { }
            }
        }
    }
}

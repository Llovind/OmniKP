#nullable enable
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using static VantageNet.Reporting.BackendBundleV2Contract;
using static VantageNet.Reporting.BackendBundleV2Digest;

namespace VantageNet.Reporting
{
    internal static class OperatorFeedbackAcceptance
    {
        internal const string SyntheticLabel = "SYNTHETIC ACCEPTANCE SCENARIO";
        private const string Explanation = SyntheticLabel + " — This is hypothetical test input, not a verified operational observation.\n\n"
            + "The Demo South deployment count is below its reporting target. For this test scenario, assume that several planned deployment activities are awaiting site-access coordination.";
        private const string CorrectiveAction = "Review the pending deployment list, identify activities awaiting access approval, and coordinate revised execution schedules with the responsible teams.";
        private const string WorkflowCase = "gate3-ed-fact12";
        private const string FeedbackEndpoint = "/api/v1/domains/1/feedback";
        private const string FeedbackQuery = FeedbackEndpoint + "?fact_id=12";
        private const string Decision = "submit_synthetic_feedback";
        private const string Fingerprint = "9ce70be76344f7839cb405c2053cd9e2b5ce750794ff53d84c61793903bd5b1c";
        private const int MaxHttpBytes = 4 * 1024 * 1024;
        private static readonly BackendBundleV2Selection Selection = new("http://127.0.0.1:8187", 1,
            "vantagenet-acceptance-20261121-e63c", "sqlite:disposable_vantagenet_acceptance_20261121_e63c.db",
            "aff04920-b5ee-4ddd-9786-9c94a7549d35", 12, WorkflowCase, "v1");

        private sealed record FeedbackReceipt(long FeedbackId, string Reference, long FactId,
            string Division, string Origin, string CreatedAt);

        private sealed record HttpEvidence(int? Status, string? MediaType, byte[] Body, string? Error)
        {
            internal JsonElement Json()
            {
                Require(Status == 200 && Error is null && MediaType == "application/json",
                    "Expected an HTTP 200 JSON response from the pinned backend.");
                return Parse(Body);
            }

            internal string Save(string path)
            {
                var archive = JsonSerializer.SerializeToUtf8Bytes(new
                {
                    scenario_label = SyntheticLabel, http_status = Status, content_type = MediaType,
                    body_base64 = Convert.ToBase64String(Body), body_sha256 = Sha256(Body), error = Error,
                });
                BackendNarrativeV2.Write(path, archive);
                return Sha256(archive);
            }

            internal static HttpEvidence ReadArchive(byte[] bytes)
            {
                var archive = Parse(bytes);
                Require(Text(archive, "scenario_label") == SyntheticLabel, "Invalid feedback archive label.");
                var encodedBody = Field(archive, "body_base64");
                Require(encodedBody.ValueKind == JsonValueKind.String && encodedBody.TryGetBytesFromBase64(out _),
                    "Invalid archived HTTP response bytes.");
                var body = encodedBody.GetBytesFromBase64();
                Require(Sha256(body) == Text(archive, "body_sha256"), "Archived HTTP response hash mismatch.");
                return new(Field(archive, "http_status").GetInt32OrNull(), OptionalText(archive, "content_type"),
                    body, OptionalText(archive, "error"));
            }

            private static string? OptionalText(JsonElement value, string name) =>
                Field(value, name).ValueKind == JsonValueKind.Null ? null : Text(value, name);
        }

        internal static async Task<string> Run(HttpClient client, string projectFolder, string decisionPath,
            bool authorizePost, TimeProvider clock)
        {
            var project = Path.GetFullPath(projectFolder);
            Require(Text(Parse(BackendNarrativeV2.Read(Path.Combine(project, "project.json"))), "projectId")
                == "a5ddfe29-5288-4542-85a4-72e9a6156a5d", "Use the VantageNet.Reporting project folder.");

            var folder = Path.Combine(project, "Output", "OperatorFeedback", Selection.InstanceId, WorkflowCase);
            BackendNarrativeV2.SafePath(folder);
            Directory.CreateDirectory(folder);
            var lockPath = Path.Combine(folder, ".feedback.lock");
            BackendNarrativeV2.SafePath(lockPath);
            using var gate = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var attempt = Path.Combine(folder, "attempt");
            BackendNarrativeV2.SafePath(attempt);

            var identity = await Exchange(client, HttpMethod.Get, "/_development/instance").ConfigureAwait(false);
            CheckInstance(identity.Json(), Selection);
            var ledgerResponse = await Exchange(client, HttpMethod.Get, "/api/v1/domains/1/submissions/" + Selection.SubmissionId)
                .ConfigureAwait(false);
            var ledger = CheckLedger(ledgerResponse.Json(), Selection);
            CheckSelectedReading(ledger);

            var review = Path.Combine(folder, "review");
            var requestPath = Path.Combine(review, "request.json");
            if (Directory.Exists(attempt))
                return await Verify(client, attempt, clock).ConfigureAwait(false);

            if (string.IsNullOrWhiteSpace(decisionPath))
            {
                Require(!authorizePost, "Provide an attended decision file before authorizing a feedback POST.");
                return Prepare(project, review, ledger.Reading, clock.GetUtcNow());
            }

            Require(authorizePost, "A decision file requires separate authorizePost=true authorization to submit.");
            var requestBytes = BackendNarrativeV2.Read(requestPath);
            var request = Parse(requestBytes);
            var template = BackendNarrativeV2.Read(Path.Combine(project, "Data", "operator-feedback-review.html"));
            var payload = JsonSerializer.SerializeToUtf8Bytes(Payload());
            CheckRequest(request, ledger.Reading, template);
            Require(BackendNarrativeV2.Read(Path.Combine(review, "operator-feedback-review.html"))
                .SequenceEqual(RenderForm(template, request, Sha256(requestBytes))), "The attended feedback form changed.");
            var decisionBytes = BackendNarrativeV2.Read(Path.GetFullPath(decisionPath));
            CheckDecision(Parse(decisionBytes), request, Sha256(requestBytes), clock.GetUtcNow());

            var baseline = await Exchange(client, HttpMethod.Get, FeedbackQuery).ConfigureAwait(false);
            // Preserve each preflight response even when eligibility checks fail.
            var baselineFolder = NewObservation(folder, "preflight");
            var baselinePath = Path.Combine(baselineFolder, "feedback-get.json");
            var baselineHash = baseline.Save(baselinePath);
            Require(FeedbackRecords(baseline.Json()).GetArrayLength() == 0,
                "Fact 12 already has feedback. No POST was sent. Inspect " + baselinePath);

            var startedAt = clock.GetUtcNow();
            BackendNarrativeV2.CreatePending(attempt);
            BackendNarrativeV2.Write(Path.Combine(attempt, "decision.json"), decisionBytes);
            BackendNarrativeV2.Write(Path.Combine(attempt, "request.json"), requestBytes);
            baseline.Save(Path.Combine(attempt, "baseline-get.json"));
            WriteJson(Path.Combine(attempt, "write-intent.json"), new
            {
                scenario_label = SyntheticLabel, state = "write_intent", started_at = startedAt,
                request_sha256 = Sha256(requestBytes), decision_sha256 = Sha256(decisionBytes),
                baseline_sha256 = baselineHash, method = "POST", endpoint = FeedbackEndpoint,
                payload_sha256 = Sha256(payload), payload = Parse(payload),
            });

            // An attempt directory is permanent. Later entries take the GET-only path above.
            var post = await Exchange(client, HttpMethod.Post, FeedbackEndpoint, payload).ConfigureAwait(false);
            post.Save(Path.Combine(attempt, "feedback-post.json"));
            return await Verify(client, attempt, clock).ConfigureAwait(false);
        }

        private static void CheckSelectedReading(BackendBundleV2Ledger ledger)
        {
            var row = ledger.Reading;
            Require(ledger.Fingerprint == Fingerprint && ledger.Division == "ED" && ledger.Date == "2026-06-30"
                && ledger.FileName == "ed.xlsx" && Text(row, "kpi_name") == "DEP-WHF-Deployment Alpro"
                && Integer(row, "kpi_id") == 6 && Text(row, "location_name") == "Demo South"
                && Integer(row, "location_id") == 2 && Text(row, "unit") == "Port"
                && NumericEquals(row, "actual_value", 546) && NumericEquals(row, "target_value", 600)
                && Integer(row, "source_row") == 16 && Boolean(row, "higher_is_better") && Text(row, "status") == "RED",
                "Selected KPI, workbook provenance, location or values differ from the acceptance fact.");
        }

        private static bool NumericEquals(JsonElement element, string name, decimal expected)
        {
            var value = Field(element, name);
            return value.ValueKind == JsonValueKind.Number && value.TryGetDecimal(out var actual) && actual == expected;
        }

        private static object Payload() => new { fact_id = Selection.FactId, explanation = Explanation, corrective_action = CorrectiveAction };

        private static object Binding() => new
        {
            instance_id = Selection.InstanceId, backend_origin = Selection.Origin.AbsoluteUri, database = Selection.Database,
            domain_id = Selection.DomainId, submission_id = Selection.SubmissionId, submission_fingerprint = Fingerprint,
            fact_id = Selection.FactId,
        };

        private static string Prepare(string project, string review, JsonElement reading, DateTimeOffset now)
        {
            BackendNarrativeV2.SafePath(review);
            var html = Path.Combine(review, "operator-feedback-review.html");
            var template = BackendNarrativeV2.Read(Path.Combine(project, "Data", "operator-feedback-review.html"));
            if (Directory.Exists(review))
            {
                var existing = BackendNarrativeV2.Read(Path.Combine(review, "request.json"));
                CheckRequest(Parse(existing), reading, template);
                Require(BackendNarrativeV2.Read(html).SequenceEqual(RenderForm(template, Parse(existing), Sha256(existing))),
                    "The attended feedback form changed.");
                return html;
            }
            var request = JsonSerializer.SerializeToUtf8Bytes(new
            {
                scenario_label = SyntheticLabel, request_id = Guid.NewGuid().ToString("D"), created_at = now,
                binding = Binding(), reading, payload = Payload(), form_sha256 = Sha256(template),
            });
            BackendNarrativeV2.CreatePending(review);
            BackendNarrativeV2.Write(Path.Combine(review, "request.json"), request);
            BackendNarrativeV2.Write(html, RenderForm(template, Parse(request), Sha256(request)));
            return html;
        }

        private static byte[] RenderForm(byte[] template, JsonElement request, string hash)
        {
            const string marker = "/*OPERATOR_FEEDBACK_DATA*/null";
            var html = Encoding.UTF8.GetString(template);
            Require(html.Contains(marker, StringComparison.Ordinal), "Operator feedback form template marker is missing.");
            var data = JsonSerializer.Serialize(new { request, request_sha256 = hash });
            return Encoding.UTF8.GetBytes(html.Replace(marker, data, StringComparison.Ordinal));
        }

        private static void CheckRequest(JsonElement request, JsonElement reading, byte[] template)
        {
            Require(Text(request, "scenario_label") == SyntheticLabel && Guid.TryParseExact(Text(request, "request_id"), "D", out _)
                && JsonElement.DeepEquals(Field(request, "binding"), JsonSerializer.SerializeToElement(Binding()))
                && JsonElement.DeepEquals(Field(request, "reading"), reading)
                && JsonElement.DeepEquals(Field(request, "payload"), JsonSerializer.SerializeToElement(Payload()))
                && Text(request, "form_sha256") == Sha256(template), "Attended feedback request no longer matches its pinned form or reading.");
        }

        private static void CheckDecision(JsonElement decision, JsonElement request, string requestHash, DateTimeOffset now)
        {
            Require(Text(decision, "scenario_label") == SyntheticLabel && Text(decision, "decision") == Decision
                && Boolean(decision, "acknowledged")
                && Text(decision, "request_id") == Text(request, "request_id")
                && Text(decision, "request_sha256") == requestHash, "The attended feedback decision is missing or belongs to a different request.");
            var reviewedAt = UtcTimestamp(Text(decision, "decided_at"));
            Require(reviewedAt >= UtcTimestamp(Text(request, "created_at")) && reviewedAt >= now.AddHours(-24)
                && reviewedAt <= now.AddMinutes(5), "The attended feedback decision has expired or has an invalid timestamp.");
        }

        private static JsonElement FeedbackRecords(JsonElement response)
        {
            var entries = Field(response, "feedback");
            Require(entries.ValueKind == JsonValueKind.Array, "Expected a feedback array.");
            Require(Integer(response, "domain_id") == Selection.DomainId && Integer(response, "fact_id") == Selection.FactId
                && Text(response, "submission_id") == Selection.SubmissionId && Text(response, "division") == "ED"
                && Text(response, "source_file") == "ed.xlsx" && Integer(response, "source_row") == 16
                && Integer(response, "feedback_count") == entries.GetArrayLength(), "Exact-fact feedback GET provenance mismatch.");
            return entries;
        }

        private static FeedbackReceipt ValidateReceipt(JsonElement entry, DateTimeOffset startedAt, DateTimeOffset now)
        {
            var id = Integer(entry, "feedback_id");
            var timestamp = Text(entry, "created_at");
            var created = UtcTimestamp(timestamp);
            var receipt = new FeedbackReceipt(id, Text(entry, "reference"), Integer(entry, "fact_id"),
                Text(entry, "division"), Text(entry, "origin"), timestamp);
            Require(id > 0 && receipt.Reference == "F" + id.ToString(CultureInfo.InvariantCulture)
                && receipt.FactId == Selection.FactId && receipt.Division == "ED" && receipt.Origin == "operator-api"
                && created >= startedAt && created <= now.AddMinutes(5), "Feedback receipt identity, origin or timestamp mismatch.");
            return receipt;
        }

        private static DateTimeOffset UtcTimestamp(string text)
        {
            if ((text.EndsWith('Z') || text.EndsWith("+00:00", StringComparison.Ordinal))
                && DateTimeOffset.TryParseExact(text,
                    new[] { "yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK", "yyyy-MM-dd'T'HH:mm:ssK" },
                    CultureInfo.InvariantCulture, DateTimeStyles.None, out var value)) return value;
            throw new InvalidDataException("Expected a UTC feedback timestamp.");
        }

        private static async Task<string> Verify(HttpClient client, string attempt, TimeProvider clock)
        {
            var requestBytes = BackendNarrativeV2.Read(Path.Combine(attempt, "request.json"));
            var intent = Parse(BackendNarrativeV2.Read(Path.Combine(attempt, "write-intent.json")));
            Require(Text(intent, "scenario_label") == SyntheticLabel && Text(intent, "state") == "write_intent"
                && Sha256(requestBytes) == Text(intent, "request_sha256")
                && Sha256(BackendNarrativeV2.Read(Path.Combine(attempt, "decision.json"))) == Text(intent, "decision_sha256")
                && Sha256(BackendNarrativeV2.Read(Path.Combine(attempt, "baseline-get.json"))) == Text(intent, "baseline_sha256")
                && Text(intent, "payload_sha256") == Sha256(JsonSerializer.SerializeToUtf8Bytes(Payload()))
                && JsonElement.DeepEquals(Field(intent, "payload"), JsonSerializer.SerializeToElement(Payload())),
                "The archived write intent or its evidence changed. No POST will be retried.");
            var startedAt = UtcTimestamp(Text(intent, "started_at"));
            var folder = NewObservation(attempt, "verification");
            var get = await Exchange(client, HttpMethod.Get, FeedbackQuery).ConfigureAwait(false);
            var getHash = get.Save(Path.Combine(folder, "feedback-get.json"));
            var responsePath = Path.Combine(attempt, "feedback-post.json");
            var now = clock.GetUtcNow();
            FeedbackReceipt? verified = null;
            var state = "verification_failed";
            string? error = null;
            byte[]? postArchive = null;
            try
            {
                BackendNarrativeV2.SafePath(responsePath);
                if (File.Exists(responsePath)) postArchive = BackendNarrativeV2.Read(responsePath);
                var post = postArchive is null ? null : HttpEvidence.ReadArchive(postArchive);
                var records = FeedbackRecords(get.Json());
                var candidates = records.EnumerateArray().Where(entry =>
                    Text(entry, "explanation") == Explanation && Text(entry, "corrective_action") == CorrectiveAction).ToArray();
                Require(candidates.Length == 1, candidates.Length == 0
                    ? "No matching feedback found. The POST will not be repeated."
                    : "Multiple matching feedback rows found. Preserve the evidence for manual reconciliation.");
                var saved = ValidateReceipt(candidates[0], startedAt, now);
                if (post is { Status: 200, Error: null })
                {
                    Require(ValidateReceipt(post.Json(), startedAt, now) == saved, "POST receipt differs from exact-fact GET.");
                    state = "verified";
                }
                else
                {
                    Require(post?.Status is null or >= 500 || post is { Status: 200, Error: not null },
                        "The POST returned an unexpected HTTP result. Preserve the evidence for manual reconciliation.");
                    state = "reconciled_after_ambiguous_post";
                }
                verified = saved;
            }
            catch (InvalidDataException validation)
            {
                error = validation.Message;
            }

            var result = Path.Combine(folder, "receipt.json");
            WriteJson(result, new
            {
                scenario_label = SyntheticLabel, binding = Binding(), state, checked_at = now, error,
                request_sha256 = Sha256(requestBytes), decision_sha256 = Text(intent, "decision_sha256"),
                baseline_sha256 = Text(intent, "baseline_sha256"),
                post_archive_sha256 = postArchive is null ? null : Sha256(postArchive), get_archive_sha256 = getHash,
                get_body_sha256 = Sha256(get.Body), feedback = verified is null ? null : new
                {
                    scenario_label = SyntheticLabel, feedback_id = verified.FeedbackId, reference = verified.Reference,
                    fact_id = verified.FactId, division = verified.Division, origin = verified.Origin, created_at = verified.CreatedAt,
                    explanation = Explanation, corrective_action = CorrectiveAction,
                },
            });
            Require(verified is not null, error + " See " + result);
            return result;
        }

        private static string NewObservation(string root, string prefix)
        {
            var folder = Path.Combine(root, prefix + "-" + Guid.NewGuid().ToString("N"));
            BackendNarrativeV2.CreatePending(folder);
            return folder;
        }

        private static void WriteJson(string path, object value) =>
            BackendNarrativeV2.Write(path, JsonSerializer.SerializeToUtf8Bytes(value));

        private static async Task<HttpEvidence> Exchange(HttpClient client, HttpMethod method, string endpoint, byte[]? payload = null)
        {
            using var request = new HttpRequestMessage(method, new Uri(Selection.Origin, endpoint));
            if (payload is not null)
            {
                request.Headers.ConnectionClose = true;
                request.Content = new ByteArrayContent(payload);
                request.Content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
            }

            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(10));
            int? status = null;
            string? mediaType = null;
            using var body = new MemoryStream();
            try
            {
                using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, deadline.Token).ConfigureAwait(false);
                status = (int)response.StatusCode;
                mediaType = response.Content.Headers.ContentType?.MediaType;
                using var stream = await response.Content.ReadAsStreamAsync(deadline.Token).ConfigureAwait(false);
                var buffer = new byte[8192];
                int read;
                while ((read = await stream.ReadAsync(buffer.AsMemory(), deadline.Token).ConfigureAwait(false)) > 0)
                {
                    if (body.Length + read > MaxHttpBytes)
                        return new(status, mediaType, body.ToArray(), "Response exceeds the 4 MiB archive limit.");
                    body.Write(buffer, 0, read);
                }
                return new(status, mediaType, body.ToArray(), null);
            }
            catch (OperationCanceledException)
            {
                return new(status, mediaType, body.ToArray(), "HTTP request or response read timed out.");
            }
            catch (Exception error) when (error is HttpRequestException or IOException)
            {
                return new(status, mediaType, body.ToArray(), error.GetType().Name + ": " + error.Message);
            }
        }

        private static int? GetInt32OrNull(this JsonElement value)
        {
            if (value.ValueKind == JsonValueKind.Null) return null;
            Require(value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out _), "Invalid archived HTTP status.");
            return value.GetInt32();
        }
    }
}

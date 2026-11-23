#nullable enable
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace VantageNet.Reporting
{
    internal sealed record BackendBundleV2Ledger(string Fingerprint, string Division, string Date,
        string FileName, DateTimeOffset ConfirmedAt, JsonElement Reading);

    internal static class BackendBundleV2Contract
    {
        internal const string Name = "vantagenet.report-bundle";
        private const string ReadingFields = "fact_id kpi_id location_id kpi_name kpi_archetype location_name date division actual_value target_value unit higher_is_better attainment_pct source_file source_row status_code status chart_supported";

        internal static void Require(bool valid, string reason)
        {
            if (!valid) throw new InvalidDataException(reason);
        }

        internal static JsonElement Parse(byte[] bytes)
        {
            try
            {
                using var document = JsonDocument.Parse(bytes, new JsonDocumentOptions { MaxDepth = 32 });
                var root = document.RootElement;
                CheckJson(root);
                return root.Clone();
            }
            catch (JsonException)
            {
                throw new InvalidDataException("Backend response must be valid UTF-8 JSON.");
            }
            catch (InvalidOperationException)
            {
                throw new InvalidDataException("Backend response contains an invalid JSON string.");
            }
        }

        private static void CheckJson(JsonElement value)
        {
            if (value.ValueKind == JsonValueKind.Object)
            {
                var seen = new HashSet<string>(StringComparer.Ordinal);
                foreach (var property in value.EnumerateObject())
                {
                    Require(seen.Add(property.Name), "Duplicate JSON property.");
                    CheckJson(property.Value);
                }
            }
            else if (value.ValueKind == JsonValueKind.Array)
            {
                foreach (var entry in value.EnumerateArray()) CheckJson(entry);
            }
            else if (value.ValueKind == JsonValueKind.String)
            {
                _ = value.GetString(); // Decode now, before anything can be staged.
            }
        }

        private static void Shape(JsonElement value, string fields)
        {
            Require(value.ValueKind == JsonValueKind.Object, "Expected a JSON object.");
            var names = fields.Split(' ');
            Require(value.EnumerateObject().Count() == names.Length
                && names.All(key => value.TryGetProperty(key, out _)), "Unexpected or missing v2 field.");
        }

        internal static JsonElement Field(JsonElement value, string field)
        {
            if (value.ValueKind == JsonValueKind.Object && value.TryGetProperty(field, out var result)) return result;
            throw new InvalidDataException("Missing field: " + field);
        }

        internal static string Text(JsonElement value, string field)
        {
            var element = Field(value, field);
            Require(element.ValueKind == JsonValueKind.String, "Expected text: " + field);
            return element.GetString()!;
        }

        private static string Nonempty(JsonElement value, string field)
        {
            var text = Text(value, field);
            Require(!string.IsNullOrWhiteSpace(text), "Empty field: " + field);
            return text;
        }

        private static string? OptionalText(JsonElement value, string field) =>
            Field(value, field).ValueKind == JsonValueKind.Null ? null : Text(value, field);

        internal static bool Boolean(JsonElement value, string field)
        {
            var element = Field(value, field);
            Require(element.ValueKind is JsonValueKind.True or JsonValueKind.False, "Expected boolean: " + field);
            return element.GetBoolean();
        }

        internal static long Integer(JsonElement value, string field)
        {
            var element = Field(value, field);
            if (element.ValueKind == JsonValueKind.Number && element.TryGetInt64(out var number)) return number;
            throw new InvalidDataException("Expected integer: " + field);
        }

        private static double? Number(JsonElement value, string field, bool nullable = false)
        {
            var element = Field(value, field);
            if (element.ValueKind == JsonValueKind.Null && nullable) return null;
            if (element.ValueKind == JsonValueKind.Number && element.TryGetDouble(out var number) && double.IsFinite(number))
                return number;
            throw new InvalidDataException("Expected finite number: " + field);
        }

        private static JsonElement Array(JsonElement value, string field)
        {
            var array = Field(value, field);
            Require(array.ValueKind == JsonValueKind.Array, "Expected array: " + field);
            return array;
        }

        internal static bool IsHash(string text) => Regex.IsMatch(text, @"\A[0-9a-f]{64}\z");

        private static DateTimeOffset Timestamp(JsonElement value, string field)
        {
            var timestamp = Text(value, field);
            if (Regex.IsMatch(timestamp, @"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,7})?(Z|\+00:00)\z")
                && DateTimeOffset.TryParse(timestamp, CultureInfo.InvariantCulture, DateTimeStyles.None, out var time)) return time;
            throw new InvalidDataException("Expected UTC timestamp: " + field);
        }

        private static long PositiveId(JsonElement value, string field)
        {
            var text = Text(value, field);
            if (long.TryParse(text, NumberStyles.None, CultureInfo.InvariantCulture, out var id) && id > 0
                && id.ToString(CultureInfo.InvariantCulture) == text) return id;
            throw new InvalidDataException("Expected canonical numeric string ID: " + field);
        }

        internal static void CheckInstance(JsonElement instance, BackendBundleV2Selection selection)
        {
            Require(Text(instance, "app") == "VantageNet" && Boolean(instance, "disposable")
                && Integer(instance, "domain_id") == selection.DomainId
                && Text(instance, "instance_id") == selection.InstanceId
                && Text(instance, "database") == selection.Database, "Disposable backend identity mismatch.");
        }

        internal static BackendBundleV2Ledger CheckLedger(JsonElement ledger, BackendBundleV2Selection selection)
        {
            Require(Text(ledger, "status") == "confirmed" && Integer(ledger, "domain_id") == selection.DomainId
                && Text(ledger, "submission_id") == selection.SubmissionId, "Expected the independently confirmed submission.");
            var capturedRows = Array(ledger, "readings");
            Require(Integer(ledger, "row_count") == capturedRows.GetArrayLength(), "Incomplete confirmation ledger.");
            var matches = capturedRows.EnumerateArray().Where(item => Integer(item, "fact_id") == selection.FactId).ToArray();
            Require(matches.Length == 1, "Exact fact must belong to the confirmed submission.");
            var row = matches[0];
            var fingerprint = Text(ledger, "fingerprint");
            var division = Nonempty(ledger, "division");
            var date = Text(ledger, "report_date");
            var filename = Nonempty(ledger, "filename");
            Require(IsHash(fingerprint) && DateOnly.TryParseExact(date, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out _)
                && Text(row, "submission_id") == selection.SubmissionId && Text(row, "division") == division
                && Text(row, "date") == date && Text(row, "source_file") == filename,
                "Confirmation ledger has inconsistent scope or provenance.");
            return new BackendBundleV2Ledger(fingerprint, division, date, filename, Timestamp(ledger, "confirmed_at"), row);
        }

        internal static string Validate(JsonElement bundle, BackendBundleV2Selection selection, BackendBundleV2Ledger ledger)
        {
            Shape(bundle, "contract schema_version bundle_id revision source_kind ai_invoked dataset evidence_status producer scope snapshot");
            Require(Text(bundle, "contract") == Name && Integer(bundle, "schema_version") == 2, "Unsupported v2 report bundle contract.");
            Require(Text(bundle, "source_kind") == "backend-read-bundle" && Text(bundle, "dataset") == "submitted",
                "Expected a submitted backend-read bundle.");
            Require(Text(bundle, "bundle_id") == selection.BundleId && Text(bundle, "revision") == selection.Revision,
                "Bundle ID or revision differs from the request.");

            var producer = Field(bundle, "producer");
            Shape(producer, "domain_id disposable instance_id captured_at submission_fingerprint reading_sha256");
            Require(Boolean(producer, "disposable") && Integer(producer, "domain_id") == selection.DomainId
                && Text(producer, "instance_id") == selection.InstanceId, "Bundle producer identity mismatch.");
            Require(Timestamp(producer, "captured_at") >= ledger.ConfirmedAt, "Bundle capture predates confirmation.");
            Require(Text(producer, "submission_fingerprint") == ledger.Fingerprint, "Submission fingerprint does not match the ledger.");
            var digest = Text(producer, "reading_sha256");
            Require(IsHash(digest), "Invalid reading digest.");

            var scope = Field(bundle, "scope");
            Shape(scope, "division report_date submission_id fact_id");
            var snapshot = Field(bundle, "snapshot");
            Shape(snapshot, "schema_version origin run_id submission_id division report_date reading feedback narrative");
            Require(Integer(snapshot, "schema_version") == 2 && Text(snapshot, "origin") == "backend-confirmed-submission"
                && Text(snapshot, "run_id") == selection.BundleId + "-" + selection.Revision, "Invalid v2 snapshot identity.");
            foreach (var part in new[] { scope, snapshot })
                Require(Text(part, "submission_id") == selection.SubmissionId && Text(part, "division") == ledger.Division
                    && Text(part, "report_date") == ledger.Date, "Bundle scope differs from the confirmed ledger.");
            Require(PositiveId(scope, "fact_id") == selection.FactId, "Bundle fact differs from the confirmed fact.");

            var reading = Field(snapshot, "reading");
            CheckReading(reading, ledger);
            var records = CheckFeedback(Field(snapshot, "feedback"), selection, ledger);
            var status = Text(bundle, "evidence_status");
            CheckNarrative(Field(snapshot, "narrative"), status, Boolean(bundle, "ai_invoked"), records);
            Require(digest == BackendBundleV2Digest.Reading(ledger.Fingerprint, reading, Field(Field(snapshot, "feedback"), "records")),
                "Reading digest mismatch.");
            return status;
        }

        private static void CheckReading(JsonElement reading, BackendBundleV2Ledger ledger)
        {
            Shape(reading, ReadingFields);
            var row = ledger.Reading;
            foreach (var field in new[] { "fact_id", "kpi_id", "location_id" })
                Require(PositiveId(reading, field) == Integer(row, field), "Reading identity mismatch: " + field);
            foreach (var field in new[] { "kpi_name", "kpi_archetype", "location_name", "date", "division", "unit", "source_file" })
                Require(Text(reading, field) == Text(row, field), "Reading provenance mismatch: " + field);

            var sourceRow = Integer(reading, "source_row");
            Require(sourceRow > 0 && sourceRow == Integer(row, "source_row"), "Reading source row mismatch.");
            foreach (var field in new[] { "actual_value", "target_value", "attainment_pct" })
                Require(Number(reading, field, field != "actual_value") == Number(row, field, field != "actual_value"),
                    "Reading value differs from the ledger: " + field);

            var higher = Boolean(reading, "higher_is_better");
            var code = Text(row, "status");
            var label = code switch
            {
                "RED" => higher ? "Below target" : "Above allowed limit",
                "GREEN" => "Meeting target",
                "YELLOW" => "Target unavailable",
                _ => throw new InvalidDataException("Unknown confirmed reading status."),
            };
            Require(higher == Boolean(row, "higher_is_better") && Text(reading, "status_code") == code
                && Text(reading, "status") == label, "Reading performance metadata differs from the ledger.");
            Require(Boolean(reading, "chart_supported") == (Number(reading, "target_value", true) > 0
                && Number(reading, "actual_value") >= 0), "Invalid backend chart metadata.");
        }

        private static Dictionary<string, JsonElement> CheckFeedback(JsonElement feedback,
            BackendBundleV2Selection selection, BackendBundleV2Ledger ledger)
        {
            Shape(feedback, "fact_id count origin records text");
            Require(PositiveId(feedback, "fact_id") == selection.FactId, "Feedback is for another fact.");
            var records = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
            var origins = new HashSet<string>(StringComparer.Ordinal);
            var previousId = 0L;
            foreach (var record in Array(feedback, "records").EnumerateArray())
            {
                Shape(record, "feedback_id reference fact_id division explanation corrective_action origin created_at");
                var id = PositiveId(record, "feedback_id");
                Require(id > previousId, "Feedback IDs must be unique and ordered.");
                previousId = id;
                var key = Text(record, "feedback_id");
                Require(Text(record, "reference") == "F" + key && PositiveId(record, "fact_id") == selection.FactId
                    && Text(record, "division") == ledger.Division, "Feedback fact or reference mismatch.");
                var origin = Text(record, "origin");
                Require(origin is "fixture-worksheet-notes" or "operator-api", "Unknown feedback origin.");
                _ = Nonempty(record, "explanation");
                _ = Text(record, "corrective_action");
                _ = Timestamp(record, "created_at");
                origins.Add(origin);
                records.Add(key, record);
            }
            var expectedOrigin = origins.Count switch { 0 => "none", 1 => origins.Single(), _ => "mixed" };
            var expectedText = records.Count == 0 ? "No division feedback recorded for this reading."
                : string.Join(" | ", records.Values.Select(record => "[" + Text(record, "reference") + "] " + Text(record, "explanation")));
            Require(records.Count == Integer(feedback, "count") && Text(feedback, "origin") == expectedOrigin
                && Text(feedback, "text") == expectedText, "Feedback count, aggregate origin, or summary mismatch.");
            return records;
        }

        private static void CheckNarrative(JsonElement narrative, string status, bool invoked,
            Dictionary<string, JsonElement> records)
        {
            Shape(narrative, "origin backend_evidence_status llm_model ai_invoked provider_status provider_error_code grounding cited_feedback_ids root_cause prescriptive_action draft references error");
            var provider = Text(narrative, "provider_status");
            var errorCode = OptionalText(narrative, "provider_error_code");
            var error = OptionalText(narrative, "error");
            var origin = Text(narrative, "origin");
            var backendStatus = Text(narrative, "backend_evidence_status");
            var model = Nonempty(narrative, "llm_model");
            var root = OptionalText(narrative, "root_cause");
            var action = OptionalText(narrative, "prescriptive_action");
            var draft = OptionalText(narrative, "draft");
            Require(invoked == Boolean(narrative, "ai_invoked") && invoked == (provider != "not_attempted"),
                "Provider invocation flags disagree.");

            var grounding = Field(narrative, "grounding");
            Shape(grounding, "cited_feedback_ids structural_check citation_verified");
            var ready = status == "draft_ready";
            var cited = CitationIds(narrative);
            Require(cited.SequenceEqual(CitationIds(grounding)) && Boolean(grounding, "structural_check") == ready
                && Boolean(grounding, "citation_verified") == ready, "Invalid grounding metadata.");
            Require(ready || (draft is null && cited.Length == 0), "Blocked status cannot supply a draft or verified citations.");

            var validModel = model is not ("not called" or "not available");
            var hasText = !string.IsNullOrWhiteSpace(root) && !string.IsNullOrWhiteSpace(action);
            var success = provider == "response_accepted" && errorCode is null && error is null
                && origin == "live-provider-rca" && validModel && hasText && records.Count > 0;
            var valid = status switch
            {
                "draft_ready" => success && backendStatus == "ai_draft" && !string.IsNullOrWhiteSpace(draft)
                    && draft == root + " Recommended action: " + action && cited.Length > 0,
                "insufficient_evidence" => success && backendStatus == "insufficient_evidence",
                "awaiting_feedback" => records.Count == 0 && provider == "not_attempted" && errorCode is null
                    && error is null && origin == "backend-deterministic-gate" && backendStatus == status
                    && model == "not called" && hasText,
                "provider_unavailable" => records.Count > 0 && !string.IsNullOrWhiteSpace(error)
                    && origin == "provider-error" && backendStatus == "provider_error" && model == "not available"
                    && root is null && action is null && ValidFailure(provider, errorCode),
                _ => false,
            };
            Require(valid, "Invalid evidence status or provider metadata combination.");

            var expected = status == "insufficient_evidence" ? records.Keys.ToArray() : cited;
            var references = Array(narrative, "references").EnumerateArray().ToArray();
            Require(references.Length == expected.Length, "Narrative reference count differs from captured evidence.");
            for (var i = 0; i < references.Length; i++)
            {
                var reference = references[i];
                Shape(reference, "id feedback_id origin text");
                Require(Text(reference, "feedback_id") == expected[i] && records.ContainsKey(expected[i]),
                    "Unresolved citation ID in narrative references.");
                var record = records[expected[i]];
                var actionText = Text(record, "corrective_action");
                var expectedText = Text(record, "explanation") + (actionText.Length == 0 ? "" : " Proposed action: " + actionText);
                Require(Text(reference, "id") == Text(record, "reference") && Text(reference, "origin") == Text(record, "origin")
                    && Text(reference, "text") == expectedText, "Reference metadata differs from the captured feedback.");
            }
            if (ready)
            {
                var inline = InlineIds(root + "\n" + action).ToArray();
                Require(inline.Length > 0 && inline.All(id => cited.Contains(id)), "Unresolved inline narrative citation.");
            }
        }

        private static bool ValidFailure(string status, string? code) => status switch
        {
            "not_attempted" => code == "missing_configuration",
            "attempted_unconfirmed" => code is "request_failed" or "timeout",
            "response_rejected" => code is "invalid_response" or "invalid_citations",
            _ => false,
        };

        private static string[] CitationIds(JsonElement value) =>
            Array(value, "cited_feedback_ids").EnumerateArray().Select(item =>
            {
                Require(item.ValueKind == JsonValueKind.String, "Expected string citation ID.");
                return item.GetString()!;
            }).ToArray();

        private static IEnumerable<string> InlineIds(string text)
        {
            foreach (Match match in Regex.Matches(text, @"\[F([^\[\]\r\n]+)\]"))
            {
                var digits = new StringBuilder();
                foreach (var rune in match.Groups[1].Value.EnumerateRunes())
                {
                    if (Rune.GetUnicodeCategory(rune) != UnicodeCategory.DecimalDigitNumber)
                    {
                        digits.Clear();
                        break;
                    }
                    digits.Append((char)('0' + (int)Rune.GetNumericValue(rune)));
                }
                if (digits.Length > 0) yield return digits.ToString().TrimStart('0');
            }
        }
    }
}

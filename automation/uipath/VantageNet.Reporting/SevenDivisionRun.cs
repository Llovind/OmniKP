#nullable enable
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace VantageNet.Reporting
{
    internal sealed partial class SevenDivisionRun : IDisposable
    {
        private sealed record Division(string Name, string Folder, string Filename, string Sheet, int Header, int Depth, int Kpis, int Readings);
        private sealed record Workbook(Division Division, string Path, string Sha, string Folder);
        private const string Api = "api/v1/domains/1/";
        private static readonly JsonSerializerOptions Json = new() { WriteIndented = true };
        private readonly string project, input, logs, output, runId, bundleId, revision, day, mode, referencePath;
        private readonly Division[] divisions;
        private readonly JsonNode identity;
        private readonly HttpClient http;
        private readonly FileStream gate;

        public SevenDivisionRun(string projectFolder, string configPath)
        {
            project = Path.GetFullPath(projectFolder);
            var config = Read(configPath);
            runId = Token(S(config, "run_id"));
            bundleId = Token(S(config, "bundle_id"));
            revision = S(config, "revision");
            Need(Regex.IsMatch(revision, @"\Av[1-9][0-9]{0,5}\z"), "Use a revision such as v8.");
            day = S(config, "report_date");
            Need(DateOnly.TryParseExact(day, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out _), "Invalid report date.");
            mode = S(config, "decision_mode");
            Need(mode is "supervised-local" or "automated-test", "Unknown decision mode.");
            var configDir = Path.GetDirectoryName(Path.GetFullPath(configPath))!;
            string PathFromConfig(string key) => Path.GetFullPath(S(config, key), configDir);
            input = PathFromConfig("input_root");
            var root = PathFromConfig("work_root");
            var manifestPath = PathFromConfig("division_manifest");
            referencePath = PathFromConfig("expected_readings");
            divisions = Items(Read(manifestPath)).Select(item =>
            {
                Need(S(item, "report_date") == day, "Division metadata must use the selected reporting date.");
                var name = S(item, "filename");
                Need(Path.GetFileName(name) == name && name.EndsWith(".xlsx", StringComparison.OrdinalIgnoreCase), "Manifest filenames must be local XLSX names.");
                var folder = item["folder"]?.GetValue<string>() ?? Path.GetFileNameWithoutExtension(name).ToUpperInvariant();
                var header = N(item, "header_row");
                var depth = N(item, "header_depth");
                Need(header is >= 1 and <= 50 && depth is >= 1 and <= 3, "Set explicit worksheet headers in the division manifest.");
                return new Division(S(item, "division"), Token(folder), name, S(item, "sheet"), header, depth, N(item, "kpis"), N(item, "readings"));
            }).ToArray();
            Need(divisions.Length == 7 && divisions.Select(d => d.Name).Distinct().Count() == 7 &&
                 divisions.Select(d => d.Folder).Distinct(StringComparer.OrdinalIgnoreCase).Count() == 7 &&
                 divisions.All(d => d.Kpis > 0 && d.Readings >= d.Kpis), "Manifest requires seven distinct divisions with expected counts.");
            var origin = new Uri(S(config, "backend_origin"));
            Need(origin.Scheme == "http" && origin.Host == "127.0.0.1" && origin.AbsolutePath == "/" &&
                 origin.UserInfo == "" && origin.Query == "" && origin.Fragment == "", "Use a loopback HTTP backend origin.");
            logs = Path.Combine(root, "Logs", runId);
            output = Path.Combine(root, "Output", runId, bundleId, revision);
            // The new demo uses its own workspace, regardless of which directory the robot runs from.
            Need(!Inside(root, project) && !Inside(root, Path.Combine(project, "..", "..", "..", "deliverables")),
                 "Use a demo work root outside the UiPath project and deliverables.");
            Directory.CreateDirectory(logs);
            gate = new FileStream(Path.Combine(logs, "batch.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            http = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false })
            { BaseAddress = origin, Timeout = TimeSpan.FromSeconds(90) };
            try
            {
                identity = Get("_development/instance");
                Need(B(identity, "disposable") && S(identity, "app") == "VantageNet" && N(identity, "domain_id") == 1 &&
                     S(identity, "instance_id") == S(config, "expected_instance_id") &&
                     S(identity, "database") == S(config, "expected_database") && S(identity, "database").StartsWith("sqlite:disposable-", StringComparison.Ordinal),
                     "The backend identity does not match the designated disposable database.");
                var importConfig = config.DeepClone().AsObject();
                importConfig.Remove("bundle_id");
                importConfig.Remove("revision");
                var binding = Node(new { import_config_sha256 = Hash(Encoding.UTF8.GetBytes(importConfig.ToJsonString())),
                    manifest_sha256 = HashFile(manifestPath), reference_sha256 = HashFile(referencePath), identity, run_id = runId, decision_mode = mode });
                var bindingPath = Log("run.json");
                if (File.Exists(bindingPath))
                    Need(JsonNode.DeepEquals(binding, Read(bindingPath)), "Run configuration changed. Restore it or start a new run.");
                else
                {
                    var baseline = Get(Api + "submissions");
                    var periods = Get(Api + "periods?dataset=all");
                    Need(baseline.AsArray().Count == 0 && periods.AsArray().Count == 0,
                         "A new batch requires an empty disposable database. Resume an existing batch with its original config.");
                    var clean = Node(new { identity, submissions = baseline, periods });
                    if (File.Exists(Log("baseline.json")))
                        Need(JsonNode.DeepEquals(clean, Read(Log("baseline.json"))), "Initial baseline changed.");
                    else WriteNew(Log("baseline.json"), clean);
                    WriteNew(bindingPath, binding);
                }
            }
            catch { Dispose(); throw; }
        }

        public void Dispose() { http.Dispose(); gate.Dispose(); }

        public string Advance(string decisionPath)
        {
            var decision = string.IsNullOrWhiteSpace(decisionPath) ? null : Read(decisionPath);
            var inventory = Scan();
            var completed = new List<JsonNode>();
            var owners = inventory.Files.GroupBy(file => file.Sha).ToDictionary(group => group.Key,
                group => group.FirstOrDefault(file => File.Exists(Path.Combine(file.Folder, "preview-intent.json"))) ?? group.First());
            foreach (var file in inventory.Files)
            {
                if (owners[file.Sha] != file)
                {
                    inventory.Status[file.Division.Name] = "duplicate_workbook_bytes";
                    continue;
                }
                var result = Process(file, ref decision);
                inventory.Status[file.Division.Name] = result.State;
                if (result.Confirmed != null) completed.Add(result.Confirmed);
                if (result.Form == null) continue;
                Need(decision == null, "Decision does not match this pending request. Open the current review form.");
                SaveManifest(inventory.Status, inventory.Discovered, result.Form);
                return result.Form;
            }
            SaveManifest(inventory.Status, inventory.Discovered, null);
            if (completed.Count != divisions.Length)
            {
                Need(decision == null, "There is no matching pending review in this run.");
                return Log("run-manifest.json");
            }
            var report = PrepareReport(completed, decision);
            if (report.EndsWith(".html", StringComparison.Ordinal)) SaveManifest(inventory.Status, inventory.Discovered, report);
            return report;
        }

        private (List<Workbook> Files, Dictionary<string, string> Status, List<object> Discovered) Scan()
        {
            var files = new List<Workbook>();
            var status = new Dictionary<string, string>();
            var discovered = new List<object>();
            foreach (var division in divisions)
            {
                var folder = Path.Combine(input, division.Folder);
                status[division.Name] = Directory.Exists(folder) ? "expected_workbook_missing" : "division_folder_missing";
                if (!Directory.Exists(folder)) continue;
                foreach (var path in Directory.EnumerateFiles(folder).Order(StringComparer.OrdinalIgnoreCase))
                {
                    var name = Path.GetFileName(path);
                    if (name.StartsWith("~$", StringComparison.Ordinal) || !name.EndsWith(".xlsx", StringComparison.OrdinalIgnoreCase)) continue;
                    var selected = string.Equals(name, division.Filename, StringComparison.OrdinalIgnoreCase);
                    try
                    {
                        if (new FileInfo(path).Length > 10 * 1024 * 1024)
                        {
                            discovered.Add(new { division = division.Name, workbook = name, state = "over_size_limit" });
                            if (selected) status[division.Name] = "over_size_limit";
                            continue;
                        }
                        var sha = HashFile(path);
                        discovered.Add(new { division = division.Name, workbook = name, sha256 = sha,
                            state = selected ? "selected" : "unlisted_xlsx" });
                        if (!selected) continue;
                        var divisionLog = Log(division.Folder);
                        var attempt = Path.Combine(divisionLog, sha);
                        var prior = Directory.Exists(divisionLog) && Directory.EnumerateDirectories(divisionLog)
                            .Any(dir => dir != attempt && File.Exists(Path.Combine(dir, "preview-intent.json")) &&
                                !File.Exists(Path.Combine(dir, "rejection.json")) && !MalformedAndAbsent(dir));
                        if (prior) { status[division.Name] = "source_changed_after_preview"; continue; }
                        files.Add(new Workbook(division, path, sha, attempt));
                        status[division.Name] = "discovered";
                    }
                    catch (IOException) { if (selected) status[division.Name] = "workbook_unreadable"; }
                    catch (UnauthorizedAccessException) { if (selected) status[division.Name] = "workbook_unreadable"; }
                }
            }
            return (files, status, discovered);
        }

        private static bool MalformedAndAbsent(string folder) =>
            ReadIf(Path.Combine(folder, "preview-error.json")) is JsonNode error && N(error, "http_status") == 422 &&
            ReadIf(Path.Combine(folder, "preview-reconciliation.json")) is JsonNode entry && S(entry, "state") == "preview_ledger_absent";

        private (string State, string? Form, JsonNode? Confirmed) Process(Workbook file, ref JsonNode? decision)
        {
            string At(string name) => Path.Combine(file.Folder, name);
            var intent = At("preview-intent.json");
            var previewPath = At("preview.json");
            var division = file.Division;
            if (!File.Exists(intent))
            {
                Need(decision == null, "Decision does not match a staged workbook. Open the current review form.");
                Directory.CreateDirectory(file.Folder);
                var bytes = File.ReadAllBytes(file.Path);
                Need(Hash(bytes) == file.Sha, "Workbook changed during collection. Run the scan again.");
                var id = Guid.NewGuid().ToString();
                var metadata = Encoding.UTF8.GetBytes($"{division.Name}|{day}|{division.Sheet}|{division.Header}|{division.Depth}");
                WriteNew(intent, Node(new { submission_id = id, sha256 = file.Sha, fingerprint = Hash(bytes.Concat(metadata).ToArray()),
                    workbook = division.Filename, division = division.Name, report_date = day }));
                using var multipart = new MultipartFormDataContent();
                multipart.Add(new ByteArrayContent(bytes), "file", division.Filename);
                foreach (var (key, value) in new[] { ("submission_id", id), ("division", division.Name), ("report_date", day),
                    ("sheet_name", division.Sheet), ("header_row", division.Header.ToString(CultureInfo.InvariantCulture)),
                    ("header_depth", division.Depth.ToString(CultureInfo.InvariantCulture)), ("use_ai", "true") })
                    multipart.Add(new StringContent(value), key);
                RecordPost(Api + "submissions/preview", multipart, previewPath, At("preview-error.json"));
            }
            var request = Read(intent);
            var sid = S(request, "submission_id");
            var ledgerPath = Api + "submissions/" + sid;
            if (!File.Exists(previewPath))
            {
                var row = Lookup(ledgerPath);
                if (row != null) CheckLedger(row, division, request);
                var recovered = row == null ? "preview_ledger_absent" : "preview_ledger_" + S(row, "status");
                Write(At("preview-reconciliation.json"), Node(new { state = recovered, ledger = row }));
                var error = ReadIf(At("preview-error.json"));
                return (row != null || error == null ? recovered : $"preview_http_{N(error, "http_status")}", null, null);
            }
            var preview = Read(previewPath);
            Need(S(preview, "submission_id") == sid && S(preview, "division") == division.Name &&
                 S(preview, "filename") == division.Filename && S(preview, "sheet_name") == division.Sheet &&
                 N(preview, "header_row") == division.Header && N(preview, "header_depth") == division.Depth &&
                 S(preview["ai_trace"]!, "mode") == "live", "Preview scope or live AI trace does not match the run.");
            if (File.Exists(At("confirm-intent.json"))) return ReconcileConfirm(file, request, ledgerPath);
            var draft = Get(ledgerPath);
            CheckLedger(draft, division, request);
            Need(S(draft, "status") == "draft", "Unapproved submission was changed outside this run.");
            if (File.Exists(At("rejection.json"))) return ("rejected", null, null);

            var stage = Directory.EnumerateDirectories(file.Folder, "mapping-*").Order(StringComparer.Ordinal).LastOrDefault();
            var validation = stage == null ? null : ReadIf(Path.Combine(stage, "response.json"));
            var valid = validation != null && B(validation, "can_confirm") && N(validation, "valid_readings") == division.Readings &&
                N(validation, "invalid_readings") == 0 && N(validation, "conflict_count") == 0 &&
                Items(validation["issues"]!).Count() == 0 && Items(validation["conflicts"]!).Count() == 0;
            var kind = valid ? "import" : "mapping";
            var review = Node(new { kind, run_id = runId, report_date = day, submission_id = sid, decision_mode = mode, identity,
                preview_sha256 = HashFile(previewPath), attempt = stage == null ? "initial" : Path.GetFileName(stage),
                payload_sha256 = valid ? HashFile(Path.Combine(stage!, "payload.json")) : null });
            var hash = Hash(Encoding.UTF8.GetBytes(review.ToJsonString(Json)));
            if (decision != null && decision["request_sha256"]?.GetValue<string>() == hash)
            {
                CheckDecision(decision, hash);
                var chosen = decision;
                decision = null;
                if (S(chosen, "decision") == "reject")
                {
                    WriteNew(At("rejection.json"), chosen);
                    return ("rejected", null, null);
                }
                if (valid)
                {
                    Need(B(chosen, "authorize_confirm"), "Explicit authorization is required to import.");
                    var payload = Read(Path.Combine(stage!, "payload.json"));
                    WriteNew(At("confirm-intent.json"), Node(new { approval = chosen, payload }));
                    using var body = Body(payload);
                    RecordPost(ledgerPath + "/confirm", body, At("confirm-response.json"), At("confirm-error.json"));
                    return ReconcileConfirm(file, request, ledgerPath);
                }
                var mapping = chosen["mapping"]!.AsObject();
                var columns = Items(preview["columns"]!).Select(c => c.GetValue<string>()).ToArray();
                Need(mapping.Count == columns.Length && columns.All(mapping.ContainsKey), "Review every original source column.");
                Need(mapping.All(pair => pair.Value is JsonValue value && value.TryGetValue<string>(out var field) && field != "date" &&
                    (MappingReview.Fields.Contains(field) || (field.StartsWith("location:", StringComparison.Ordinal) && field[9..].Trim().Length is > 0 and <= 200))),
                    "Use supported mappings and the reporting date supplied by the manifest.");
                var payloadToReview = Node(new { mapping, default_direction = chosen["default_direction"] });
                var index = Directory.EnumerateDirectories(file.Folder, "mapping-*").Count() + 1;
                var next = At($"mapping-{index:D4}");
                Directory.CreateDirectory(next);
                WriteNew(Path.Combine(next, "decision.json"), chosen);
                WriteNew(Path.Combine(next, "payload.json"), payloadToReview);
                using var bodyToReview = Body(payloadToReview);
                RecordPost(ledgerPath + "/review", bodyToReview, Path.Combine(next, "response.json"), Path.Combine(next, "error.json"));
                return Process(file, ref decision);
            }
            var form = At(kind + "-review.html");
            RenderForm(form, Node(new { request = review, request_sha256 = hash, preview, validation,
                validated_mapping = valid ? Read(Path.Combine(stage!, "payload.json")) : null,
                previous_review = stage == null ? null : ReadIf(Path.Combine(stage, "payload.json")),
                review_error = stage == null ? null : ReadIf(Path.Combine(stage, "error.json")),
                fields = MappingReview.Fields.Where(field => field != "date"), expected_readings = division.Readings,
                workbook_sha256 = file.Sha }));
            return (valid ? "awaiting_import_authorization" : "awaiting_mapping_review", form, null);
        }

        private (string, string?, JsonNode?) ReconcileConfirm(Workbook file, JsonNode intent, string url)
        {
            string At(string name) => Path.Combine(file.Folder, name);
            var ledger = Get(url);
            CheckLedger(ledger, file.Division, intent);
            var payload = Read(At("confirm-intent.json"))["payload"]!;
            if (S(ledger, "status") != "confirmed")
            {
                Write(At("confirm-reconciliation.json"), Node(new { state = "confirmation_unresolved", ledger }));
                return ("confirmation_unresolved", null, null);
            }
            var readings = Items(ledger["readings"]!).ToArray();
            Need(JsonNode.DeepEquals(ledger["mapping"], payload["mapping"]) && N(ledger, "row_count") == file.Division.Readings &&
                readings.Length == file.Division.Readings && readings.Select(row => N(row, "fact_id")).Distinct().Count() == readings.Length &&
                readings.Select(row => N(row, "kpi_id")).Distinct().Count() == file.Division.Kpis &&
                readings.All(row => S(row, "date") == day && S(row, "division") == file.Division.Name &&
                    S(row, "submission_id") == S(intent, "submission_id") && S(row, "source_file") == file.Division.Filename && N(row, "source_row") > 0),
                "Confirmed submission differs from the authorized mapping, scope or expected reading count.");
            var previous = ReadIf(At("confirmed.json"));
            if (previous == null) WriteNew(At("confirmed.json"), ledger);
            else Need(JsonNode.DeepEquals(previous, ledger), "A confirmed ledger entry changed.");
            return ("confirmed", null, ledger);
        }

        private void CheckLedger(JsonNode row, Division division, JsonNode request) =>
            Need(S(row, "submission_id") == S(request, "submission_id") && S(row, "division") == division.Name &&
                 S(row, "filename") == division.Filename && S(row, "report_date") == day && S(row, "sheet_name") == division.Sheet &&
                 S(row, "fingerprint") == S(request, "fingerprint") && N(row, "domain_id") == 1, "Submission detail does not match the workbook and metadata.");

        private void CheckDecision(JsonNode decision, string hash) => Need(S(decision, "request_sha256") == hash &&
            S(decision, "decision_mode") == mode && S(decision, "decision") is "approve" or "reject" &&
            S(decision, "reviewer").Trim().Length is > 0 and <= 60 && S(decision, "reason").Trim().Length is > 0 and <= 240 &&
            DateTimeOffset.TryParse(S(decision, "decided_at"), CultureInfo.InvariantCulture, DateTimeStyles.None, out _),
            "A matching explicit decision, reviewer, reason and decision timestamp are required.");

        private void SaveManifest(Dictionary<string, string> status, List<object> discovered, string? pending) =>
            Write(Log("run-manifest.json"), Node(new { run_id = runId, report_date = day, identity, decision_mode = mode,
                input_root = input, divisions = status, discovered, pending_review = pending, updated_at = DateTimeOffset.UtcNow }));

        private void RenderForm(string path, JsonNode data) => Atomic(path,
            File.ReadAllText(Path.Combine(project, "Data", "seven-division-review.html")).Replace("/*REVIEW_DATA*/null", data.ToJsonString(Json)), true);

        private void VerifyIdentity() => Need(JsonNode.DeepEquals(Get("_development/instance"), identity), "Backend identity changed during the run.");

        private void RecordPost(string path, HttpContent body, string responsePath, string errorPath)
        {
            VerifyIdentity();
            try
            {
                using var response = http.PostAsync(path, body).GetAwaiter().GetResult();
                var raw = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                if (response.IsSuccessStatusCode) Atomic(responsePath, raw, false);
                else WriteNew(errorPath, Node(new { http_status = (int)response.StatusCode, response = raw }));
            }
            catch (Exception exc) when (exc is HttpRequestException or OperationCanceledException)
            {
                WriteNew(errorPath, Node(new { http_status = 0, response = "Transport outcome unknown. Check the ledger before taking further action." }));
            }
        }

        private JsonNode Get(string path) => Lookup(path) ?? throw new InvalidDataException("Backend resource not found: " + path);
        private JsonNode? Lookup(string path)
        {
            using var response = http.GetAsync(path).GetAwaiter().GetResult();
            if (response.StatusCode == HttpStatusCode.NotFound) return null;
            response.EnsureSuccessStatusCode();
            return JsonNode.Parse(response.Content.ReadAsStringAsync().GetAwaiter().GetResult())!;
        }

        private string Log(string name) => Path.Combine(logs, name);
        private static bool Inside(string candidate, string parent)
        {
            var relative = Path.GetRelativePath(Path.GetFullPath(parent), candidate);
            return relative != ".." && !relative.StartsWith(".." + Path.DirectorySeparatorChar, StringComparison.Ordinal) && !Path.IsPathRooted(relative);
        }
        private static string Token(string token)
        {
            Need(Regex.IsMatch(token, @"\A[A-Za-z0-9_-]{1,48}\z"), "Run, bundle and folder labels must contain only letters, digits, hyphens and underscores.");
            return token;
        }
        internal static void Need(bool ok, string message) { if (!ok) throw new InvalidDataException(message); }
        internal static string S(JsonNode node, string key) => node[key]!.GetValue<string>();
        internal static int N(JsonNode node, string key) => node[key]!.GetValue<int>();
        internal static bool B(JsonNode node, string key) => node[key]?.GetValue<bool>() == true;
        internal static IEnumerable<JsonNode> Items(JsonNode n) => n.AsArray().Select(item => item!);
        internal static JsonNode Read(string path) => JsonNode.Parse(File.ReadAllText(path))!;
        private static JsonNode? ReadIf(string path) => File.Exists(path) ? Read(path) : null;
        internal static JsonNode Node(object value) => JsonSerializer.SerializeToNode(value, Json)!;
        internal static string HashFile(string path) { using var stream = File.OpenRead(path); return Convert.ToHexStringLower(SHA256.HashData(stream)); }
        private static string Hash(byte[] data) => Convert.ToHexStringLower(SHA256.HashData(data));
        private static StringContent Body(JsonNode n) => new(n.ToJsonString(Json), Encoding.UTF8, "application/json");
        internal static void WriteNew(string path, JsonNode content) => Atomic(path, content.ToJsonString(Json), false);
        private static void Write(string path, JsonNode content) => Atomic(path, content.ToJsonString(Json), true);
        private static void Atomic(string path, string text, bool replace)
        {
            var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                stream.Write(Encoding.UTF8.GetBytes(text));
                stream.Flush(true);
            }
            File.Move(temporary, path, replace);
        }
    }
}

#nullable enable
using System;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using UiPath.Core;

namespace VantageNet.Reporting
{
    // Local-only Sprint 1 adapter. Backend owns parsing and interpretation.
    public static class PreviewIntake
    {
        public static string Run(string configPath)
        {
            configPath = Path.GetFullPath(configPath);
            using var config = JsonDocument.Parse(File.ReadAllText(configPath));
            var c = config.RootElement;
            string Text(string key) => c.GetProperty(key).GetString() ?? "";
            string Resolve(string key) => Path.GetFullPath(Path.Combine(Path.GetDirectoryName(configPath)!, Text(key)));
            var api = new Uri(Text("base_url"), UriKind.Absolute);
            if (api.Scheme != "http" || api.Host != "127.0.0.1" || api.AbsolutePath != "/" || api.UserInfo != "" || api.Query != "" || api.Fragment != "")
                throw new BusinessRuleException("Sprint 1 requires an HTTP 127.0.0.1 test backend base URL without path or credentials.");
            var input = Resolve("input_file");
            var output = Resolve("output_folder");
            var division = Text("division").Trim();
            var day = Text("report_date");
            var sheet = Text("sheet_name");
            var row = c.GetProperty("header_row").GetInt32();
            var depth = c.GetProperty("header_depth").GetInt32();
            if (division.Length < 1 || division.Length > 100 || !DateTime.TryParseExact(day, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None, out _) || row < 0 || depth < 1 || depth > 3)
                throw new BusinessRuleException("Invalid division, ISO report_date, header_row or header_depth.");
            if (!File.Exists(input) || (Path.GetExtension(input).ToLowerInvariant() != ".xlsx" && Path.GetExtension(input).ToLowerInvariant() != ".csv"))
                throw new BusinessRuleException("Input must be an existing XLSX or UTF-8 CSV file.");
            var bytes = File.ReadAllBytes(input);
            if (bytes.Length == 0 || bytes.Length > 10 * 1024 * 1024)
                throw new BusinessRuleException("Input must contain between 1 byte and 10 MiB.");
            Directory.CreateDirectory(output);
            var runId = Guid.NewGuid().ToString("N");
            var runFolder = Path.Combine(output, runId);
            Directory.CreateDirectory(runFolder);
            var hash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            var manifest = Path.Combine(runFolder, "manifest.json");
            string? submissionId = null;
            int? status = null;
            void Save(string state, string? error = null) => AtomicWrite(manifest, JsonSerializer.Serialize(new {
                run_id = runId, filename = Path.GetFileName(input), sha256 = hash, division,
                report_date = day, sheet_name = sheet, header_row = row, header_depth = depth,
                submission_id = submissionId, http_status = status, state, error,
                updated_at = DateTime.UtcNow.ToString("O"), confirmed = false
            }, new JsonSerializerOptions { WriteIndented = true }));
            Save("preview_pending");
            try
            {
                using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false };
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(90) };
                using var form = new MultipartFormDataContent();
                form.Add(new ByteArrayContent(bytes), "file", Path.GetFileName(input));
                form.Add(new StringContent(division), "division");
                form.Add(new StringContent(day), "report_date");
                form.Add(new StringContent(sheet), "sheet_name");
                form.Add(new StringContent(row.ToString(System.Globalization.CultureInfo.InvariantCulture)), "header_row");
                form.Add(new StringContent(depth.ToString(System.Globalization.CultureInfo.InvariantCulture)), "header_depth");
                form.Add(new StringContent("true"), "use_ai");
                // Preview creates a draft: do not retry an ambiguous POST automatically.
                using var response = client.PostAsync(new Uri(api, "api/v1/domains/1/submissions/preview"), form).GetAwaiter().GetResult();
                status = (int)response.StatusCode;
                var body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                if (!response.IsSuccessStatusCode)
                    throw new HttpRequestException($"Preview HTTP {status}. Check the local backend; no fallback or confirm was performed.");
                using var preview = JsonDocument.Parse(body);
                var p = preview.RootElement;
                submissionId = p.GetProperty("submission_id").GetString();
                if (string.IsNullOrWhiteSpace(submissionId) || p.GetProperty("column_mapping").ValueKind != JsonValueKind.Object || p.GetProperty("columns").GetArrayLength() == 0)
                    throw new InvalidDataException("Preview response lacks a submission or column mapping.");
                var mapping = p.GetProperty("column_mapping");
                foreach (var col in p.GetProperty("columns").EnumerateArray())
                    if (string.IsNullOrWhiteSpace(mapping.GetProperty(col.GetString()!).GetProperty("target").GetString()))
                        throw new InvalidDataException("Preview response contains an incomplete mapping.");
                if (p.GetProperty("ai_trace").GetProperty("mode").GetString() != "live")
                    throw new InvalidDataException("Backend did not report live AI interpretation. No fallback accepted.");
                AtomicWrite(Path.Combine(runFolder, "preview.json"), body);
                Save("awaiting_human_review");
                return manifest;
            }
            catch (Exception ex)
            {
                Save("preview_failed", ex is HttpRequestException ? $"HTTP/network failure ({status?.ToString() ?? "no status"}); inspect local backend and reconcile draft before rerun." : ex is System.Threading.Tasks.TaskCanceledException ? "Preview timed out; reconcile draft before rerun." : "Invalid preview response or local output failure; inspect local backend and run artifacts.");
                throw;
            }
        }

        private static void AtomicWrite(string path, string content)
        {
            var temporary = path + ".tmp";
            File.WriteAllText(temporary, content, new UTF8Encoding(false));
            File.Move(temporary, path, true);
        }
    }
}

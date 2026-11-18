#nullable enable
using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Mail;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using UiPath.CodedWorkflows;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public class PrepareReportWork : CodedWorkflow
    {
        // Offline staging only. No transport, RCA provider, API or import dependency.
        [Workflow]
        public string Execute(string configPath)
        {
            var configFile = Path.GetFullPath(configPath);
            var configRaw = File.ReadAllText(configFile);
            var config = JsonNode.Parse(configRaw)!;
            var project = new DirectoryInfo(Path.GetDirectoryName(configFile)!);
            while (project != null && !File.Exists(Path.Combine(project.FullName, "project.json"))) project = project.Parent;
            if (project == null) throw new BusinessRuleException("Configuration must be inside the UiPath project.");
            var inputPath = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(configFile)!, config["input_path"]!.GetValue<string>()));
            var raw = File.ReadAllText(inputPath);
            var data = JsonNode.Parse(raw)!;
            if (data["schema_version"]!.GetValue<int>() != 1 || data["origin"]!.GetValue<string>() != "synthetic-local-fixture" || config["delivery_mode"]!.GetValue<string>() != "draft_only")
                throw new BusinessRuleException("Only explicit synthetic local inputs and draft_only mode are supported.");
            var run = data["run_id"]!.GetValue<string>();
            if (!Regex.IsMatch(run, "^[A-Za-z0-9_-]{1,80}$")) throw new BusinessRuleException("Invalid local run ID.");
            var recipient = config["test_recipient"]!.GetValue<string>();
            var address = new MailAddress(recipient);
            if (address.Address != recipient || !address.Host.EndsWith(".invalid", StringComparison.OrdinalIgnoreCase))
                throw new BusinessRuleException("Offline fixtures require a reserved .invalid recipient.");
            var reading = data["reading"]!;
            foreach (var key in new[] { "fact_id", "kpi_name", "location_name", "date", "division", "actual_value", "target_value", "unit", "source_file", "source_row" })
                if (reading[key] == null) throw new BusinessRuleException("Missing source field: " + key);
            if (reading["division"]!.GetValue<string>() != data["division"]!.GetValue<string>() || reading["date"]!.GetValue<string>() != data["report_date"]!.GetValue<string>())
                throw new BusinessRuleException("Reading scope differs from report scope.");
            if (data["narrative"]!["origin"]!.GetValue<string>() != "synthetic-script-not-live-RCA" || string.IsNullOrWhiteSpace(data["narrative"]!["draft"]!.GetValue<string>()) || data["narrative"]!["references"]!.AsArray().Count == 0)
                throw new BusinessRuleException("Explicit synthetic narrative and source references required.");
            var outputRoot = Path.Combine(project.FullName, "Output", "IndependentReportWork");
            Directory.CreateDirectory(outputRoot);
            using var gate = new FileStream(Path.Combine(outputRoot, run + ".lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            var folder = Path.Combine(outputRoot, run);
            var binding = MappingReview.Hash(raw + "\n" + configRaw);
            var statePath = Path.Combine(folder, "state.json");
            if (Directory.Exists(folder))
            {
                var prior = JsonNode.Parse(File.ReadAllText(statePath))!;
                if (prior["input_config_sha256"]!.GetValue<string>() != binding) throw new BusinessRuleException("Run inputs changed; use a new run ID and review again.");
                foreach (var item in prior["artifacts"]!.AsObject())
                    if (MappingReview.Hash(File.ReadAllText(Path.Combine(folder, item.Key))) != item.Value!.GetValue<string>()) throw new BusinessRuleException("Staged artifact changed; reconcile manually.");
                return statePath;
            }
            var staging = folder + ".preparing";
            if (Directory.Exists(staging)) throw new BusinessRuleException("Incomplete preparation; inspect the .preparing directory before recovery.");
            Directory.CreateDirectory(staging);
            var artifacts = new JsonObject();
            void Write(string name, string text)
            {
                File.WriteAllText(Path.Combine(staging, name), text, new UTF8Encoding(false));
                artifacts[name] = MappingReview.Hash(text);
            }
            var body = "SYNTHETIC LOCAL DRAFT — NOT SENT. No live RCA.\n" + reading.ToJsonString() + "\nRequest feedback for this exact fixture fact_id; no backend feedback was submitted.";
            Write("notification.eml", "To: " + recipient + "\r\nSubject: [SYNTHETIC DRAFT] VantageNet " + run + "\r\nX-Unsent: 1\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" + Convert.ToBase64String(Encoding.UTF8.GetBytes(body)) + "\r\n");
            Write("input-snapshot.json", data.ToJsonString());
            Write("narrative-review.html", "<!doctype html><meta charset=utf-8><title>Synthetic narrative review packet</title><h1>Awaiting human narrative review</h1><p>SYNTHETIC SCRIPT — NOT LIVE RCA. No approval captured. Local review packet only.</p><pre>" + WebUtility.HtmlEncode(data.ToJsonString(new System.Text.Json.JsonSerializerOptions { WriteIndented = true })) + "</pre>");
            Write("pptx-job.json", new JsonObject { ["state"] = "blocked_pending_human_narrative_and_template", ["run_id"] = run, ["submission_id"] = data["submission_id"]!.DeepClone(), ["report_date"] = data["report_date"]!.DeepClone(), ["division"] = data["division"]!.DeepClone(), ["approved_narrative"] = null, ["template_path"] = null, ["snapshot_sha256"] = MappingReview.Hash(data.ToJsonString()), ["output_filename"] = run + ".pptx" }.ToJsonString());
            var state = new JsonObject { ["run_id"] = run, ["input_config_sha256"] = binding, ["state"] = "awaiting_human_narrative_review", ["notification_state"] = "draft_only_not_delivered", ["artifacts"] = artifacts };
            File.WriteAllText(Path.Combine(staging, "state.json"), state.ToJsonString(), new UTF8Encoding(false));
            Directory.Move(staging, folder);
            return statePath;
        }
    }
}

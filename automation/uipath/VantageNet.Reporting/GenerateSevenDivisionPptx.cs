#nullable enable
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json.Nodes;
using System.Xml.Linq;
using UiPath.CodedWorkflows;
using UiPath.Presentations.Activities.API;
using static VantageNet.Reporting.SevenDivisionRun;

namespace VantageNet.Reporting
{
    public class GenerateSevenDivisionPptx : CodedWorkflow
    {
        private sealed record TextSlot(int Slide, string Name, string Text);

        [Workflow]
        public string Execute(string projectFolder, string configPath)
        {
            using var run = new SevenDivisionRun(projectFolder, configPath);
            var (bundle, decision, requestHash) = run.ApprovedReport();
            var filename = $"VantageNet-{S(bundle, "bundle_id")}-{S(bundle, "revision")}.pptx";
            var report = Path.Combine(run.ReportFolder, "report");
            var final = Path.Combine(report, filename);
            var receipt = Path.Combine(report, "generation-receipt.json");
            JsonNode Receipt(string path) => Node(new { request_sha256 = requestHash, pptx_sha256 = HashFile(path),
                decision_sha256 = HashFile(Path.Combine(run.ReportFolder, "narrative-decision.json")),
                approval_mode = S(decision, "decision_mode"), filename, slide_count = 7 });
            if (Directory.Exists(report))
            {
                Need(JsonNode.DeepEquals(Read(receipt), Receipt(final)), "Existing aggregate PowerPoint or receipt changed.");
                return final;
            }
            var pending = Path.Combine(run.ReportFolder, "report.preparing");
            Need(!Directory.Exists(pending), "A previous generation is incomplete. Preserve it and use a new report revision.");
            var slides = Slides(bundle, decision);
            Directory.CreateDirectory(pending);
            var temporary = Path.Combine(pending, filename);
            File.Copy(run.ReportTemplate, temporary);
            using (var ppt = powerpoint.UsePresentationDocument(temporary, false))
                foreach (var item in slides) ppt.AddTextToSlide(item.Slide, item.Name, item.Text, true);
            PreserveTemplateFormatting(temporary, slides);
            WriteNew(Path.Combine(pending, "generation-receipt.json"), Receipt(temporary));
            Directory.Move(pending, report);
            return final;
        }

        private static List<TextSlot> Slides(JsonNode b, JsonNode approval)
        {
            var output = new List<TextSlot>();
            void Add(int slide, string shape, string text) => output.Add(new TextSlot(slide, shape, text));
            string F(JsonNode r, string key) => r[key]!.GetValue<double>().ToString("G", CultureInfo.InvariantCulture) + " " + S(r, "unit");
            var totals = b["totals"]!;
            var divisions = Items(b["divisions"]!).ToArray();
            var rows = Items(b["readings"]!).ToDictionary(r => N(r, "fact_id"));
            var gaps = Items(b["gaps"]!).ToArray();
            var n = b["narrative"]!;
            var meeting = N(totals, "meeting");
            var total = N(totals, "readings");
            var below = N(totals, "below_target");

            Add(1, "Period", "REPORTING DATE  " + S(b, "report_date"));
            Add(1, "Headline", $"{meeting} of {total} readings\nmet target");
            Add(1, "Scope", $"{divisions.Length} divisions     /     {N(totals, "kpis")} KPIs     /     {N(totals, "locations")} locations");
            Add(1, "Summary", $"{below} readings below target");
            Add(1, "ApprovalMode", S(approval, "decision_mode") == "automated-test" ? "AUTOMATED TEST OUTPUT" : "APPROVED MANAGEMENT REPORT");

            for (var i = 0; i < divisions.Length; i++)
            {
                var d = divisions[i];
                Add(2, $"Division{i}", S(d, "division"));
                foreach (var field in new[] { "kpis", "readings", "meeting", "below_target" })
                    Add(2, $"{field}{i}", N(d, field).ToString(CultureInfo.InvariantCulture));
            }

            Add(3, "MetLabel", $"Meeting target   {meeting}");
            Add(3, "MissLabel", $"Below target   {below}");
            Add(3, "MetBar", new string('█', Math.Max(1, (int)Math.Round(48.0 * meeting / total))));
            Add(3, "MissBar", below == 0 ? "0" : new string('█', Math.Max(1, (int)Math.Round(48.0 * below / total))));
            var locations = Items(b["locations"]!).ToArray();
            Need(locations.Length == 2, "The synthetic report template expects two locations.");
            for (var i = 0; i < locations.Length; i++)
            {
                var l = locations[i];
                Add(3, $"Location{i}", $"{S(l, "location")}   /   {N(l, "meeting")} meeting target   /   {N(l, "below_target")} below target");
            }

            for (var i = 0; i < Math.Min(gaps.Length, 5); i++)
            {
                var reading = rows[N(gaps[i], "fact_id")];
                Add(4, $"GapKpi{i}", S(reading, "kpi_name"));
                Add(4, $"GapScope{i}", S(reading, "division") + "\n" + S(reading, "location_name"));
                Add(4, $"GapActual{i}", F(reading, "actual_value"));
                Add(4, $"GapTarget{i}", F(reading, "target_value"));
            }

            var withFeedback = N(b, "shortfalls_with_feedback");
            var aiDraft = S(n, "evidence_status") == "ai_draft";
            var focus = n["fact_id"] == null ? null : rows[N(n, "fact_id")];
            Add(5, "EvidenceScope", $"{withFeedback} of {below} shortfalls have recorded feedback.");
            Add(5, "Focus", focus == null ? "Insufficient evidence" : $"{S(focus, "division")}  /  {S(focus, "kpi_name")}  /  {S(focus, "location_name")}");
            Add(5, "Narrative", aiDraft ? S(n, "root_cause") : "Insufficient evidence to establish a cause for this reporting period.");
            var cited = aiDraft ? Items(n["cited_feedback_ids"]!).Select(id => id.GetValue<int>()).ToHashSet() : new HashSet<int>();
            var sources = Items(b["feedback"]!).Where(f => cited.Contains(N(f, "feedback_id"))).Select(f =>
                $"[{S(f, "reference")}] {(S(f, "origin") == "fixture-worksheet-notes" ? "Synthetic worksheet note" : S(f, "origin"))} · {S(f, "explanation")}");
            Add(5, "Evidence", aiDraft ? string.Join("\n", sources) : "Additional division feedback is required.");
            Add(5, "Model", B(n, "ai_invoked") ? "Model  " + S(n, "llm_model") : "AI draft unavailable without supporting feedback.");

            Add(6, "ActionScope", aiDraft ? S(focus!, "division") + "  /  AI advisory draft" : "Division feedback required");
            Add(6, "Action", aiDraft ? S(n, "prescriptive_action") : "Ask each division with shortfalls for observations and a proposed corrective action.");
            Add(6, "Followup", $"Request supporting observations for the {below - withFeedback} shortfalls without recorded feedback.");

            var submissions = Items(b["submissions"]!).ToArray();
            for (var i = 0; i < submissions.Length; i++)
            {
                var s = submissions[i];
                Add(7, $"SourceDivision{i}", S(s, "division"));
                Add(7, $"Workbook{i}", S(s, "filename"));
                Add(7, $"Submission{i}", S(s, "submission_id"));
            }
            Add(7, "Approval", S(approval, "decision_mode") == "automated-test" ? "Automated test decision recorded" : "Approved by " + S(approval, "reviewer"));
            Add(7, "Trace", $"{S(b, "report_date")}  /  {S(b, "bundle_id")}  /  {S(b, "revision")}  /  Source rows in aggregate-bundle.json");
            return output;
        }

        private static void PreserveTemplateFormatting(string path, List<TextSlot> slots)
        {
            using var archive = ZipFile.Open(path, ZipArchiveMode.Update);
            XNamespace p = "http://schemas.openxmlformats.org/presentationml/2006/main";
            XNamespace a = "http://schemas.openxmlformats.org/drawingml/2006/main";
            for (var slide = 1; slide <= 7; slide++)
            {
                var entry = archive.GetEntry($"ppt/slides/slide{slide}.xml")!;
                XDocument xml;
                using (var stream = entry.Open()) xml = XDocument.Load(stream);
                foreach (var slot in slots.Where(slot => slot.Slide == slide))
                {
                    var shape = xml.Descendants(p + "sp").SingleOrDefault(element =>
                        (string?)element.Element(p + "nvSpPr")?.Element(p + "cNvPr")?.Attribute("name") == slot.Name);
                    Need(shape != null, "Missing PowerPoint shape: " + slot.Name);
                    var paragraphs = shape!.Descendants(a + "p").Select(paragraph => string.Concat(paragraph.Descendants()
                        .Where(node => node.Name == a + "t" || node.Name == a + "br").Select(node => node.Name == a + "br" ? "\n" : node.Value)));
                    Need(string.Join("\n", paragraphs) == slot.Text, "Generated PowerPoint text differs: " + slot.Name);
                    // AddTextToSlide appends a new run without the formatted placeholder's character properties.
                    var styled = shape.Descendants(a + "rPr").FirstOrDefault();
                    Need(styled != null, "Template styling is missing: " + slot.Name);
                    foreach (var run in shape.Descendants(a + "r").Where(run => run.Element(a + "rPr") == null))
                        run.AddFirst(new XElement(styled!));
                }
                using var updated = entry.Open();
                updated.SetLength(0);
                xml.Save(updated);
            }
        }
    }
}

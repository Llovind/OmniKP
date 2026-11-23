#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Xml.Linq;
using UiPath.CodedWorkflows;
using UiPath.Core;
using UiPath.Presentations.Activities.API;
using static VantageNet.Reporting.BackendBundleV2Contract;

namespace VantageNet.Reporting
{
    public class GenerateBackendNarrativePptxV2 : CodedWorkflow
    {
        private sealed record ShapeText(int Slide, string Shape, string Text, int Width, int Rows);

        [Workflow]
        public string Execute(string projectFolder, string bundleId, string revision)
        {
            try
            {
                using var review = new BackendNarrativeV2(projectFolder, bundleId, revision);
                var (decision, decisionHash, requestHash) = review.Approved();
                return Generate(review, decision, decisionHash, requestHash);
            }
            catch (InvalidDataException error)
            {
                throw new BusinessRuleException(error.Message);
            }
        }

        private string Generate(BackendNarrativeV2 review, JsonElement decision, string decisionHash, string requestHash)
        {
            var folder = Path.Combine(review.Folder, "report");
            BackendNarrativeV2.SafePath(folder);
            var filename = "VantageNet-" + NarrativeState.Text(review.Binding, "run_id") + ".pptx";
            var output = Path.Combine(folder, filename);
            var receipt = new JsonObject
            {
                ["binding"] = review.Binding.DeepClone(), ["request_sha256"] = requestHash, ["decision_sha256"] = decisionHash,
                ["reviewed_narrative_sha256"] = Text(decision, "reviewed_narrative_sha256"), ["decision"] = Text(decision, "decision"),
                ["reviewer"] = Text(decision, "reviewer"), ["decided_at"] = Text(decision, "decided_at"),
                ["output_path"] = output, ["state"] = "generated_local_only",
            };
            const string receiptName = "generation-receipt.json";
            if (Directory.Exists(folder))
            {
                receipt["pptx_sha256"] = BackendBundleV2Digest.Sha256(BackendNarrativeV2.Read(output));
                var prior = Parse(BackendNarrativeV2.Read(Path.Combine(folder, receiptName)));
                Require(JsonElement.DeepEquals(prior, JsonSerializer.SerializeToElement(receipt)), "Final PPTX or generation receipt changed.");
                return output;
            }

            var shapes = BuildSlides(review, decision);
            var pending = folder + ".preparing";
            var intent = Path.Combine(review.Folder, "generation-intent.json");
            BackendNarrativeV2.SafePath(intent);
            Require(!File.Exists(intent) && !Directory.Exists(pending), "Incomplete generation exists; preserve it for reconciliation.");
            NarrativeState.SaveNew(intent, (JsonObject)receipt.DeepClone());
            BackendNarrativeV2.CreatePending(pending);
            var temporary = Path.Combine(pending, filename);
            BackendNarrativeV2.Write(temporary, review.TemplateBytes);
            using (var ppt = powerpoint.UsePresentationDocument(temporary, false))
            {
                foreach (var item in shapes) ppt.AddTextToSlide(item.Slide, item.Shape, item.Text, true);
            }
            LayoutSlide3(temporary);
            CheckPptx(temporary, shapes);
            receipt["pptx_sha256"] = BackendBundleV2Digest.Sha256(BackendNarrativeV2.Read(temporary));
            NarrativeState.SaveNew(Path.Combine(pending, receiptName), receipt);
            Directory.Move(pending, folder);
            return output;
        }

        private static ShapeText[] BuildSlides(BackendNarrativeV2 review, JsonElement decision)
        {
            var s = review.Snapshot;
            var k = review.Reading;
            var n = review.Narrative;
            var actualField = Field(k, "actual_value");
            var targetField = Field(k, "target_value");
            Require(Boolean(k, "chart_supported") && actualField.ValueKind == JsonValueKind.Number && targetField.ValueKind == JsonValueKind.Number,
                "Admitted values are unsupported by the provisional chart.");
            var actual = actualField.GetDouble();
            var target = targetField.GetDouble();
            Require(double.IsFinite(actual) && double.IsFinite(target) && actual >= 0 && target > 0, "Admitted values are unsupported by the provisional chart.");
            var scale = Math.Max(actual, target);
            string Bar(double value) => new string('■', (int)Math.Round(34 * (value / scale)));
            var unit = Text(k, "unit");
            string WithUnit(JsonElement value) => value.GetRawText() + (unit.Length == 0 ? "" : " " + unit);
            var references = new List<string>();
            foreach (var reference in Field(n, "references").EnumerateArray())
            {
                var origin = Text(reference, "origin") switch
                {
                    "fixture-worksheet-notes" => "Worksheet-derived note",
                    "operator-api" => "Operator API feedback",
                    _ => throw new InvalidDataException("Unsupported feedback origin in reference."),
                };
                references.Add($"{Text(reference, "id")} | {origin}\n{Text(reference, "text")}");
            }
            Require(references.Count > 0, "Admitted draft must contain references.");
            const string label = "VANTAGENET | BACKEND-CONFIRMED READING";
            var shapes = new[]
            {
                new ShapeText(1, "TestLabel", label, 75, 1),
                new ShapeText(1, "Scope", $"Period {Text(s, "report_date")} | Division {Text(s, "division")}\nSubmission {Text(s, "submission_id")}\nBundle {NarrativeState.Text(review.Binding, "run_id")}", 59, 5),
                new ShapeText(1, "KPI", $"{Text(k, "kpi_name")}\nFact {Text(k, "fact_id")} | {Text(k, "location_name")}\nStatus {Text(k, "status")}", 48, 3),
                new ShapeText(1, "Comparison", $"Actual {WithUnit(actualField)}\n{Bar(actual)}\nTarget {WithUnit(targetField)}\n{Bar(target)}\nBars share a zero baseline and common scale", 64, 7),
                new ShapeText(2, "TestLabel", label, 75, 1),
                new ShapeText(2, "Narrative", Text(decision, "reviewed_narrative"), 52, 9),
                new ShapeText(2, "Decision", $"AI-assisted draft | Model {Text(n, "llm_model")}\nApproved by {Text(decision, "reviewer")}\n{Text(decision, "decided_at")}\nRationale {Text(decision, "reason")}", 75, 6),
                new ShapeText(3, "TestLabel", label, 75, 1),
                new ShapeText(3, "Source", $"Workbook {Text(k, "source_file")} | Row {Integer(k, "source_row")}\n{Text(k, "division")} | {Text(k, "date")} | {Text(k, "location_name")}\nFact {Text(k, "fact_id")} | Bundle {NarrativeState.Text(review.Binding, "run_id")}\nOperator API origins identify the submission channel.", 63, 8),
                new ShapeText(3, "References", string.Join("\n", references), 58, 12),
            };
            foreach (var item in shapes)
                Require(BackendNarrativeV2.Fits(item.Text, item.Width, item.Rows), "Content exceeds provisional template capacity: " + item.Shape);
            return shapes;
        }

        private static void LayoutSlide3(string path)
        {
            using var zip = ZipFile.Open(path, ZipArchiveMode.Update);
            var entry = zip.GetEntry("ppt/slides/slide3.xml") ?? throw new InvalidDataException("Missing slide3.xml.");
            XDocument xml;
            using (var stream = entry.Open())
            {
                xml = XDocument.Load(stream, LoadOptions.PreserveWhitespace);
            }
            XNamespace p = "http://schemas.openxmlformats.org/presentationml/2006/main";
            XNamespace a = "http://schemas.openxmlformats.org/drawingml/2006/main";
            var source = xml.Descendants(p + "sp").SingleOrDefault(node =>
                (string?)node.Element(p + "nvSpPr")?.Element(p + "cNvPr")?.Attribute("name") == "Source")
                ?? throw new InvalidDataException("Missing Slide 3 Source shape.");
            source.Element(p + "spPr")?.Element(a + "xfrm")?.Element(a + "ext")?.SetAttributeValue("cy", "1645920");

            var references = xml.Descendants(p + "sp").SingleOrDefault(node =>
                (string?)node.Element(p + "nvSpPr")?.Element(p + "cNvPr")?.Attribute("name") == "References")
                ?? throw new InvalidDataException("Missing Slide 3 References shape.");
            var xfrm = references.Element(p + "spPr")?.Element(a + "xfrm")
                ?? throw new InvalidDataException("Missing Slide 3 References transform.");
            xfrm.Element(a + "off")?.SetAttributeValue("y", "2834640");
            xfrm.Element(a + "ext")?.SetAttributeValue("cy", "3383280");
            foreach (var rpr in references.Descendants().Where(node => node.Name == a + "defRPr" || node.Name == a + "rPr"))
                rpr.SetAttributeValue("sz", "1500");
            foreach (var run in references.Descendants(a + "r").Where(node => node.Element(a + "rPr") is null))
                run.AddFirst(new XElement(a + "rPr", new XAttribute("sz", "1500")));

            entry.Delete();
            var updated = zip.CreateEntry("ppt/slides/slide3.xml");
            using var outStream = updated.Open();
            xml.Save(outStream);
        }

        private static void CheckPptx(string path, ShapeText[] expected)
        {
            using var zip = ZipFile.OpenRead(path);
            var slides = zip.Entries.Where(entry => Regex.IsMatch(entry.FullName, @"\Appt/slides/slide[0-9]+\.xml\z")).ToArray();
            Require(slides.Length == 3, "Generated presentation must contain three slides.");
            XNamespace p = "http://schemas.openxmlformats.org/presentationml/2006/main";
            XNamespace a = "http://schemas.openxmlformats.org/drawingml/2006/main";
            foreach (var group in expected.GroupBy(item => item.Slide))
            {
                using var stream = zip.GetEntry($"ppt/slides/slide{group.Key}.xml")!.Open();
                var xml = XDocument.Load(stream, LoadOptions.PreserveWhitespace);
                foreach (var item in group)
                {
                    var shape = xml.Descendants(p + "sp").SingleOrDefault(node =>
                        (string?)node.Element(p + "nvSpPr")?.Element(p + "cNvPr")?.Attribute("name") == item.Shape);
                    Require(shape is not null, "Missing generated PowerPoint shape: " + item.Shape);
                    var paragraphs = shape!.Descendants(a + "p").Select(paragraph =>
                        string.Concat(paragraph.Descendants().Where(node => node.Name == a + "t" || node.Name == a + "br")
                            .Select(node => node.Name == a + "br" ? "\n" : node.Value)));
                    Require(string.Join("\n", paragraphs) == item.Text, "Generated PowerPoint text differs: " + item.Shape);
                }
            }
        }
    }
}

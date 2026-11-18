using System;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using UiPath.CodedWorkflows;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public class PreviewReport : CodedWorkflow
    {
        [Workflow]
        public string Execute(string configPath)
        {
            var manifest = PreviewIntake.Run(configPath);
            using var config = JsonDocument.Parse(File.ReadAllText(configPath));
            MappingReview.Run(manifest, config.RootElement.GetProperty("base_url").GetString(), "");
            return manifest;
        }
    }
}

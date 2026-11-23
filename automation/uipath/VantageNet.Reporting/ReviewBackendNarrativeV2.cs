#nullable enable
using System;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public class ReviewBackendNarrativeV2 : CodedWorkflow
    {
        [Workflow]
        public string Execute(string projectFolder, string bundleId, string revision, string decisionPath = "")
        {
            try
            {
                using var review = new BackendNarrativeV2(projectFolder, bundleId, revision);
                return string.IsNullOrWhiteSpace(decisionPath) ? review.Prepare() : review.Record(decisionPath);
            }
            catch (InvalidDataException error)
            {
                throw new BusinessRuleException(error.Message);
            }
        }
    }
}

using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class ReviewMapping : CodedWorkflow
    {
        [Workflow]
        public string Execute(string manifestPath, string baseUrl, string decisionPath = "")
        {
            return MappingReview.Run(manifestPath, baseUrl, decisionPath);
        }
    }
}

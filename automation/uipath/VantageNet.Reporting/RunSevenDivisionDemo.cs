#nullable enable
using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class RunSevenDivisionDemo : CodedWorkflow
    {
        [Workflow]
        public string Execute(string projectFolder, string configPath, string decisionPath = "")
        {
            using var run = new SevenDivisionRun(projectFolder, configPath);
            return run.Advance(decisionPath);
        }
    }
}

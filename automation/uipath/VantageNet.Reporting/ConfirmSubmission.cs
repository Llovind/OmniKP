using UiPath.CodedWorkflows;

namespace VantageNet.Reporting
{
    public class ConfirmSubmission : CodedWorkflow
    {
        [Workflow]
        public string Execute(string manifestPath, string baseUrl, string approvalPath)
        {
            return ControlledConfirm.Run(manifestPath, baseUrl, approvalPath);
        }
    }
}

#nullable enable
using System;
using System.IO;
using System.Net.Http;
using UiPath.CodedWorkflows;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public class SubmitOperatorFeedback : CodedWorkflow
    {
        [Workflow]
        public string Execute(string projectFolder, string decisionPath = "", bool authorizePost = false)
        {
            try
            {
                using var handler = BackendBundleV2Admission.CreateTransport();
                using var client = new HttpClient(handler);
                return OperatorFeedbackAcceptance.Run(client, projectFolder, decisionPath, authorizePost, TimeProvider.System)
                    .GetAwaiter().GetResult();
            }
            catch (InvalidDataException error)
            {
                throw new BusinessRuleException(error.Message);
            }
        }
    }
}

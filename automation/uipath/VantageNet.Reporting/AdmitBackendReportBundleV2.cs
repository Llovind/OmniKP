#nullable enable
using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using UiPath.CodedWorkflows;
using UiPath.Core;

namespace VantageNet.Reporting
{
    public class AdmitBackendReportBundleV2 : CodedWorkflow
    {
        [Workflow]
        public string Execute(string projectFolder, string backendOrigin, int domainId, string expectedInstanceId,
            string expectedDatabase, string submissionId, long factId, string bundleId, string revision)
        {
            try
            {
                var selection = new BackendBundleV2Selection(backendOrigin, domainId, expectedInstanceId,
                    expectedDatabase, submissionId, factId, bundleId, revision);
                using var handler = BackendBundleV2Admission.CreateTransport();
                using var client = new HttpClient(handler);
                using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(100));
                return BackendBundleV2Admission.FetchAndStage(client, selection, projectFolder, deadline.Token)
                    .GetAwaiter().GetResult();
            }
            catch (InvalidDataException error)
            {
                throw new BusinessRuleException(error.Message);
            }
            catch (HttpRequestException)
            {
                throw new BusinessRuleException("Pinned disposable backend is unavailable. Review the request outcome before a retry.");
            }
            catch (OperationCanceledException)
            {
                throw new BusinessRuleException("Pinned backend request timed out. Review the request outcome before a retry.");
            }
        }
    }
}

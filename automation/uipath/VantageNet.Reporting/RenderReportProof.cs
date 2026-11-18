using UiPath.CodedWorkflows;
using UiPath.Presentations.Activities.API;

namespace VantageNet.Reporting
{
    public class RenderReportProof : CodedWorkflow
    {
        // Explicit local rendering verification; never sends or modifies the source report.
        [Workflow]
        public string Execute(string pptxPath, string pdfPath)
        {
            NarrativeState.Require(!System.IO.File.Exists(pdfPath), "Render proof already exists; preserve prior evidence.");
            using var ppt = powerpoint.UsePowerPointPresentation(pptxPath, false, false);
            ppt.SavePresentationAsPDF(pdfPath, false);
            return pdfPath;
        }
    }
}

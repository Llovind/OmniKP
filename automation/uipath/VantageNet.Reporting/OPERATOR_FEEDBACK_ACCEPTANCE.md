# Attended operator feedback acceptance

Send the approved synthetic scenario for confirmed ED fact 12 through the existing
feedback endpoint. The UiPath entry point is SubmitOperatorFeedback.cs. Its only
required input is projectFolder, the VantageNet.Reporting directory. The instance,
database, submission, workbook fingerprint, and fact are pinned in source for
this acceptance case.

1. After authorization to access the acceptance backend, run with projectFolder
   alone. This uses GET for instance and ledger verification and returns the path
   to the local review form. Open the form, review the fixed text and reading,
   check the acknowledgment, and save its decision file. The form has no backend
   transport.
2. After separate authorization for one POST, run with the same projectFolder,
   the absolute decisionPath, and authorizePost=true. The workflow validates the
   decision and checks that the fact still has zero feedback. It archives a durable
   write intent before attempting the POST and verifies the result with GET.
3. To reconcile an existing attempt, run with projectFolder alone. This branch
   uses GET regardless of supplied submission arguments. A missing, mismatched,
   or duplicate record leaves the case for manual reconciliation. Keep the attempt
   directory and inspect its evidence before deciding how to proceed.

Artifacts are under Output/OperatorFeedback/vantagenet-acceptance-20261121-e63c/
gate3-ed-fact12/. The review request binds the exact payload and form. The attempt
preserves the decision, write intent, and baseline. Its POST and GET archives
contain HTTP metadata, exact response bytes as base64, and SHA-256 hashes. A
verification receipt either identifies the verified feedback or reports the
reconciliation failure. A separate receipt status identifies GET recovery after
an ambiguous POST. Each verification has its own directory.

The backend assigns operator-api to this submission channel. The payload, local
audit records, and downstream v2 review carry the synthetic scenario label.
The label identifies hypothetical test input and carries no authentication claim.

## Offline verification

Run Tests/test_operator_feedback.ps1 in PowerShell 7 on .NET 10. It compiles the
production C# logic with an in-process mock HTTP handler and uses temporary
fixtures. Run node Tests/test_operator_feedback_form.mjs for the review-form
checks. The tests use fabricated decisions and do not invoke UiPath admission,
generate a report, or use live HTTP.

# Backend v2 attended narrative and PowerPoint

Start with the project folder, bundle ID, and current revision already staged by the v2 admission workflow. The review and generation workflows use those three inputs to find the controlled admission directory. They run offline.

1. Run `ReviewBackendNarrativeV2.cs` with `projectFolder`, `bundleId`, and `revision`. Open its returned local HTML file in a browser with Web Crypto enabled.
2. Inspect the confirmed reading, exact fact, feedback origins, citations, provider outcome, and original draft. Edit the proposed narrative, provide a reviewer name or ID and a reason, and explicitly choose a decision. Download the decision JSON.
3. Run the same review workflow with the absolute `decisionPath` of that file. Each revision accepts one terminal decision. A request for revision or rejection needs a new admitted revision before another review. An identical decision file replays its archived result.
4. Run `GenerateBackendNarrativePptxV2.cs` with the same project, case, and revision. It uses the recorded approval and returns the local presentation path. Run `RenderReportProof.cs` with that PPTX path and a fresh PDF path. Inspect the three rendered pages against the approved text and the admitted reading.

Review files and generated reports are under `Output/BackendNarrativeReviewV2/case-<bundleId>/<revision>/`. The admission directory is read under its existing case lock. Review and generation both recheck that the requested revision is current, the bundle and snapshot hashes match, and the snapshot belongs to the archive. A higher admitted revision supersedes old approvals even when the new revision is blocked. Earlier artifacts remain available as evidence.

The decision binds the request ID and SHA-256, case and revision, bundle and admission state hashes, snapshot hash, submission and fact IDs, original draft, edited narrative, form template, PPTX template, reviewer, decision, reason, and UTC timestamp. The existing provisional PPTX is pinned by content. Reviewer identity is locally asserted. Decisions have a 24-hour validation window and follow the preparation timestamp.

Generation checks text capacity and chart eligibility before writing, then verifies the generated three-slide shape text before publishing the report and receipt together. The receipt identifies the approved decision and output hash, and a replay verifies both. A failed generation can leave an intent and a pending directory for manual reconciliation. Keep those files and investigate before making another attempt. Rendering and inspection are separate from the generation receipt.

`Tests/test_backend_narrative_v2.py` exercises native offline workflows against temporary directories with explicitly fabricated test decisions and archived v2 fixtures. Its report and render evidence belong to the regression only.

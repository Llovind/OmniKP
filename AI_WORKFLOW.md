# Integrated AI workflow

The review branch now uses one product workflow. Every uploaded report is interpreted by the configured model before analyst review, validation and confirmation. The previous use_ai request field remains accepted for older clients, but false cannot bypass AI. Approved mapping records no longer bypass model interpretation.

Try demo interprets the same seven synthetic divisional reports with the model before consolidating them. Repeated opens reuse that AI-prepared dataset; Reset demo regenerates its mappings with the provider. All model calls finish before replacing the existing synthetic demo. A preparation failure is visible and does not silently substitute rule mappings. Confirmation still validates readings; an incorrect model interpretation can require retry or analyst review.

On opening the populated demo, the workspace selects the ED shortfall with fixture feedback and requests its AI draft automatically. Normal reading selection and feedback submission use the same RCA endpoint. The model must cite attached feedback. Missing feedback requests evidence; missing provider, provider failure or invalid citations returns a visible error rather than a non-AI explanation.

Provider credentials remain in ignored backend/.env. No key is returned by the configuration endpoint. Model: gemini-flash-lite-latest, from the user's existing local configuration.

Local main integration includes the AI trace, per-column reasons, `/evaluation`,
and the Docker/static hosting support. Historical benchmark recordings remain
available as evidence, but never substitute live interpretation. RCA reports an
actual model invocation even when the response abstains, and exposes structural
citation checks instead of an unmeasured “ungrounded claims” count. Direct demo
visits prepare the dataset on demand; backend startup does not call the provider.

Verification: live seed interpreted all seven reports and produced 180 readings matching the fixture reference (actual, target, unit, source row and target status). Browser checks exercised the normal Try demo and Upload report flows, verified automatic AI RCA, zero AI opt-out checkboxes, and seven model-generated ED column suggestions. Build, lint and typecheck were run. Backend tests mock the provider and cover required-AI intake, duplicate protection, provider failure, citation rejection, AI draft success, seed idempotency and reset behavior. Synthetic input content is used for live checks.

The original UI work is preserved in local checkpoint dc73f39 on review/ui-refinement-v2.
It is integrated with the latest remote main in C:\KPI_Dashboard. This integration
is local and has not been pushed or deployed.

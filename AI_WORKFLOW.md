# Integrated AI workflow

The review branch now uses one product workflow. Every uploaded report is interpreted by the configured model before analyst review, validation and confirmation. The previous use_ai request field remains accepted for older clients, but false cannot bypass AI. Approved mapping records no longer bypass model interpretation.

Try demo interprets the same seven synthetic divisional reports with the model before consolidating them. Repeated opens reuse that AI-prepared dataset; Reset demo regenerates its mappings with the provider. All model calls finish before replacing the existing synthetic demo. A preparation failure is visible and does not silently substitute rule mappings. Confirmation still validates readings; an incorrect model interpretation can require retry or analyst review.

On opening the populated demo, the workspace selects the ED shortfall with fixture feedback and requests its AI draft automatically. Normal reading selection and feedback submission use the same RCA endpoint. The model must cite attached feedback. Missing feedback requests evidence; missing provider, provider failure or invalid citations returns a visible error rather than a non-AI explanation.

Provider credentials remain in ignored backend/.env. No key is returned by the configuration endpoint. Model: gemini-flash-lite-latest, from the user's existing local configuration.

Verification: live seed interpreted all seven reports and produced 180 readings matching the fixture reference (actual, target, unit, source row and target status). Browser checks exercised the normal Try demo and Upload report flows, verified automatic AI RCA, zero AI opt-out checkboxes, and seven model-generated ED column suggestions. Build, lint and typecheck were run. Backend tests mock the provider and cover required-AI intake, duplicate protection, provider failure, citation rejection, AI draft success, seed idempotency and reset behavior. Synthetic input content is used for live checks.

All work is local to C:\KPI_Dashboard_UI_Review and is uncommitted. It has not been merged or deployed.

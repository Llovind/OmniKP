# Seven-division implementation plan

The current Windows coded-workflow project already supports local HTML decisions, disposable identity checks and PowerPoint template filling. Its controlled confirmation is pinned to ED, and its v2 bundle and PowerPoint describe one fact. The seven-division workflow will use separate entry points and artifacts. The frozen Gate 3D.1 revision stays outside the new run directories.

1. Stage a disposable database and configurable division folders. Add a batch entry point and durable per-file state. Reuse the existing multipart preview, mapping validation, confirmation and detail endpoints. Add an optional caller-assigned preview ID so interrupted writes can be checked against the ledger.
2. Capture one date-scoped backend snapshot from confirmed submissions and exact-fact evidence. Compare the confirmed IDs, scope and reading totals with the robot ledger. Reconcile the complete reading set with the independent expected workbook.
3. Prepare browser-based mapping, import and narrative decisions. Bind decisions to the exact request and preserve them with the run. Fill a dedicated aggregate PowerPoint template only after narrative approval.
4. Run the installed robot and FastAPI against the disposable database, with a configured live provider. Exercise malformed inputs, rejection, replay and interrupted confirmation. Render the final report through the installed PowerPoint workflow and retain the proof.

Live inference availability and response quality can block drafting. An interrupted preview may create a draft without a locally captured AI proposal. Confirmations must be reconciled with the submission detail before any further action. The runbook will distinguish supervised local decisions from test decisions and identify all remaining recording steps.

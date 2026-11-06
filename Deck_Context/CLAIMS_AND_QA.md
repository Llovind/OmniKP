# Claims, evidence and likely Q&A

## Use claims like these

- “The prototype accepts divisional Excel and CSV reports, lets an analyst review column mappings, validates readings, and records confirmed data with source attribution.”
- “Our synthetic validation pack has seven reconstructed division reports, 90 KPIs and 180 readings.”
- “The fixtures preserve the reference workbook's KPI names, units, directions and submitting-unit grouping. The readings, targets, feedback and locations are fictional.”
- “AI proposes report-column meanings, with a short reason for each column. The analyst confirms them before import.”
- “The interface reports whether suggestions came from a live call, a labelled recorded run, or were skipped.”
- “On five synthetic layouts, local rules mapped 0 of 7 unfamiliar headers; the configured model mapped 7 of 7 and 6 of 7 when the same headers were reordered.”
- “RCA drafts use feedback attached to an exact KPI, location and date. Without feedback, the prototype returns insufficient evidence and does not call the model.”
- “Our reference comparison checks fixture import correctness. We have not measured analyst time saved or real-report AI accuracy.”

## Avoid these claims

| Avoid | Why | Safer wording |
|---|---|---|
| “AI consolidates all telecom data” | Data confirmation and consolidation are application logic; supported layouts are bounded | “The prototype consolidates validated reports and uses AI to suggest column meanings.” |
| “AI finds the root cause” | The system uses division feedback and cannot independently establish causality | “It drafts an attributed explanation from submitted feedback for analyst review.” |
| “It predicts outages” | Forecasting is not implemented | “The dashboard checks target attainment and statistical deviations in available history.” |
| “It saves X hours / reduces downtime by X%” | No comparative field measurement exists | “Time savings are a hypothesis we plan to test against manual consolidation.” |
| “AI mapping is 96% accurate” | The only measured figure is a five-layout synthetic benchmark, not real reports | “On our five synthetic layouts, the provider mapped unfamiliar headers 7/7 and reordered 6/7; real-report accuracy is unmeasured.” |
| “The demo you see is live AI” | Recorded suggestions may be replayed when no key is configured | “Each suggestion is labelled live or recorded; the trace states which path ran.” |
| “Validated on Infranexia data” | Public demo fixtures are synthetic; no operational validation is documented | “Inspired by an internship workflow; the demo uses reconstructed synthetic reports.” |
| “Production-ready / enterprise SaaS” | Prototype has no production deployment controls or authentication | “A competition prototype demonstrating an intake-to-review workflow.” |
| “Compliant with SDG 9” | Product contribution is indirect; it does not measure official SDG indicators | “The intended contribution is better visibility into KPI reporting for infrastructure operations.” |

## Likely judge questions

### What is the AI innovation?

The AI is used at two interpretation points. During intake, a pretrained language model can suggest meanings for unfamiliar report columns from headers and up to three sample values per column, and it must return a short reason per column. Every response carries a trace: which mode ran (live, recorded, skipped), the model, the column and sample scope, batches and latency. Later, if division feedback is attached to a selected KPI reading, an optional model can draft an attributed explanation with feedback references. Deterministic code validates data, blocks duplicates, calculates target status and statistical history. The analyst reviews the mapping and the RCA draft. The innovation claim is bounded: interpretation placed inside a reviewed, traceable workflow.

### Why use AI instead of rules?

Known headers can use local aliases and fuzzy matching. Reports can use different labels and combinations of header rows, units, targets and locations. AI can propose mappings for unfamiliar labels; the analyst still reviews them. On the five synthetic layouts, local rules mapped conventional and Indonesian headers perfectly but mapped none of the unfamiliar or reordered headers, while the configured model mapped all seven unfamiliar headers and six of seven reordered ones. That is a synthetic result, not real-report validation.

### What if the AI provider is unavailable during the demo?

The interface states the mode instead of faking a live call. Without a key, the seven demo header signatures replay recorded provider output and are labelled “AI suggestion · recorded”; unknown layouts show the skipped state. With a key, the trace reports a live call and its latency. A provider failure mid-request keeps local rules and reports the failed batch.

### Does it know the cause of a KPI miss?

No. A KPI shortfall alone does not establish cause. omniKPI asks for division feedback linked to the exact reading. It can summarize or draft from that feedback and show its references. It labels reported explanations as unverified and asks for more evidence when feedback is missing or inadequate.

### How did you validate it?

Two separate checks. First, we reconstructed seven synthetic reports from the structure of a June WISA reference workbook. An independent script calculated the expected output from exported fixture cells, then integration checks compared imported readings and attribution against that reference. This validates the demo path, not AI generalization.

Second, `backend/evidence/mapping-benchmark-live.json` records a synthetic mapping benchmark: five authored layouts, three repeats, local rules versus `google/gemini-2.5-flash-lite`. Rules scored 7/7 on conventional and Indonesian headers, 0/7 on unfamiliar and reordered headers, 9/9 on the wide layout. The provider scored 7/7, 7/7, 7/7, 6/7 and 9/9 at roughly 1.5–2 s per preview. This is not a held-out or real-report benchmark, not a model comparison, and not a time-saving measurement. The layouts are synthetic and two of them share vocabulary.

### Are these real Infranexia reports?

No. The project motivation comes from an internship experience. The public demo contains reconstructed synthetic inputs. KPI labels, units, directions and submitting-unit grouping follow a reference structure, while readings, targets, feedback and locations are fictional. The files are explicitly not recovered original divisional templates.

### What data and safeguards are needed?

Each submission needs the reporting unit, report date, KPI identity, actual value, unit and target or a defined target source, plus location where applicable. The analyst reviews mappings and validation before confirmation. Feedback should be tied to the specific reading and attributed to its division. The current prototype does not verify user identity or division authority.

### How does this relate to SDG 9?

The strongest fit is an indirect link to Target 9.1 through the work of teams monitoring infrastructure reliability. Target 9.c is relevant sector context for telecom, but omniKPI does not measure population coverage or affordability. The prototype does not calculate official SDG indicators or prove better service outcomes. Use [SDG 9 position](SDG_9_POSITION.md) for the approved explanation.

### Your submitted proposal included more modules. Why are they missing?

The proposal described a broader system and listed implementation states for its components. The current demo narrowed to the divisional spreadsheet workflow that can be exercised and checked end to end: report intake, reviewed mappings, validation, consolidation, provenance and feedback-linked drafts. Modules such as Isolation Forest, hybrid embedding retrieval, cross-KPI incident grouping, Case Library, recovery verification and facility-level SDG indicators are not part of the current demonstrated scope. Explain the narrowing clearly and present those items only as future work if needed.

### Why is this still an AI innovation if consolidation is the central product value?

The reporting workflow is the product problem. AI addresses a specific source of friction inside it: interpreting inconsistent report headers and, when feedback exists, drafting a referenced explanation. If the input layouts always had identical headers, local rules could handle more of the work. With unfamiliar layouts, AI suggestions can help, while analyst approval and deterministic validation control what enters the dataset. The deck should show that bounded role instead of calling the entire system AI.

### What would you test next?

Use owner-approved, sanitized divisional reports and independently reviewed expected outputs. Have analysts complete matched manual and assisted consolidation tasks. Record corrections, failed layouts, final value accuracy and elapsed task time, including review and retries. Report the sample size and failures before making a time-saving or accuracy claim.

## Q&A posture

Answer with the current behavior first, then its limit, then the next validation step. If a feature is planned, call it planned. If the answer depends on deployment policy or data access, say what would need to be decided instead of guessing.

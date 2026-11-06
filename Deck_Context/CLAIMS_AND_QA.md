# Claims, evidence and likely Q&A

## Use claims like these

- “The prototype accepts divisional Excel and CSV reports, lets an analyst review column mappings, validates readings, and records confirmed data with source attribution.”
- “Our synthetic validation pack has seven reconstructed division reports, 90 KPIs and 180 readings.”
- “The fixtures preserve the reference workbook's KPI names, units, directions and submitting-unit grouping. The readings, targets, feedback and locations are fictional.”
- “AI proposes report-column meanings. The analyst confirms them before import.”
- “RCA drafts use feedback attached to an exact KPI, location and date. Without feedback, the prototype returns insufficient evidence.”
- “Our reference comparison checks fixture import correctness. We have not measured analyst time saved or real-report AI accuracy.”

## Avoid these claims

| Avoid | Why | Safer wording |
|---|---|---|
| “AI consolidates all telecom data” | Data confirmation and consolidation are application logic; supported layouts are bounded | “The prototype consolidates validated reports and uses AI to suggest column meanings.” |
| “AI finds the root cause” | The system uses division feedback and cannot independently establish causality | “It drafts an attributed explanation from submitted feedback for analyst review.” |
| “It predicts outages” | Forecasting is not implemented | “The dashboard checks target attainment and statistical deviations in available history.” |
| “It saves X hours / reduces downtime by X%” | No comparative field measurement exists | “Time savings are a hypothesis we plan to test against manual consolidation.” |
| “Validated on Infranexia data” | Public demo fixtures are synthetic; no operational validation is documented | “Inspired by an internship workflow; the demo uses reconstructed synthetic reports.” |
| “Production-ready / enterprise SaaS” | Prototype has no production deployment controls or authentication | “A competition prototype demonstrating an intake-to-review workflow.” |
| “Compliant with SDG 9” | Product contribution is indirect; it does not measure official SDG indicators | “The intended contribution is better visibility into KPI reporting for infrastructure operations.” |

## Likely judge questions

### What is the AI innovation?

The AI is used at two interpretation points. During intake, a pretrained language model can suggest meanings for unfamiliar report columns from headers and up to three sample values per column. Later, if division feedback is attached to a selected KPI reading, an optional model can draft an attributed explanation with feedback references. Deterministic code validates data, blocks duplicates, calculates target status and statistical history. The analyst reviews the mapping and the RCA draft.

### Why use AI instead of rules?

Known headers can use local aliases and fuzzy matching. Reports can use different labels and combinations of header rows, units, targets and locations. AI can propose mappings for unfamiliar labels; the analyst still reviews them. The prototype should be tested on approved, varied reports before claiming generalization.

### Does it know the cause of a KPI miss?

No. A KPI shortfall alone does not establish cause. omniKPI asks for division feedback linked to the exact reading. It can summarize or draft from that feedback and show its references. It labels reported explanations as unverified and asks for more evidence when feedback is missing or inadequate.

### How did you validate it?

We reconstructed seven synthetic reports from the structure of a June WISA reference workbook. An independent script calculated the expected output from exported fixture cells, then integration checks compared imported readings and attribution against that reference. This validates the demo path, not AI generalization, real-world accuracy or time savings.

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

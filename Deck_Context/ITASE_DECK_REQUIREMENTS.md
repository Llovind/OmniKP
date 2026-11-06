# ITASE 7.0 final deck: required content and judging

This file combines the final-round event briefing images in `Documents/` with the ITASE guidebook. If organizers have since issued an update, follow that update.

## Submission and format

- Submit the presentation as PDF or PPTX.
- The event-day briefing lists the deadline as 6 November 2026 at 23:59 WIB.
- The final presentation is online on 7 November 2026.
- The presentation slot is ten minutes, followed by ten minutes of Q&A.
- Confirm the current submission link, file-size rules, presentation order and technical setup with the organizers. The local images do not specify these details.

## Required deck sections

The event-day briefing explicitly lists eight sections. Make every section easy to find, even if one slide covers more than one item.

| Required section | What the deck should establish | Evidence from this project |
|---|---|---|
| Cover | Innovation title, team, members and university | omniKPI; Team Mejeuh Euy; Lovind Luthfan Hakeem Firdaus, Faiz Aditia Zain, Muhammad Lazuardi; Telkom University Bandung |
| Problem identification | Who handles the reports, what is fragmented, and where manual work happens | User's internship account; a before-flow showing division spreadsheets being combined by an analyst |
| Solution concept and innovation | What changes in the workflow and what is distinct | One reviewed, source-traceable KPI dataset from multiple divisional submissions; AI-assisted schema interpretation at intake |
| Use of artificial intelligence | Model type, input, output, reason for use, human review and boundaries | Optional pretrained LLM sees headers and up to three sample values per column; it proposes mappings. Optional feedback-grounded RCA drafting is attributed and checked. Rules handle validation and calculations. Name the model/provider actually configured for the presentation, not just the code default |
| Design and system workflow | System components, data path and product demonstration | Upload -> map -> review -> validate -> confirm -> shared dashboard -> division feedback -> RCA draft |
| Implementation feasibility | Users, required data, fit with current workflow, technical approach, safeguards and next validation | Excel/CSV intake, analyst confirmation, source attribution, synthetic validation pack; deployment and identity controls remain future work |
| Contribution to the SDGs | Which SDG 9 target is relevant, the pathway, and what is not measured | Explain the indirect link to resilient digital infrastructure operations; see [SDG 9 position](SDG_9_POSITION.md) |
| Conclusion | Restate the problem, what the prototype demonstrates and the next proof needed | Close on reviewed divisional reporting and a proposed human comparison study, with no unmeasured impact claim |

The event-day briefing does not prescribe slide count, visual theme or a required section order.

### AI explanation checklist

The guidebook requires the solution to use AI as a core part of addressing the problem and asks teams to explain its mechanism, why they selected the technology and what role it plays. The AI slide or spoken narration should cover:

- **Problem where AI helps:** divisional reports may use differing or unfamiliar column names.
- **Input:** headers plus up to three sample values per column when an authorized user opts into AI mapping.
- **Output:** proposed schema meanings for analyst review and correction.
- **Model:** identify the provider and model configured for the live demo. Check `GET /api/v1/ai/status` before presenting; it reports the active mode (`live`, `recorded`, `skipped`) and model. The committed benchmark used `google/gemini-2.5-flash-lite`, but confirm the deployed value. Do not claim the code default is necessarily the live model.
- **Honesty about the fallback:** if the deployed demo has no key, the interface replays recorded suggestions labelled “AI suggestion · recorded”. Say that explicitly instead of presenting replay as live inference.
- **Why this class of model:** language models can interpret unfamiliar labels from context and return structured mapping suggestions; a pretrained model avoids training a bespoke model for this prototype. Do not imply a comparative model study established superiority.
- **Control:** AI suggests; deterministic validation and an analyst's confirmation control import. RCA drafts use only attached division feedback, and the model may be unavailable.
- **Data handling:** explain that AI mapping is opt-in and may send the bounded headers and sample values to the configured provider. Do not claim on-premise processing, masking or production privacy controls unless those are actually configured and tested.

The repository includes legacy model-selection comments referring to a shift-log retrieval flow. Those comments are not a substitute for checking the current environment and product flow.

## Two rubrics for two stages

### Final-round rubric from the event-day briefing

| Criterion | Weight | What the team controls |
|---|---:|---|
| PPT completeness | 20% | Cover and all seven content sections above; readable evidence, labels and source notes |
| Presentation | 50% | A clear ten-minute story, confident explanation, useful demo, pacing and team delivery |
| Q&A | 30% | Accurate answers about AI, validation, feasibility, SDG 9 and limitations |

### Proposal-selection rubric in the guidebook

The guidebook lists a different rubric for proposal selection: problem identification 15%, solution innovation 25%, AI utilization 25%, implementation feasibility 20%, and SDG contribution 15%. Do not present this as the final-round scoring breakdown. Use the event-day rubric for the final deck unless organizers replace it.

## Suggested deck crosswalk

This crosswalk makes required material visible while keeping the talk within ten minutes. Merge or split slides as needed; content coverage matters more than this sample slide count.

1. **Cover:** title, team members and university.
2. **Problem:** internship-motivated reporting handoff and a simple manual before-flow.
3. **Solution:** product concept and unified, traceable KPI view.
4. **Design and workflow:** upload, mapping review, validation, confirmation and dashboard.
5. **AI:** schema interpretation and feedback-linked drafting, with deterministic and AI responsibilities labeled.
6. **Prototype evidence:** synthetic demo counts and a provenance example; label all synthetic material.
7. **Feasibility and safeguards:** spreadsheet workflow, analyst confirmation, required data, current limits and validation still needed.
8. **SDG 9:** primary connection, impact pathway and indicator boundary.
9. **Conclusion:** what works now and the next test.

This is a content map, not a mandated slide count. Rehearse transitions and prepare for the ten-minute Q&A separately.

## Source notes

- `Documents/WhatsApp Image 2026-10-28 at 19.49.23.jpeg`: final submission deadline, presentation date and section list.
- `Documents/WhatsApp Image 2026-10-28 at 19.50.32.jpeg`: final-round 20/50/30 rubric.
- `Documents/GUIDEBOOK ITASE 7.0.pdf`: competition rules, AI requirements, presentation duration and proposal-selection rubric.
- `Documents/OMNIkpi.pdf`: submitted proposal context and original plan. Proposed capabilities are not automatically current features; compare against [current system](CURRENT_SYSTEM.md).

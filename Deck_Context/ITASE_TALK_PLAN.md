# ITASE 7.0: requirements and ten-minute talk plan

## Final-round requirements from the event-day briefing

The event-day briefing images in `Documents/` list submission in PDF or PPTX format by 6 November 2026 at 23:59 WIB. The online presentation is on 7 November 2026, with ten minutes to present and ten minutes for Q&A.

The required deck sections are: cover (title, member names and university), problem identification, solution concept and innovation, use of AI, design and system workflow, implementation feasibility, SDG contribution, and conclusion.

The final-round rubric is **PPT completeness 20%, presentation 50%, and Q&A 30%**. This is the rubric to optimize the final deck for. The detailed coverage checklist is in [ITASE deck requirements](ITASE_DECK_REQUIREMENTS.md).

## Additional requirements recorded in the local guidebook

The local copy of `Documents/GUIDEBOOK ITASE 7.0.pdf` says:

- The final is online, with ten minutes for the presentation and ten minutes for Q&A.
- Finalists submit a PowerPoint or PDF before the deadline set by the committee.
- The guidebook's proposal-selection rubric is problem identification 15%, solution innovation 25%, AI utilization 25%, implementation feasibility 20%, and SDG contribution 15%. This is a different stage from final judging; do not confuse the two rubrics.
- Teams should use an available AI technology rather than train a model from scratch, and explain its mechanism, selection and role.
- The solution must clearly connect to one of SDG 3, SDG 8 or SDG 9.

The local guidebook lists the final on 7 November 2026. The event-day briefing supplies the deck deadline of 6 November 2026 at 23:59 WIB. Confirm dates against the latest organizer message before relying on them.

## Suggested ten-minute narrative

Use a small number of slides with one point each. The durations below total ten minutes and leave room for a short live walkthrough.

| Time | Slide job | Evidence or visual |
|---|---|---|
| 0:00-0:40 | Introduce the reporting handoff and the analyst's problem | One clear sentence from the internship context; identify it as the team's motivating experience |
| 0:40-1:50 | Show why scattered division files create a real workflow burden | A simple before diagram: several files -> analyst's manual workbook -> stakeholder view. Do not invent hours or error rates |
| 1:50-2:40 | State the product and its distinct idea | “Reviewed divisional KPI submissions become one traceable performance view.” Explain the role of AI in interpreting report structure |
| 2:40-4:00 | Walk through intake and human review | Live or recorded upload, proposed mapping, correction/validation and confirmation |
| 4:00-5:15 | Show consolidation and provenance | Seven synthetic division files, 90 KPIs, 180 readings; point to unit, filename and source row |
| 5:15-6:40 | Explain AI accurately | Schema suggestions and feedback-grounded draft. Contrast with deterministic validation, thresholds and statistics |
| 6:40-7:35 | Show the shortfall investigation path | Choose an off-target reading, show attached division feedback, then show attributed draft or no-evidence state |
| 7:35-8:35 | Make feasibility and safeguards credible | Existing Excel/CSV workflow, analyst confirmation, isolated prototype, required data and limits |
| 8:35-9:20 | Connect to SDG 9 | Explain the indirect infrastructure-resilience pathway. Distinguish the product from official SDG indicators; see [SDG 9 position](SDG_9_POSITION.md) |
| 9:20-10:00 | Close with the measured next validation step | Compare manual and assisted consolidation on matched, approved reports; state that this remains to be measured |

Adjust slide count and timing to the presenter's delivery. A live demo should have a prepared fallback because network or AI-provider access may vary.

## Demo run-of-show

1. Open the landing page and choose Try demo.
2. Show the consolidated view and identify its synthetic-data badge.
3. Filter by division or inspect the submission ledger to show that the view preserves unit ownership.
4. Open a reading and point out the source file and source row.
5. Select a reading with feedback and request an RCA draft. Call it division-reported evidence, not a verified cause.
6. If time permits, show a no-feedback reading returning insufficient evidence.
7. Optional, if the AI slide needs proof: open `/evaluation`, state the synthetic five-layout result, then upload one demo workbook with the AI checkbox on and read the trace (mode, model, columns, samples, latency). Say out loud whether it says live or recorded.
8. Close on the analyst's role: confirm mappings and review the draft.

Do not upload the reconstructed inputs on top of the one-click demo's already seeded database. Use a clean workspace if demonstrating the seven-file import from scratch.

## Message to carry through the deck

The main innovation is the workflow: divisional KPI submissions become a shared, reviewable dataset that preserves provenance. AI reduces the manual interpretation burden at report intake and helps draft explanations from feedback already tied to a reading. The presentation should show this exact boundary.

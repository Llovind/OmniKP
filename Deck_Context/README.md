# omniKPI deck context

These notes are the working memory for preparing the omniKPI competition deck. They summarize the product and demo as they exist in this repository, plus the ITASE 7.0 final requirements recorded in the local guidebook.

## Read in this order

1. [Product brief](PRODUCT_BRIEF.md): the user, reporting problem, product promise and AI contribution.
2. [Current system](CURRENT_SYSTEM.md): implemented workflow, architecture, demo facts and limits.
3. [ITASE deck requirements](ITASE_DECK_REQUIREMENTS.md): required sections, final rubric and checklist.
4. [SDG 9 position](SDG_9_POSITION.md): the defensible connection to infrastructure and connectivity.
5. [ITASE and talk plan](ITASE_TALK_PLAN.md): requirements and a ten-minute presentation spine.
6. [Claims and Q&A](CLAIMS_AND_QA.md): safe wording, evidence and likely judge questions.

## Source-of-truth order

- Current code and current demo fixtures establish what the prototype does.
- `README.md`, `backend/evidence/division-demo/README.md` and `frontend/public/demo/divisions/VALIDATE.md` explain the workflow and validation pack.
- `Documents/GUIDEBOOK ITASE 7.0.pdf` establishes the competition rules available in this repository.
- The two `WhatsApp Image 2026-10-28 ...` files in `Documents/` record event-day deck requirements and the final-round rubric. Use them subject to any newer organizer notice.
- `Documents/OMNIkpi.pdf` is the submitted proposal. It records the original proposal, not necessarily the implementation as it stands now.
- `Documents/Kick Off Automation Hackathon 2026.pdf` belongs to the separate UiPath-Indosat automation competition. Keep its requirements out of the ITASE deck unless the user asks for a combined presentation.
- `.MD_Context/` contains earlier project memory. Some files describe a prior incident-log concept and should not override the current product behavior.

The guidebook is a local copy and event instructions can change. Recheck the organizer's latest notice before submitting or presenting.

## One-sentence product description

omniKPI helps a telco performance analyst turn separate divisional KPI spreadsheets into a reviewed, source-traceable shared dataset, then organize target checks and division feedback around those readings.

## Presentation discipline

Tell the story through the real reporting handoff: division files arrive separately, analysts reconcile their meaning and ownership, and stakeholders need one comparable view. Demonstrate the implemented flow. Label all fixture data as synthetic and distinguish working code from planned deployment. Do not imply the prototype has been validated on live operator data.

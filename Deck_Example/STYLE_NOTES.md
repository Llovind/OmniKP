# Deck_Example: reference analysis

This note records the visual and storytelling patterns observed in the three PDFs in this folder. It is a reference for future omniKPI competition and project decks, not a request to reproduce any one deck.

## Shared visual language

- Blue is the recurring identity color. The examples use cobalt or royal blue for headings and emphasis, navy for strong contrast, and white or pale blue for most content backgrounds.
- Large, bold sans-serif headings establish hierarchy. Several slides use a short vertical blue rule beside the title.
- The deck's current section is visible through a chapter strip, progress bar, or top navigation. Page numbers and small brand marks repeat on content slides.
- Text is organized with diagrams, comparisons, metrics, tables, screenshots and roadmap stages. The visual form changes with the content, even when the brand system remains consistent.
- Covers are more expressive than content slides. They use a hero image, product context, logos and team attribution, while most later pages favor a bright, structured reading surface.

## What each file contributes

### `1792983308568.pdf` - Baiess: Platform Continuous Financial Intelligence

This 18-page deck opens with a photographic collage and a strong centered product title, then shifts to a white slide canvas with a persistent section navigation bar. Its argument starts with an everyday business owner and fragmented transaction data, then moves through the problem, validation, competitive position, implementation, finance and conclusion. It uses large figures, infographic cards, comparison matrices, roadmap stages, product mockups and a QR code. The last pages provide sources and a thank-you close.

Useful cues: a human opening, section orientation, varied evidence formats, named product screens and an explicit end. Some pages are crowded; preserve the variety, but simplify the density for a ten-minute talk.

### `Salinan dari CASE 2 · MONETIZING THE CONNECTED HOME —ZTE × ITB INNOVATION COMPETITION (2).pdf` - Creator Turbo Agent

This 29-page deck opens with a light-blue product cover, team and partner attribution. It tells a specific live-commerce lag story through a seller persona and three failure moments before showing the solution. Blue title text with a vertical accent rule, dark navy bands and a four-part footer navigation create a consistent system. The main section uses an evidence progression: problem, workflow, architecture, test metrics, commercial model, feasibility, impact and conclusion. It labels assumptions and puts detailed system design, benchmark tables and sensitivity work in an appendix.

Useful cues: explain the problem through a user journey, show the system's decisions and boundaries, separate measured prototype output from projected value, and reserve technical detail for backup slides. The branded ZTE imagery and exact visual assets belong to that deck; do not reuse them.

### `Salinan dari White and Blue Modern Startup Pitch Deck Presentation.pdf` - Afferent

This 31-page PDF appears to combine multiple versions of an Afferent presentation: a short English set at the beginning, a longer Indonesian version later, followed by appendix and roadmap pages. It uses a white canvas, blue condensed-style headings, a small top-right brand mark, short blue title rules, navy section navigation and occasional pale-blue or navy containers. It is especially explicit about what the prototype does and does not claim. Later pages show current measures, data-protection boundaries and open questions for a pilot.

Useful cues: put limitations and “what works today” on slides, treat security and human control as design details, and show a roadmap as a set of gates or questions. The PDF has blank pages and overlapping versions, so its full page order is not a single clean narrative to imitate.

## Storytelling patterns

1. Begin with a concrete person or operational situation, not a broad technology claim.
2. State the friction in a conclusion-style headline, then support it with a small number of sourced facts or observations.
3. Show how the proposed system changes a real workflow. Use a diagram or product screen instead of a paragraph describing every step.
4. Pair product claims with proof: a prototype screen, a labeled measurement, a comparison, or an explicit test plan.
5. Separate present capability from projected business value and future work.
6. Finish with a compact conclusion, then keep source lists and detailed technical evidence available in backup slides.

## What to adapt for omniKPI

- Keep the blue/navy and white visual language, but follow omniKPI's existing logo and brand colors.
- Open with the analyst combining separate division reports. Keep it grounded in the user's internship account, and do not present it as an official company endorsement.
- Show one traceable divisional report flowing into a shared KPI view. Demonstrate the actual upload, mapping review, confirmation and provenance path.
- Make synthetic data visible as a label. Do not style synthetic readings as customer evidence or company outcomes.
- Favor a few strong diagrams and screens over a dashboard-shaped grid of cards.
- Include the AI boundary, the human review step, current limitations and an honest validation plan. Do not add unimplemented features to match the original proposal.
- For ITASE, follow the event-day content list and final-round scoring in `Deck_Context/ITASE_DECK_REQUIREMENTS.md`; the example decks do not override the competition brief.

## Skill entry point

The reusable project skill is at `.agents/skills/omnikpi-deck-style/SKILL.md`. Root `AGENTS.md` routes future presentation work to it.

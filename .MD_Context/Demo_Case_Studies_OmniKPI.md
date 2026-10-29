# GOLDEN FLOW — TELCO FIBER CUT

## Scenario

District Bandung Timur experiences a backbone fiber cut on the
Cicaheum–Ujungberung segment during third-party excavation. Twelve BTS sites
fail over to a redundant path supporting 60% of normal traffic.

The seed injects these readings on 2026-08-25:

| KPI | Actual |
|---|---|
| Network Availability | 96.2% |
| BTS Accessibility Rate | 82.0% |
| Call Drop Rate | 2.8% |
| Data Throughput | 312 Mbps |
| Bandwidth Utilization | 89.5% |

Three synthetic logs describe the fiber cut and failover on 2026-08-20, and an
unrelated scheduled maintenance entry on 2026-08-19. The retrieval window includes
these dates; the demo does not establish that the incident remained unresolved
through 2026-08-25. This timing is a limitation of the current seed.

## Presentation sequence

1. Show the district KPI matrix and identify service degradation.
2. Open Network Availability and its historical trend.
3. Trigger RCA; explain direct KPI links, text matching and contextual evidence.
4. Show the fiber-cut hypothesis and engineer-reviewed repair recommendations.
5. Explain provider fallback, heuristic confidence and evidence limitations.

Exact Z-scores come from the generated baseline rather than hand-written examples.
On the current deterministic seed, Network Availability has Z = -32.8543.
The fifteen KPIs across three districts produce 45 latest-date cells, including
eight RED cells: five injected incident nodes and three additional deviations.
Retrieval coverage is not evidence that every deviation shares the fiber-cut cause.

All numbers and events are synthetic. Do not claim measured reductions in downtime,
verified causal diagnosis or production deployment from this demonstration.

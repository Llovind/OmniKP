# KPI FRAMEWORK — OMNIKPI TELCO

OmniKPI groups its fifteen telecommunications KPIs into four operational categories.
These categories organize the demo; formal standard compliance is not asserted.

| Category | Metrics |
|---|---|
| Availability | Network Availability, BTS Accessibility Rate, Core Network Uptime |
| Performance | Data Throughput, Bandwidth Utilization, Handover Success Rate, Network Congestion Rate |
| Quality | Packet Loss Rate, Call Drop Rate, Latency (RTT), Jitter |
| Reliability | MTTR, MTTD, Service Restoration Time, Fiber Restoration Time |

`dim_kpi` stores name, category (`kpi_archetype`), domain 1, formula description,
unit, target, higher_is_better and source_standard. Review individual formula and
source labels before presenting them as formal definitions.

Examples: Network Availability = uptime / total period × 100; Packet Loss Rate =
lost packets / packets sent × 100; MTTR = downtime / incident count. Target values
in the demo are synthetic assumptions rather than universal operator SLAs.

The matrix reflects statistical deviation from a baseline. SLA attainment and
statistical normality are different: a normal reading can miss its target and an
improved reading can be statistically anomalous. The current color rule uses |Z|
without directionality. Explain this limitation when discussing prioritization.

The hierarchy is Nasional → Regional Jawa Barat → Witel → District. Only leaf
district readings populate the heatmap. Parent aggregation is future work.

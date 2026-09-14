# Trinetra — Cost-Benefit Analysis (indicative)

## Assumptions
- Existing ~80,000 cameras and their NVR/VMS remain in place (no camera replacement).
- INR figures are planning-grade estimates (±30%), commercial procurement would refine them.

## Pilot (50 cameras)

| Item | Estimate |
|---|---|
| Gateway compute (2× mini-PC) | ₹1.5 L |
| Central server (16 GB VM or 1U) | ₹2.5 L |
| Integration, survey, training (team effort) | ₹2–4 L |
| **Pilot total (CAPEX)** | **₹6–9 L** |

OPEX: near-zero incremental (existing police WAN + data-centre rack space).

## Statewide (80,000 cameras)

| Item | Estimate |
|---|---|
| 3,200 gateway pods (₹60k CPU / ₹1.2L GPU mix, incl. install) | ₹28–38 Cr |
| Central DC: 24 app nodes + DB tier + 20 GPU nodes + networking | ₹22–30 Cr |
| Control-plane services (records/notifier/janitor/streamer) | ₹1–2 Cr (shares app tier; streamer runs on-site) |
| Storage 250 TB tiered + DR site | ₹10–15 Cr |
| Site surveys, cabling-to-gateway, project management (33 districts) | ₹25–35 Cr |
| **Total CAPEX (5-year horizon)** | **₹95–140 Cr** |
| Annual OPEX (power, links, maintenance, staff) | ₹18–25 Cr/yr |

**Avoided cost of the naive alternative:** centralizing raw streams from 80k cameras would need ~320 Gbps of dedicated WAN plus ~86 PB/yr — order ₹400 Cr+ in network and storage alone, before any AI. Trinetra's federated plane runs on the existing WAN at 1–2 Gbps.

## Benefits

1. **Recovered stolen vehicles:** ANPR hits on stolen/blacklisted plates at junction cameras convert to interception. Even a 5% improvement in recovery rate on Gujarat's ~40k annual vehicle-theft FIRs is a citizen-visible outcome.
2. **Force multiplication:** one control room cannot watch 80,000 feeds; automated matching + alerts turns the estate into an active sensor grid. Effective monitoring capacity per operator rises ~100×.
3. **Investigation hours:** plate/camera/time search that takes minutes instead of days of CCTV footage review across vendors — the searchable event log with CSV export is the audit-ready artefact for courts.
4. **Zero vendor lock-in:** new cameras of any brand onboard through the registry in minutes; incumbent VMS stays functional during and after rollout (no downtime migration risk).
5. **Interoperability dividend:** the normalized event schema becomes reusable by future state systems (traffic management, disaster response, CCTNS integration).

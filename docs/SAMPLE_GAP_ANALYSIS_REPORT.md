# Trinetra — Sample Gap-Analysis Report (Model 1)

*Generated from the pilot registry dataset (53 cameras: 50 government + 3 community across 5 zones, 26 departments). This is the Model-1 "sample gap-analysis report" deliverable, also available live at `GET /api/v1/gap-analysis/report` and downloadable as CSV at `/api/v1/gap-analysis/report/download`.*

**Generated:** 2026-09-01 (pilot dataset) · **Planning targets:** min 6 online cameras/zone, min 60% online ratio, min 0.30 km² coverage footprint, ageing ≥ 5 years, critical ≥ 7 years.

## 1. Summary

| Metric | Value |
|---|---|
| Zones assessed | 5 |
| Zones with coverage gaps | **2** |
| Ageing cameras (5y+) | 32 |
| Critical cameras (7y+) | **20** |
| End-of-life firmware (v2.x) | **17** |
| Cameras needing maintenance | **14** |

## 2. Coverage by zone

| Zone | Cameras | Online | Degraded | Offline | In repair | Coverage km² | Online ratio | Gap |
|---|---|---|---|---|---|---|---|---|
| Zone-1 Ahmedabad West | 13 | 12 | 2 | 1 | 1 | 0.40 | 92% | ok |
| Zone-2 Ahmedabad Central | 13 | 12 | 0 | 1 | 1 | 0.41 | 92% | ok |
| Zone-3 SG Highway | 14 | 14 | 1 | 0 | 1 | 0.48 | 100% | ok |
| Zone-4 Gandhinagar Highway | 6 | 5 | 0 | 1 | 0 | 0.23 | 83% | **GAP** |
| Zone-5 Gandhinagar | 7 | 7 | 1 | 0 | 0 | 0.26 | 100% | **GAP** |

## 3. Ageing infrastructure

| Age bucket | Count |
|---|---|
| Under 2 years | 6 |
| 2–5 years | 12 |
| 5–7 years (ageing) | 12 |
| **Over 7 years (critical)** | **20** |

End-of-life firmware (v2.x): **17** cameras · Cameras needing maintenance: **14**

## 4. Recommendations

1. **Deploy additional cameras in 2 under-covered zones:** Zone-4 Gandhinagar Highway (5 online, 0.23 km² coverage) and Zone-5 Gandhinagar (0.26 km² coverage below the 0.30 km² target).
2. **Plan replacement of 20 cameras** older than 7 years (end-of-life hardware, higher failure risk).
3. **Upgrade firmware on 17 cameras** running end-of-life v2.x firmware (security and interoperability risk; GB/T 28181 readiness requires current firmware).
4. **Schedule maintenance for 14 cameras** in degraded health or currently under repair.

## 5. Methodology

- **Coverage footprint** is the sum of circular coverage areas (π × radius²) per camera, by zone. In production this is computed precisely with PostGIS `ST_Buffer`/`ST_Union` over camera coverage polygons and zone boundaries to identify true uncovered polygons, not just aggregate density.
- **Ageing** uses the camera's `install_date`; **end-of-life firmware** flags `v2.x` builds.
- **Gap flag** triggers when a zone is below any planning target (online count, online ratio, or coverage footprint).
- All thresholds are configurable; the report is regenerated on demand from the live registry.

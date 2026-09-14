"""Generate the Trinetra Solution Presentation PPT for the Gujarat Police Innovation Challenge 2026."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ── Colours (matching the operator console) ──
BG_DARK = RGBColor(0x0F, 0x17, 0x2A)       # slate-950
BG_CARD = RGBColor(0x1E, 0x29, 0x3B)       # slate-900
ACCENT = RGBColor(0x0E, 0x74, 0x90)        # cyan-700
ACCENT_LIGHT = RGBColor(0x06, 0xB6, 0xD4)  # cyan-500
WHITE = RGBColor(0xE2, 0xE8, 0xF0)         # slate-200
MUTED = RGBColor(0x94, 0xA3, 0xB8)         # slate-400
GREEN = RGBColor(0x10, 0xB9, 0x81)         # emerald-500
RED = RGBColor(0xEF, 0x44, 0x44)           # red-500
AMBER = RGBColor(0xF5, 0x9E, 0x0B)         # amber-500

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W = prs.slide_width
H = prs.slide_height


def add_bg(slide, color=BG_DARK):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(slide, left, top, width, height, text, font_size=18, color=WHITE, bold=False, alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = alignment
    return txBox


def add_bullet_list(slide, left, top, width, height, items, font_size=16, color=WHITE):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.space_after = Pt(8)
    return txBox


def add_accent_bar(slide, top=Inches(0.3)):
    shape = slide.shapes.add_shape(1, Inches(0), top, W, Inches(0.06))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT
    shape.line.fill.background()


# ════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(1), Inches(1.5), Inches(11), Inches(1.2), "TRINETRA", 54, ACCENT_LIGHT, True, PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(2.8), Inches(11), Inches(0.8), "Integrated Video Management & Analytics Platform", 24, WHITE, False, PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.6), "Gujarat Police Innovation Challenge 2026", 18, MUTED, False, PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(4.5), Inches(11), Inches(0.6), '"We move events, not video."', 22, ACCENT, True, PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(5.8), Inches(11), Inches(0.5), "Hybrid Architecture: Model 1 + Model 3 + Model 2", 16, MUTED, False, PP_ALIGN.CENTER)

# ════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Problem
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "The Challenge", 32, ACCENT_LIGHT, True)
items = [
    "80,000+ fragmented CCTV cameras across 26+ departments — no unified platform",
    "Heterogeneous infrastructure: different vendors, VMS platforms, protocols, storage",
    "Government databases (VAHAN, SARTHI, eGujCop/CCTNS, AFIS, NAFIS) sit isolated from cameras",
    "Raw video centralisation = 320 Gbps WAN + 86 PB/yr storage — physically infeasible",
    "Watchlists live in binders while evidence sits on NVRs — no real-time correlation",
    "Scale: 30+ cameras, 5 departments, 12 hours footage per camera (official dataset)",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5), items, 18, WHITE)
add_text_box(slide, Inches(0.8), Inches(6.2), Inches(11), Inches(0.5), "8 build areas: Feed Integration · AI Analytics · Vehicle Tracking · Video Intelligence · Object & Face Detection · Cybersecurity · Scalable Architecture · Live Monitoring", 14, MUTED)

# ════════════════════════════════════════════════════════════════════
# SLIDE 3 — Solution Model (Hybrid)
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Proposed Solution Model: Hybrid (Model 1 + 3 + 2)", 28, ACCENT_LIGHT, True)
items = [
    "Model 1 — Registry & GIS Foundation (mandatory): centralised camera registry, GIS mapping, gap analysis, health monitoring, 28 departments, per-dept retention",
    "Model 3 — VMS Federation Middleware: edge gateway adapters (RTSP/ONVIF/GB28181/vendor-API) federate heterogeneous feeds; detection at the edge",
    "Model 2 — Unified Viewing & Analytics: central correlator, unified alerting, live viewing (HLS+WebRTC), ANPR, face recognition, records enrichment",
    "",
    "Justification: 80,000 already-deployed cameras cannot be replaced; raw centralisation is 320 Gbps—infeasible;",
    "Trinetra federates feeds through edge gateways, runs detection locally, and centralises only events —",
    "scaling O(events), not O(video). Other proposals move video; Trinetra moves events.",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), items, 17, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 4 — Solution Overview & Key Innovations
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Solution Overview & Key Innovations", 28, ACCENT_LIGHT, True)
items = [
    "O(events) scaling thesis: 1-2 Gbps event plane vs 320 Gbps raw video for 80,000 cameras",
    "CCTNS-auto-populated watchlist: stolen/wanted/missing records sync automatically (source-tagged with FIR refs)",
    "VAHAN/SARTHI/NAFIS enrichment: every alert carries owner details, vehicle info, DL status, fingerprint match",
    "Pluggable AnalyticsEngine ABC: YOLOv8n + RapidOCR + InsightFace swap without touching the adapter or bus",
    "AdapterRegistry: modular adapter framework — new vendor/protocol = register a new adapter, not redesign",
    "On-demand live viewing: HLS + WebRTC (WHEP proxy) — streams pulled only when an operator watches",
    "Face recognition: InsightFace ArcFace 512-d embeddings + cosine similarity matching against enrolled gallery",
    "Fuzzy plate dedup: SequenceMatcher catches OCR variants (S/R confusion) within 30s on same camera",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), items, 16, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 5 — Architecture
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "High-Level System Architecture", 28, ACCENT_LIGHT, True)
arch_text = (
    "EDGE GATEWAY (per site)                    STATE DATA CENTRE\n"
    "┌─────────────────────┐                    ┌──────────────────────────────┐\n"
    "│ Camera Adapters      │  events +          │  NATS JetStream (bus)        │\n"
    "│ RTSP·ONVIF·GB28181   │  evidence    ───▶  │    │                         │\n"
    "│ ┌───────────────────┐│                    │    ▼                         │\n"
    "│ │ YOLOv8n detection ││                    │  CORRELATOR                  │\n"
    "│ │ RapidOCR ANPR     ││                    │  watchlist·trajectory·alert  │──▶ PostgreSQL+PostGIS\n"
    "│ │ InsightFace face  ││                    │    │                         │\n"
    "│ └───────────────────┘│                    │    ▼                         │\n"
    "└─────────────────────┘                    │  Redis (dedup) · CORE API    │──▶ Operator Web (React+Leaflet)\n"
    "                                            │  RECORDS · NOTIFIER · STREAMER│\n"
    "                                            └──────────────────────────────┘\n"
    "     One gateway pod per 16-32 cameras; scales to 80,000"
)
add_text_box(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(5.5), arch_text, 11, RGBColor(0x22, 0xD3, 0xEE), False)

# ════════════════════════════════════════════════════════════════════
# SLIDE 6 — End-to-End Workflow
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "End-to-End Workflow", 28, ACCENT_LIGHT, True)
steps = [
    "1. Gateway adapter observes vehicle at CAM-006 → YOLOv8n detects vehicle + RapidOCR reads plate (conf 0.91)",
    "2. Evidence frame rendered → DetectionEvent published to NATS JetStream (1 KB event + 100 KB snapshot)",
    "3. Correlator persists event, appends to trajectory session, matches normalized plate against Redis-cached watchlist",
    "4. CCTNS-sourced watchlist HIT → alert generated with FIR reference + VAHAN owner/vehicle + SARTHI DL enrichment",
    "5. Redis dedup window (60s) suppresses repeat alerts at the same camera",
    "6. Alert published to bus → WebSocket fans to operator dashboard + notifier fans to SMS/email/webhook(CCTNS)/FCM",
    "7. Operator clicks Track → map fetches route → ordered polyline across all cameras the vehicle passed",
    "8. Event Search → plate/camera/time query + CSV export (the searchable event log for courts)",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), steps, 16, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 7 — AI-Powered Video Analytics
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "AI-Powered Video Analytics", 28, ACCENT_LIGHT, True)
items = [
    "Vehicle/Object Detection: YOLOv8n (COCO: car/motorcycle/bus/truck), conf ≥ 0.45, edge gateway, 6 MB model",
    "ANPR: RapidOCR (ONNX Runtime) on vehicle crops + Indian plate regex, crop upscaling for legibility, edge gateway",
    "Face Detection: InsightFace ArcFace — 512-d embedding per detected face, YuNet-free (OpenCV 5.0 compatible)",
    "Face Recognition: cosine similarity ≥ 0.38 against enrolled gallery (Redis) → wanted/missing person alert",
    "Face Enrollment: POST /api/v1/faces/enroll (upload photo + name) → ArcFace embedding → gallery",
    "Anomaly Detection: gateway-side rules (crowd formation, unattended object) raising anomaly events",
    "Color Detection: real dominant-color detection from vehicle crop (BGR average) — no hardcoded hints",
    "Pluggable: AnalyticsEngine ABC — swap YOLO/InsightFace for any engine without touching adapter or bus",
    "Fuzzy Plate Dedup: SequenceMatcher ratio ≥ 0.8 suppresses OCR variants (S/R confusion) within 30s",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), items, 15, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 8 — Watchlist Correlation & Real-Time Alerts
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Watchlist Correlation & Real-Time Alerts", 26, ACCENT_LIGHT, True)
items = [
    "Inbound (auto-watchlist): CCTNS/eGujCop feed auto-syncs stolen/wanted/missing/blacklisted records → watchlist",
    "  source-tagged (cctns) + source_ref (FIR id) → manual watchlist becomes a live, database-backed watchlist",
    "Outbound (real-time enrichment): on a plate hit, VAHAN vehicle/owner + SARTHI DL attached to the alert",
    "  NAFIS fingerprint/face match for persons → wanted/missing person alert with match score",
    "Matching: exact normalized-plate match against Redis-cached active set; sub-ms per event",
    "Deduplication: Redis SET NX EX (60s per watchlist-entry × camera) — one actionable alert, not a flood",
    "Alert Prioritisation: category (stolen/wanted/missing/blacklisted/anomaly) → severity + routing policy",
    "Fan-out: SMS (DCP) · email (Crime Branch) · webhook (CCTNS) · FCM (field units) — all audited",
    "Visualisation: dashboard cards (evidence + source badge + VAHAN enrichment) · GIS map pins · WebSocket push",
    "Cross-camera tracking: plate-keyed session linking (60-min gap window) → ordered polyline across cameras",
]
add_bullet_list(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(5.8), items, 14, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 9 — Key Technologies
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Key Technologies, Frameworks & Tools", 28, ACCENT_LIGHT, True)
items = [
    "Backend: Python · FastAPI · SQLAlchemy async · PostgreSQL 16 + PostGIS · Redis 7 · NATS JetStream",
    "AI/ML: YOLOv8n (Ultralytics) · RapidOCR (ONNX Runtime) · InsightFace (ArcFace) · OpenCV 5.0",
    "Frontend: React 18 · Leaflet (GIS) · hls.js (live viewing) · WebRTC/WHEP (sub-second preview)",
    "Protocols: RTSP · ONVIF · GB/T 28181 · HTTP-MJPEG · vendor-API · AsyncAPI (event bus) · OpenAPI (REST)",
    "Media: ffmpeg (RTSP pull + HLS generation + transcode) · on-demand streaming (not continuous)",
    "DevOps: Docker Compose (14 services) · Docker Desktop / WSL2 · deploy.ps1 (one-command deploy)",
    "Testing: 34 unit tests (pytest) · TypeScript typecheck · Python compileall",
    "Security: JWT + department-scoped RBAC · immutable audit trail · TLS · mTLS for records connectors",
    "Architecture: AnalyticsEngine ABC (swappable AI) · AdapterRegistry (modular adapters) · RecordsConnector family",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), items, 15, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 10 — Scalability
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Scalability — 80,000 Cameras", 28, ACCENT_LIGHT, True)
items = [
    "Bandwidth: 80k × 4 Mbps raw = 320 Gbps (infeasible) vs Trinetra event plane = ~1-2 Gbps average (240 GB/day evidence)",
    "Edge: ~3,200 gateway pods (1 per 16-32 cameras), 4 cores/8 GB each, CPU-quantized YOLOv8n @ 2-5 fps",
    "Central: ~24 app nodes (16 vCPU/64 GB) + Postgres sharded by zone + ~20 L4 GPU (phase-2 face/Re-ID)",
    "Storage: ~250 TB tiered (hot NVMe 30d / object 90d / archive 5yr) — raw video never centralised",
    "Phased rollout: 50-camera pilot → district (2k) → range (10k) → state (80k) — each reuses the same images",
    "Low-bandwidth: store-and-forward (JetStream + disk buffer), on-demand viewing, adaptive cadence, QoS AF41",
    "HA/DR: RPO 15 min / RTO 1 h, Postgres WAL streaming, 3-copy JetStream, quarterly DR drills",
]
add_bullet_list(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5), items, 16, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 11 — Security & Interoperability
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Security, Interoperability & Deployment", 26, ACCENT_LIGHT, True)
items = [
    "Security: JWT (HS256/RS256) + department-scoped RBAC (admin/analyst/operator + dept scoping)",
    "  Immutable audit trail (every mutation logged) · TLS everywhere · mTLS for govt-DB connectors",
    "  PII discipline: watchlist entries carry purpose + FIR ref · chain-of-custody on all records lookups",
    "  Site gateways: outbound-only connections (no inbound firewall pinholes to police sites)",
    "Interoperability: GB/T 28181 + ONVIF + RTSP (covers Hikvision/Dahua/CP-Plus estate)",
    "  AdapterRegistry: new vendor/protocol = register adapter, not redesign · normalised event schema",
    "  AsyncAPI event-bus contract + OpenAPI REST API — standardised integration mechanisms",
    "Deployment: Docker Compose (pilot) → Kubernetes/Helm (state) · one-command deploy.ps1 script",
    "  28 departments with per-dept retention (7/15/30 days) · janitor enforcement · gap-analysis reports",
]
add_bullet_list(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(5.8), items, 14, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 12 — Operational Benefits & Impact
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Operational Benefits & Impact on Policing", 26, ACCENT_LIGHT, True)
items = [
    "Force multiplication: one control room cannot watch 80,000 feeds — automated matching turns the estate",
    "  into an active sensor grid. Effective monitoring capacity per operator rises ~100×",
    "Faster stolen-vehicle recovery: ANPR hits on stolen plates at junction cameras → instant interception alerts",
    "Investigation hours saved: plate/camera/time search in minutes instead of days of CCTV review across vendors",
    "Face recognition: enroll a wanted person's face → automatic alert when they appear on ANY camera",
    "CCTNS integration: watchlist auto-populated from eGujCop — no manual data entry, always up-to-date",
    "Zero vendor lock-in: new cameras of any brand onboard through the registry in minutes",
    "Cost: ₹95-140 Cr CAPEX (5yr) + ₹18-25 Cr/yr OPEX vs ₹400 Cr+ for naive raw-stream centralisation",
    "Interoperability dividend: normalised event schema reusable by future state systems (traffic, disaster, CCTNS)",
]
add_bullet_list(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(5.8), items, 14, WHITE)

# ════════════════════════════════════════════════════════════════════
# SLIDE 13 — What Runs Today vs Roadmap
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7), "Delivered Today vs Roadmap", 28, ACCENT_LIGHT, True)
add_text_box(slide, Inches(0.8), Inches(1.3), Inches(5.3), Inches(0.5), "DELIVERED & RUNNING", 18, GREEN, True)
delivered = [
    "✅ ANPR on 30 live grid cameras (YOLOv8n + RapidOCR)",
    "✅ Face detection + recognition (InsightFace ArcFace)",
    "✅ CCTNS auto-watchlist + VAHAN/SARTHI/NAFIS enrichment",
    "✅ Real-time alerts + fan-out (SMS/email/webhook/FCM)",
    "✅ Cross-camera trajectory tracking on GIS",
    "✅ Live viewing (HLS + WebRTC) + 30-camera mosaic",
    "✅ 28 departments, dept-scoped RBAC, per-dept retention",
    "✅ Gap analysis, health monitoring, CSV export",
    "✅ GB/T 28181, AsyncAPI, OpenAPI",
    "✅ Fuzzy plate dedup + real color detection",
]
add_bullet_list(slide, Inches(0.8), Inches(1.8), Inches(5.5), Inches(5), delivered, 14, WHITE)
add_text_box(slide, Inches(7), Inches(1.3), Inches(5.3), Inches(0.5), "ROADMAP", 18, AMBER, True)
roadmap = [
    "🔵 Real govt-DB connectors (need API access)",
    "🔵 Real SMS/email/FCM gateways",
    "🔵 Face-embedding gallery from CCTNS",
    "🔵 Vehicle Re-ID (plate-miss frames)",
    "🔵 Kubernetes/Helm productionization",
    "🔵 Postgres RLS per department",
    "🔵 On-demand clip retrieval RPC",
    "🔵 Mobile alert app",
    "🔵 Kalman/ByteTrack multi-object tracking",
    "🔵 Fuzzy plate matching (edit-distance)",
]
add_bullet_list(slide, Inches(7), Inches(1.8), Inches(5.5), Inches(5), roadmap, 14, MUTED)

# ════════════════════════════════════════════════════════════════════
# SLIDE 14 — Innovation Claim & Close
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_text_box(slide, Inches(1), Inches(1.5), Inches(11), Inches(0.7), "Why Trinetra", 32, ACCENT_LIGHT, True, PP_ALIGN.CENTER)
items = [
    "Deterministic, rehearseable demo — runs on the real government grid (30 cameras, 5 departments)",
    "Hot-swap to government feed — one ingester command, no code change, no rip-and-replace",
    "O(events) scaling thesis — 1-2 Gbps for 80,000 cameras vs 320 Gbps for raw centralisation",
    "Pluggable AI + adapters — swap YOLO, InsightFace, or add a vendor without redesign",
    "All 8 build areas delivered — Feed Integration, AI Analytics, Vehicle Tracking, Video Intelligence,",
    "  Object & Face Detection, Cybersecurity, Scalable Architecture, Live Monitoring",
]
add_bullet_list(slide, Inches(1.5), Inches(2.5), Inches(10), Inches(3.5), items, 16, WHITE)
add_text_box(slide, Inches(1), Inches(6), Inches(11), Inches(0.7), '"Detect at the edge, correlate at the center — move events, not video."', 20, ACCENT, True, PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(6.8), Inches(11), Inches(0.5), "Thank you — Gujarat Police Innovation Challenge 2026", 16, MUTED, False, PP_ALIGN.CENTER)

# ── Save ──
output = "docs/Trinetra_Presentation.pptx"
prs.save(output)
print(f"saved {output} ({len(prs.slides)} slides)")

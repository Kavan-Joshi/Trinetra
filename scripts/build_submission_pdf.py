"""Compile the Trinetra submission docs into a single styled HTML for PDF printing.

Usage:  python scripts/build_submission_pdf.py
Then print to PDF with Edge headless:
    msedge --headless --disable-gpu --print-to-pdf=docs/Trinetra_Submission.pdf docs/Trinetra_Submission.html
"""
import datetime as _dt
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# (file, title, section-number) in submission order
SECTIONS = [
    ("SUBMISSION.md", "Submission Package Guide", "1"),
    ("REQUIREMENTS_COVERAGE.md", "Requirements Coverage Matrix", "2"),
    ("PRESENTATION_OUTLINE.md", "Solution Presentation", "3"),
    ("HLD.md", "Technical Proposal — High-Level Design", "4"),
    ("ARCHITECTURE_PRINCIPLES.md", "Architecture Principles Compliance", "5"),
    ("DEPLOYMENT_AND_OPERATIONS.md", "Deployment & Operations", "6"),
    ("INTEGRATION.md", "Integration Architecture", "7"),
    ("SCALABILITY.md", "Scalability to 80,000 Cameras", "8"),
    ("SECURITY.md", "Cybersecurity Architecture", "9"),
    ("COST_BENEFIT.md", "Cost-Benefit Analysis", "10"),
    ("DEMO_OWN_FEED.md", "Demo 3 — Own Feed Runbook", "11"),
    ("DEMO_SCRIPT.md", "Demo 4 — Government Feed Runbook", "12"),
    ("OUTPUT_REPORT_GOV_FEED.md", "Output Report — Government Feed", "13"),
    ("SAMPLE_GAP_ANALYSIS_REPORT.md", "Sample Gap-Analysis Report", "14"),
    ("GRID_FEEDS.md", "External Live Camera Grid Integration", "15"),
    ("DEPLOYMENT_GUIDE.md", "Deployment Guide (New Machine)", "16"),
    ("asyncapi.yaml", "AsyncAPI — Event Bus Contract", "17"),
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #1a2230; line-height: 1.5; }
h1 { font-size: 20pt; color: #0e7490; border-bottom: 2px solid #0e7490; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 15pt; color: #0e7490; margin-top: 1.2em; }
h3 { font-size: 12.5pt; color: #155e75; }
h4 { font-size: 11.5pt; color: #334155; }
a { color: #0e7490; text-decoration: none; }
code { font-family: 'Consolas', monospace; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }
pre { background: #0f172a; color: #e2e8f0; padding: 10px 12px; border-radius: 6px; overflow-x: auto; font-size: 8.8pt; line-height: 1.35; page-break-inside: avoid; }
pre code { background: transparent; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9.8pt; }
th, td { border: 1px solid #cbd5e1; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #e0f2fe; color: #0c4a6e; }
tr:nth-child(even) td { background: #f8fafc; }
blockquote { border-left: 3px solid #94a3b8; margin: 0.6em 0; padding: 0.2em 0.9em; color: #475569; background: #f8fafc; }
hr { border: none; border-top: 1px solid #cbd5e1; margin: 1.4em 0; }
.section { page-break-before: always; }
.cover { page-break-after: always; text-align: center; padding-top: 30%; }
.cover h1 { font-size: 34pt; border: none; color: #0e7490; }
.cover .sub { font-size: 14pt; color: #475569; margin-top: 0.4em; }
.cover .meta { font-size: 11pt; color: #64748b; margin-top: 3em; }
.toc { page-break-after: always; }
.toc h1 { border: none; }
.toc ol { list-style: none; padding-left: 0; }
.toc li { padding: 3px 0; font-size: 11.5pt; }
.toc .n { display: inline-block; width: 2em; color: #0e7490; font-weight: 600; }
"""


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )


def build() -> str:
    today = _dt.date.today().isoformat()
    parts = [f"<!doctype html><html><head><meta charset='utf-8'><title>Trinetra — Submission</title>"
             f"<style>{CSS}</style></head><body>"]

    # cover
    parts.append(
        "<div class='cover'>"
        "<h1>TRINETRA</h1>"
        "<div class='sub'>Integrated Video Management &amp; Analytics Platform</div>"
        "<div class='sub'>Gujarat Police Innovation Challenge 2026 — Submission</div>"
        f"<div class='meta'>Compiled {today}<br>Federated CCTV integration · real-time ANPR · "
        "CCTNS/VAHAN/NAFIS correlation · GIS tracking · live viewing</div>"
        "</div>"
    )

    # table of contents
    toc = ["<div class='toc'><h1>Contents</h1><ol>"]
    for fname, title, num in SECTIONS:
        toc.append(f"<li><span class='n'>{num}.</span> {title}</li>")
    toc.append("</ol></div>")
    parts.append("".join(toc))

    # sections
    for fname, title, num in SECTIONS:
        p = DOCS / fname
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8")
        if fname.endswith(".yaml"):
            body = f"<pre><code>{__import__('html').escape(raw)}</code></pre>"
        else:
            body = md_to_html(raw)
        parts.append(f"<div class='section'><h1>{num}. {title}</h1>{body}</div>")

    parts.append("</body></html>")
    return "".join(parts)


if __name__ == "__main__":
    out = DOCS / "Trinetra_Submission.html"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size//1024} KB)")

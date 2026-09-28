# v1 — Six slide charts for the U.S. magnesium development case

Generated: 2026-09-27  
Git commit: `unknown` (workspace is not a Git repository)

## Configuration

| Setting | Value |
|---|---|
| Scope | Global primary concentration; U.S. primary output/consumption, import origins, end uses, secondary recovery; electricity sensitivity |
| Research cutoff | 2026-09-27, matching the report |
| Evidence | USGS MCS 2026, S01; full source record in `source-register.csv` |
| Source periods | 2025 estimates except primary-consumption trend 2023–2025 and import origins 2021–2024 |
| Global residual | 1,100,000 t rounded world estimate minus 950,000 t China = 150,000 t; not the sum of non-China country entries |
| Import headline | Israel 47% + Türkiye 31% = 78%; pure-metal category only |
| Recycling | Recovery form, new and old scrap together; not the distinct secondary end-use shares |
| Electricity assumptions | Plant consumption 10, 15, 20 kWh/kg accepted Mg; electricity US$20–100/MWh in US$10 increments |
| Cost calculation | Electricity cost (US$/kg) = kWh/kg × US$/MWh / 1,000; no other cost components |
| Layout | 960 × 540 pt, 16:9, white background; Helvetica; teal/orange/blue with gray context |
| PNG resolution | 3840 × 2160 px |
| Formats | PNG, SVG, combined six-page vector PDF, per-chart CSV |
| Renderer | ReportLab 4.4.9 chart/graphics objects; Poppler PNG rendering |
| Input / generator identity | SHA-256 digests recorded in `charts.json` |

## Produced by

Run from the workspace root:

```sh
FONTCONFIG_FILE=/tmp/mg-fonts.conf /Users/janlukacas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 make_figures.py --output-dir /tmp/mg-slide-charts-v1
```

Outputs were visually checked in staging, then moved together to `figures/v1/`. To reproduce elsewhere, use Python with ReportLab and `pdftoppm` on PATH; pass a fresh `--output-dir`. `FONTCONFIG_FILE` configures local rendering fonts and is optional on a normally configured system.

## Figures

Each stem has a `.png`, `.svg` and `.csv` file:

1. `01-global-concentration`
2. `02-us-production-gap`
3. `03-us-import-origins`
4. `04-us-end-uses`
5. `05-recycling-boundary`
6. `06-electricity-sensitivity`

`magnesium-slide-charts.pdf` contains all six as individual 16:9 pages. PDF source footers link directly to USGS. SVG files preserve vector geometry and text and include accessible descriptions.

## Data outputs

- Six CSVs use explicit units, periods and reporting bases; statistical CSVs include source IDs and URLs.
- `charts.json` contains captions, accessible descriptions, analysis flags and provenance digests.
- `source-register.csv` contains the full S01 record. Chart 6 is an analyst calculation, not an external observation.

## Note

First published version; supersedes nothing. These charts reuse the report's source-checked data and introduce no new market observations. Supply concentration is not a current company ranking; imports are not assumed to originate entirely in China; recycling is not equated to primary ingot. Energy inputs are illustrative assumptions, not producer performance or current electricity prices.

For a slideshow, insert a PNG as a full-width 16:9 image, or use SVG for scalable vector artwork. Keep the subtitle and source notes with the graph. The PDF can be presented directly. The chart-gallery captions provide concise speaker notes.

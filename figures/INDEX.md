# Magnesium Atlas figure versions

Each version keeps its chart images, underlying data and provenance together. Reports link to a specific version. Create a new version for changed inputs, assumptions, plotted quantities or layout; preserve prior versions.

| Version | Date | Scope | Evidence periods | Format | Figures | Status |
|---|---|---|---|---|---:|---|
| [v1](v1/MANIFEST.md) | 2026-09-27 | U.S. electrochemical development case | 2025 estimates; 2023–25 trend; 2021–24 import mix; illustrative energy scenarios | 16:9 PNG / SVG / PDF | 6 | Current |

## What changed between versions

- **v1:** First figure set. Five charts present reported or estimated statistics with their original boundaries. The sixth presents an explicitly assumed electricity-cost sensitivity.

## Reading a version

Each `MANIFEST.md` records the inputs, calculation boundaries, rendering configuration and reproduction command. Per-chart CSVs preserve the exact plotted values; `charts.json` records descriptions and provenance hashes.

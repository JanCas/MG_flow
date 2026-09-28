# Magnesium Atlas

Research report and static multipage website about global magnesium-metal producers. Research cutoff: **27 September 2026**.

Open [index.html](index.html) in a browser, or read [report.md](report.md). Downloadable tables and their definitions are in [data/](data/README.md).

The [production-process guide](processes.html) explains thermal extraction, chloride electrolysis, refining and recycling, with facility-specific examples and two downloadable process tables. General, laboratory and historical reference values are labeled separately.

The [magnesium hydroxide feedstock section](magnesium-hydroxide.html), researched **28 September 2026**, covers brine-derived and natural hydroxide, chloride and oxide conversion routes, commercial specifications, and calculated feed requirements. Two downloadable tables distinguish supplier assays from theoretical and assumed-recovery mass balances. The base producer review retains its 27 September cutoff.

The [purity and commodity-flow section](quality-trade.html) covers specifications, buyer qualification, material routes, regional trade and price benchmarks, with six downloadable reference tables.

The [U.S. electrochemical development case](us-development.html) brings together supply, domestic feedstocks, customer requirements and process choices. It includes revised 2025 / first-half 2026 trade data, four downloadable tables and an explicit distinction between evidence and development recommendations.

The [slide-chart gallery](charts.html) provides six widescreen charts as 3840 × 2160 PNGs, SVGs, a combined PDF and source-linked CSVs. Download the [chart pack](magnesium-slide-charts.zip). Each figure is paired with its data under [figures/v1](figures/v1/MANIFEST.md). The website build still uses only the standard library; regenerating images with `make_figures.py --output-dir <new-version-or-staging-folder>` also requires ReportLab and Poppler.

The [review log](review.md) records the independent readability and accuracy checks, newly located documents, corrections and remaining access limitations.

If using the supplied ZIP bundle, extract it before opening `index.html` or uploading its contents to GitHub Pages.

## GitHub Pages

Upload this directory to a GitHub repository. In **Settings → Pages**, choose **Deploy from a branch**, select the branch and **/(root)**. All pages use relative URLs and work under a repository subpath. `.nojekyll` is included. No server, database, package installation or build action is required to publish the checked-in HTML.

## Update and verify

`data/research.json` holds the research records. `build.py` holds the overview, methodology and compact table labels. Update the full and compact fields together. Sources include claim locators, access dates and limitations.

```sh
python3 build.py
python3 check.py
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/ for local preview. The builder uses only Python's standard library. The website works without JavaScript, external fonts or a network connection after download; external references require internet access.

## Evidence boundaries

The report distinguishes primary metal, internal chloride regeneration, recycled metal, alloy production, components, trading/shipments and proposed capacity. It does not present an unsupported current company ranking. Missing figures remain missing; older actuals and national estimates are explicitly labeled. Source documents are linked, not redistributed. See [methods.html](methods.html) for limitations.

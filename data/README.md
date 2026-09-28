# Data dictionary

Research cutoff: 2026-09-27. CSV encoding: UTF-8 with BOM. Delimiter: comma. Quoted cells may contain commas; use a CSV parser.

- `research.json`: canonical full research text, profiles, projects, national figures, numeric observations and source register. `[Snn]` tokens refer to source IDs.
- `producers.csv`: company/facility directory and classification; one row per profile, sometimes a consolidated group, never automatically additive.
- `feedstocks.csv`: raw inputs, origin/purchasing, preparation/route, grade basis, ratios and constraints.
- `output.csv`: human-readable comparison preserving quantities, periods and incompatible capacity bases. Numeric-looking text is intentionally qualified.
- `quantities.csv`: numeric observations only. `value_t` is metric tonnes, or the lower value of a reported range; `value_max_t` is its upper value. Empty upper bounds mean not a range. `period` is text because annual, half-year and unallocated two-year ranges coexist. `metric` and `note` must be used before comparing or aggregating. No all-producer total is valid.
- `countries.csv`: one USGS statistical series, converted from thousand metric tonnes to tonnes. 2025 values are estimates, not producer actuals. Capacity uses t/y and may include idle plants. World total is rounded; do not add it to country rows. Source dashes are coded 0 (zero in source), not missing company observations.
- `markets.csv`: buyer evidence with intermediate and final uses; future and historical relationships explicitly labeled.
- `projects.csv`: proposed/demonstration/stalled projects, excluded from current commercial primary supply.
- `sources.csv`: ID, title, publisher, publication/reporting date, URL, locator, supported claims, limitations and access date. An undated source remains undated.
- `purity-specifications.csv`: selected supplier/benchmark product specifications; composition in percent as published, not batch assays or a complete standard.
- `application-requirements.csv`: acceptance considerations by use; public evidence versus undisclosed buyer limits.
- `commodity-flows.csv`: qualitative material and commercial routes, with documented examples; no shipment tonnage assigned.
- `trade-context.csv`: regional shares with their original periods and product boundaries; not a common-year global flow balance.
- `price-benchmarks.csv`: grade, location, delivery, lot and currency/unit definitions; no current price observations.
- `trade-codes.csv`: six-digit HS category guide; national legal subdivisions require separate checking.
- `facility-processes.csv`: documented preparation, extraction and finishing at named facilities; evidence dates and limits remain explicit.
- `process-input-boundaries.csv`: historical reference inputs, prepared-charge recipe and chloride-stage recovery on incompatible bases; not current plant consumption estimates.
- `us-supply-case.csv`: U.S. supply indicators, periods and incompatible material boundaries; analysis alongside cited statistics.
- `us-trade.csv`: revised 2025 and first-half 2026 imports from USGS Q2 2026, preserving category-specific weight bases; not a primary-ingot market size.
- `us-route-options.csv`: chloride electrolysis, oxide electrolysis and an alternative thermal route; commercial precedents versus research/development.
- `us-development-criteria.csv`: proposed engineering evidence requirements, with units and supporting context; not observed performance or published pass/fail thresholds.

The six quality/trade exports use descriptive column headers, including units, plus source IDs and URLs. Their source text lives under `quality_trade` in `research.json`. Percentage limits, ranges and inequalities remain text to preserve their meaning. Empty or undisclosed limits are not zero.

The two process exports follow the same convention and live under `processes`. The historical DLR 2013 case is separate from current producer data. RIMA's recipe uses the explicit stage-i statement and flags the conflicting stage-iv wording.

The four U.S. development exports live under `us_development`. Recommendations are analyst synthesis, distinct from source observations. The illustrative electricity calculation uses assumed inputs, not a plant estimate or current tariff. The Big Blue project retains the company's undefined “tons/year” label; it is not converted into the metric numeric-observation table.

Unknown company annual quantities are omitted from `quantities.csv`, and explained in `output.csv`; absence does not mean zero. Values are not normalized to elemental magnesium unless the original source uses that basis. Grades retain Mg, MgO, MgCl2, alloy or product basis. No confidential number is inferred from plant capacity.

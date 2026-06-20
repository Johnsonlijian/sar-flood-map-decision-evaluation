# SAR Flood-Map Decision-Aware Evaluation

This repository is the public, rights-bounded reproducibility package for the manuscript:

**Aggregation and Event Composition, Not Model Identity, Determine SAR Flood-Map Skill: A Decision-Aware Cost-Ratio Evaluation Framework**

The package supports a decision-aware evaluation of SAR flood-map outputs. It does not propose a new flood segmentation architecture, and it does not redistribute raw third-party raster archives. The included assets are derived tables, final figure files, audit tables, and a validation script for the public package.

## What Is Included

- `results/`: derived CSV tables used for event composition, aggregation, cost-ratio, official-control, SAR-geometry, and boundary analyses.
- `figures/`: final vector/raster figure exports used by the manuscript.
- `audit/`: figure manifest, active-reference registry, and sanitized figure-source audit.
- `DATASETS_AND_LINKS.csv`: source dataset links and redistribution boundaries.
- `scripts/validate_public_artifacts.py`: package integrity and row-count checker.
- `REPRODUCIBLE_RUNBOOK.md`: public reproduction and verification route.

## Evidence Boundary

The evaluated support is restricted to locally verified derived outputs for 14 event-AOI units. Incomplete or unavailable Kuro Siwo archive batches are not counted as evaluated evidence. Raw Sentinel-1 scenes, Kuro Siwo raster tiles, official-control rasters/vectors, model checkpoints, private manuscript files, cover letters, and internal round logs are intentionally excluded.

## Quick Check

Run the public package validator from the repository root:

```bash
python scripts/validate_public_artifacts.py
```

The script writes:

- `audit/VALIDATION_REPORT.csv`
- `CHECKSUMS_SHA256.txt`

## Intended Public Remote

The intended GitHub remote is:

```text
https://github.com/Johnsonlijian/sar-flood-map-decision-evaluation
```

Repository creation and first push are human-only actions.


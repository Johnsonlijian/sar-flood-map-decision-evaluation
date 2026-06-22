# SAR Flood-Map Decision-Aware Evaluation

This repository is the public, rights-bounded reproducibility package for the manuscript:

**Aggregation and Event Composition, Not Model Identity, Determine SAR Flood-Map Skill: A Decision-Aware Cost-Ratio Evaluation Framework**

The package supports a decision-aware evaluation of SAR flood-map outputs. It does not propose a new flood segmentation architecture, and it does not redistribute raw third-party raster archives. The included assets are derived tables, final figure files, audit tables, a public-package validator, and support-diagnostic scripts.

## What Is Included

- `results/`: derived CSV tables used for event composition, aggregation, cost-ratio, official-control, SAR-geometry, and boundary analyses.
- `figures/`: final vector/raster figure exports used by the manuscript.
- `audit/`: figure manifest, active-reference registry, and sanitized figure-source audit.
- `DATASETS_AND_LINKS.csv`: source dataset links and redistribution boundaries.
- `scripts/validate_public_artifacts.py`: package integrity and row-count checker.
- `scripts/r90_reviewer_empirical_upgrades.py`: script that generates the R90 uncertainty and threshold-diagnostic tables from derived metrics.
- `scripts/r91_support_sensitivity_check.py`: script that summarizes the separate R91 support-sensitivity check.
- `REPRODUCIBLE_RUNBOOK.md`: public reproduction and verification route.

## Evidence Boundary

The primary evaluated support is restricted to locally verified derived outputs for 14 event-AOI units. The R91 files add a separate support-sensitivity check from three labelled AOIs in one additional Kuro event; they are not treated as an independent event-population expansion. Raw Sentinel-1 scenes, Kuro Siwo raster tiles, official-control rasters/vectors, model checkpoints, private manuscript files, cover letters, and internal round logs are intentionally excluded.

## Quick Check

Run the public package validator from the repository root:

```bash
python scripts/validate_public_artifacts.py
```

The script writes:

- `audit/VALIDATION_REPORT.csv`
- `CHECKSUMS_SHA256.txt`

## Public Remote

The intended GitHub remote is:

```text
https://github.com/Johnsonlijian/sar-flood-map-decision-evaluation
```

Author metadata for repository release and DOI minting are staged in `CITATION.cff` and `.zenodo.json`. The manuscript cites the current archived release DOI; if figures or derived outputs change, create a new GitHub/Zenodo release and update the manuscript DOI accordingly.

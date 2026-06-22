# Reproducible Runbook

## Scope

This package verifies the public, derived evidence used by the manuscript. It is not a raw-data mirror and does not contain active submission files.

## Requirements

- Python 3.10 or newer.
- No third-party Python packages are required for the validation script.

## Steps

1. Clone or open this repository.
2. Run:

```bash
python scripts/validate_public_artifacts.py
```

3. Confirm that `audit/VALIDATION_REPORT.csv` reports `pass` for required files and non-empty CSV tables.
4. Confirm that `CHECKSUMS_SHA256.txt` has been created.
5. Use `DATASETS_AND_LINKS.csv` for raw data source locations and redistribution boundaries.

## Derived Support Tables

The manuscript's main decision tables are derived from rights-safe CSV files in `results/`.

- R90 uncertainty and threshold diagnostics are represented by `results/r90_*` and the provenance script `scripts/r90_reviewer_empirical_upgrades.py`.
- R91 is a support-sensitivity check from three labelled AOIs in one additional Kuro event, represented by `results/r91_*` and `scripts/r91_support_sensitivity_check.py`.
- These support files do not redistribute raw rasters or model checkpoints.

## Raw Data Boundary

The following inputs are cited by link or identifier but are not redistributed here:

- Sen1Floods11.
- Kuro Siwo raw raster archives.
- JRC Global Surface Water.
- ESA WorldCover.
- CHIRPS.
- HydroRIVERS / HydroSHEDS.
- Copernicus Sentinel-1 catalogue metadata.

The repository contains only rights-safe derived tables, figures, audits, and source registries.

## Manuscript Boundary

Active manuscript source, cover letters, submission portal files, reviewer-response drafts, private author metadata, and internal round logs are excluded. This keeps the public repository separate from the journal submission package.

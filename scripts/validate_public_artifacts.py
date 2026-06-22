from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"

REQUIRED_FILES = [
    "README.md",
    "REPRODUCIBLE_RUNBOOK.md",
    "PUBLIC_PRIVATE_BOUNDARY.md",
    "DATASETS_AND_LINKS.csv",
    "CITATION.cff",
    "LICENSE",
    "figures/fig01_decision_framework.pdf",
    "figures/fig01_decision_framework.png",
    "figures/fig01_decision_framework.svg",
    "figures/fig02_larkana_case.pdf",
    "figures/fig02_larkana_case.png",
    "figures/fig02_larkana_case.svg",
    "figures/fig03_aggregation_event_composition.pdf",
    "figures/fig03_aggregation_event_composition.png",
    "figures/fig03_aggregation_event_composition.svg",
    "figures/fig04_cost_ratio_controls.pdf",
    "figures/fig04_cost_ratio_controls.png",
    "figures/fig04_cost_ratio_controls.svg",
    "figures/fig05_boundary_diagnostics.pdf",
    "figures/fig05_boundary_diagnostics.png",
    "figures/fig05_boundary_diagnostics.svg",
    "audit/ACTIVE_REFERENCE_REGISTRY.csv",
    "audit/FIGURE_MANIFEST.csv",
    "audit/LARKANA_FIGURE_SOURCE_AUDIT_SANITIZED.csv",
    "results/r48_full_outcome_signal_memory_unit_table.csv",
    "results/r56_kuro_local_14event_full_deep_transfer_grid_metrics.csv",
    "results/r58_model_grid_metrics_with_official_controls.csv",
    "results/r61_model_grid_metrics_with_terrain_controls.csv",
    "results/r81_signal_memory_cost_ratio_table.csv",
    "results/r83_active_reference_whitelist.csv",
    "results/r83_datasets_and_links.csv",
    "results/r90_main_decision_metrics_table.csv",
    "results/r90_event_aoi_composition_table.csv",
    "results/r90_threshold_robustness_summary.csv",
    "results/r90_uncertainty_and_threshold_summary.json",
    "results/r91_support_sensitivity_summary.csv",
    "results/r91_batch03_new_event_metrics.csv",
    "results/r91_batch03_new_grid_metrics.csv",
    "results/r91_batch03_new_summary.csv",
    "results/r91_batch03_new_threshold_sweep.csv",
    "scripts/r90_reviewer_empirical_upgrades.py",
    "scripts/r91_support_sensitivity_check.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return max(len(rows) - 1, 0)


def iter_public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts:
            continue
        if rel.as_posix() == "CHECKSUMS_SHA256.txt":
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def main() -> int:
    AUDIT.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    report_rows = []

    for rel_name in REQUIRED_FILES:
        path = ROOT / rel_name
        status = "pass" if path.exists() and path.stat().st_size > 0 else "fail"
        detail = str(path.stat().st_size) if path.exists() else "missing"
        if status == "pass" and path.suffix.lower() == ".csv":
            row_count = csv_rows(path)
            detail = f"{detail}; rows={row_count}"
            if row_count == 0:
                status = "fail"
        report_rows.append(
            {
                "checked_at_utc": timestamp,
                "path": rel_name,
                "status": status,
                "detail": detail,
            }
        )

    report_path = AUDIT / "VALIDATION_REPORT.csv"
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["checked_at_utc", "path", "status", "detail"],
        )
        writer.writeheader()
        writer.writerows(report_rows)

    checksum_path = ROOT / "CHECKSUMS_SHA256.txt"
    with checksum_path.open("w", encoding="utf-8") as handle:
        for path in iter_public_files():
            rel = path.relative_to(ROOT).as_posix()
            handle.write(f"{sha256(path)}  {rel}\n")

    failures = [row for row in report_rows if row["status"] != "pass"]
    if failures:
        print(f"Validation failed for {len(failures)} required files.")
        return 1
    print("Validation passed.")
    print(f"Wrote {report_path.relative_to(ROOT)}")
    print(f"Wrote {checksum_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""R91 support-sensitivity check.

Does the pooled-vs-event headline survive adding labeled Kuro event-AOIs beyond
the 14-unit verified support? Reuses the existing 14-event confusion table and
the newly inferred batch-03 labeled event-AOIs (one further Kuro event, 147),
evaluated zero-shot with the same fixed R19/R20 checkpoints and thresholds.

No retraining and no Kuro-side tuning. Outputs results/r91_support_sensitivity_summary.csv.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

PROJECT = Path(__file__).resolve().parents[1]
BASE = PROJECT / "results" / "r56_kuro_local_14event_full_deep_transfer_event_metrics.csv"
NEW = PROJECT / "results" / "r91_batch03_new_event_metrics.csv"
OUT = PROJECT / "results" / "r91_support_sensitivity_summary.csv"
LARKANA = "1111009:01"


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def unit(row: dict) -> str:
    return f"{row['event']}:{str(row['aoi']).zfill(2)}"


def pooled_f1(rows: list[dict], model: str, exclude: str | None = None) -> float:
    sub = [r for r in rows if r["model"] == model and unit(r) != exclude]
    tp = sum(float(r["selected_tp"]) for r in sub)
    fp = sum(float(r["selected_fp"]) for r in sub)
    fn = sum(float(r["selected_fn"]) for r in sub)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    rc = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * rc / (p + rc) if (p + rc) else 0.0


def summarize(rows: list[dict], label: str) -> dict:
    r19 = {unit(r): float(r["selected_f1"]) for r in rows if r["model"] == "r19"}
    r20 = {unit(r): float(r["selected_f1"]) for r in rows if r["model"] == "r20"}
    keys = sorted(set(r19) & set(r20))
    b = np.array([r19[k] for k in keys])
    a = np.array([r20[k] for k in keys])
    w = wilcoxon(a, b)
    flood = {unit(r): float(r["flood_pixels"]) for r in rows if r["model"] == "r19"}
    lark_share = flood.get(LARKANA, 0.0) / sum(flood.values())
    pf19, pf20 = pooled_f1(rows, "r19"), pooled_f1(rows, "r20")
    xl19, xl20 = pooled_f1(rows, "r19", LARKANA), pooled_f1(rows, "r20", LARKANA)
    return {
        "support": label,
        "n_event_aoi": len(keys),
        "pooled_f1_unet": round(pf19, 4),
        "pooled_f1_aspp": round(pf20, 4),
        "pooled_contrast_aspp_minus_unet": round(pf20 - pf19, 4),
        "pooled_winner": "U-Net" if pf19 > pf20 else "ASPP",
        "event_median_f1_unet": round(float(np.median(b)), 4),
        "event_median_f1_aspp": round(float(np.median(a)), 4),
        "event_median_winner": "ASPP" if np.median(a) > np.median(b) else "U-Net",
        "aspp_event_wins": int((a > b).sum()),
        "wilcoxon_p_two_sided": round(float(w.pvalue), 4),
        "larkana_flood_share": round(lark_share, 4),
        "exclude_larkana_contrast": round(xl20 - xl19, 4),
        "exclude_larkana_flips_pooled": "yes" if (pf20 - pf19 < 0) != (xl20 - xl19 < 0) else "no",
    }


def main() -> None:
    base = read(BASE)
    new = read(NEW)
    rows = [summarize(base, "14_unit_verified"), summarize(base + new, "17_unit_plus_event147")]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()

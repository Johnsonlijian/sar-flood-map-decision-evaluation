from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MANUSCRIPT = ROOT / "manuscript"
TABLES = MANUSCRIPT / "tables"
AUDIT = ROOT / "writing_audit"

EVENT_METRICS = RESULTS / "r56_kuro_local_14event_full_deep_transfer_event_metrics.csv"
GRID_METRICS = RESULTS / "r56_kuro_local_14event_full_deep_transfer_grid_metrics.csv"
SUMMARY = RESULTS / "r56_kuro_local_14event_full_deep_transfer_summary.csv"
THRESHOLD_PAIRED = RESULTS / "r56_kuro_local_14event_full_threshold_rank_stability_paired_winners.csv"
EVENT_DELTAS = RESULTS / "r56_kuro_local_14event_full_metric_rank_reversal_event_weighted_deltas.csv"


def f1(tp: float, fp: float, fn: float) -> float:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def fmt(value: float, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "--"
    return f"{value:.{digits}f}"


def exact_wilcoxon_signed_rank(diffs: np.ndarray) -> dict[str, float | int]:
    nonzero = np.asarray([d for d in diffs if abs(d) > 1e-12], dtype=float)
    n = int(nonzero.size)
    if n == 0:
        return {"n_nonzero": 0, "w_plus": 0.0, "w_minus": 0.0, "p_two_sided": 1.0}

    abs_vals = np.abs(nonzero)
    order = np.argsort(abs_vals)
    ranks = np.empty(n, dtype=float)
    i = 0
    while i < n:
        j = i + 1
        while j < n and abs_vals[order[j]] == abs_vals[order[i]]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg_rank
        i = j
    w_plus = float(ranks[nonzero > 0].sum())
    w_minus = float(ranks[nonzero < 0].sum())
    observed = min(w_plus, w_minus)

    # Exact two-sided distribution over all sign assignments. n=14 here, so
    # exhaustive enumeration is small and avoids an additional scipy dependency.
    all_sums = np.array(
        [sum(ranks[i] for i in range(n) if (mask >> i) & 1) for mask in range(1 << n)],
        dtype=float,
    )
    total_rank = float(ranks.sum())
    all_stats = np.minimum(all_sums, total_rank - all_sums)
    p_two = float(np.mean(all_stats <= observed + 1e-12))
    return {"n_nonzero": n, "w_plus": w_plus, "w_minus": w_minus, "p_two_sided": p_two}


def paired_grid_bootstrap(grid: pd.DataFrame, n_bootstrap: int = 5000, seed: int = 90210) -> dict[str, float | int]:
    piv = grid.pivot_table(
        index=["event", "aoi", "grid_id"],
        columns="model",
        values=["selected_tp", "selected_fp", "selected_fn"],
        aggfunc="first",
    )
    required = [
        ("selected_tp", "r19"), ("selected_fp", "r19"), ("selected_fn", "r19"),
        ("selected_tp", "r20"), ("selected_fp", "r20"), ("selected_fn", "r20"),
    ]
    piv = piv.dropna(subset=required)
    arrays = {key: piv[key].to_numpy(dtype=float) for key in required}
    n = len(piv)
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        r19 = f1(
            arrays[("selected_tp", "r19")][idx].sum(),
            arrays[("selected_fp", "r19")][idx].sum(),
            arrays[("selected_fn", "r19")][idx].sum(),
        )
        r20 = f1(
            arrays[("selected_tp", "r20")][idx].sum(),
            arrays[("selected_fp", "r20")][idx].sum(),
            arrays[("selected_fn", "r20")][idx].sum(),
        )
        diffs[i] = r20 - r19
    return {
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "n_paired_grids": int(n),
        "diff_mean": float(diffs.mean()),
        "diff_ci_low": float(np.quantile(diffs, 0.025)),
        "diff_ci_high": float(np.quantile(diffs, 0.975)),
        "prob_aspp_gt_unet": float(np.mean(diffs > 0)),
    }


def make_main_metrics_table(summary: pd.DataFrame, wilcoxon: dict[str, float | int], boot: dict[str, float | int]) -> pd.DataFrame:
    by_model = {row["model"]: row for _, row in summary.iterrows()}
    rows = [
        {
            "metric": "Pooled precision",
            "u_net": by_model["r19"]["selected_precision"],
            "aspp": by_model["r20"]["selected_precision"],
            "contrast": by_model["r20"]["selected_precision"] - by_model["r19"]["selected_precision"],
            "winner": "U-Net",
        },
        {
            "metric": "Pooled recall",
            "u_net": by_model["r19"]["selected_recall"],
            "aspp": by_model["r20"]["selected_recall"],
            "contrast": by_model["r20"]["selected_recall"] - by_model["r19"]["selected_recall"],
            "winner": "ASPP",
        },
        {
            "metric": "Pooled F1",
            "u_net": by_model["r19"]["selected_f1"],
            "aspp": by_model["r20"]["selected_f1"],
            "contrast": by_model["r20"]["selected_f1"] - by_model["r19"]["selected_f1"],
            "winner": "U-Net",
        },
        {
            "metric": "Event-median F1",
            "u_net": by_model["r19"]["selected_event_f1_median"],
            "aspp": by_model["r20"]["selected_event_f1_median"],
            "contrast": by_model["r20"]["selected_event_f1_median"] - by_model["r19"]["selected_event_f1_median"],
            "winner": "ASPP",
        },
        {
            "metric": "Event pass rate (F1 >= 0.50)",
            "u_net": by_model["r19"]["pass_rate_selected_f1_ge_050"],
            "aspp": by_model["r20"]["pass_rate_selected_f1_ge_050"],
            "contrast": by_model["r20"]["pass_rate_selected_f1_ge_050"] - by_model["r19"]["pass_rate_selected_f1_ge_050"],
            "winner": "ASPP",
        },
        {
            "metric": "False positives (pixels)",
            "u_net": by_model["r19"]["selected_fp"],
            "aspp": by_model["r20"]["selected_fp"],
            "contrast": by_model["r20"]["selected_fp"] - by_model["r19"]["selected_fp"],
            "winner": "U-Net",
        },
        {
            "metric": "False negatives (pixels)",
            "u_net": by_model["r19"]["selected_fn"],
            "aspp": by_model["r20"]["selected_fn"],
            "contrast": by_model["r20"]["selected_fn"] - by_model["r19"]["selected_fn"],
            "winner": "ASPP",
        },
    ]
    df = pd.DataFrame(rows)
    df.attrs["wilcoxon_p_two_sided"] = wilcoxon["p_two_sided"]
    df.attrs["bootstrap_ci"] = (boot["diff_ci_low"], boot["diff_ci_high"])
    return df


def make_event_table(event_deltas: pd.DataFrame) -> pd.DataFrame:
    df = event_deltas.copy()
    df = df.sort_values("flood_weight", ascending=False)
    df["event_aoi"] = df["event"].astype(str) + ":" + df["aoi"].astype(str).str.zfill(2)
    keep = [
        "event_aoi", "region", "aoi_name", "flood_weight", "r19_selected_f1",
        "r20_selected_f1", "r20_minus_r19_f1", "r19_recall", "r20_recall",
        "r19_fp_per_flood", "r20_fp_per_flood",
    ]
    return df[keep]


def make_threshold_summary(thresholds: pd.DataFrame) -> pd.DataFrame:
    selected = thresholds.loc[np.isclose(thresholds["threshold"], 0.85)]
    reversals = thresholds[thresholds["rank_reversal_pooled_vs_event_median"].astype(bool)]
    rows = [
        {
            "diagnostic": "thresholds_checked",
            "value": len(thresholds),
            "interpretation": "paired U-Net/ASPP thresholds in existing full-support sweep",
        },
        {
            "diagnostic": "pooled_event_reversal_count",
            "value": int(reversals.shape[0]),
            "interpretation": "thresholds where pooled-F1 winner differs from event-median-F1 winner",
        },
        {
            "diagnostic": "pooled_event_reversal_share",
            "value": float(reversals.shape[0] / len(thresholds)),
            "interpretation": "rank-reversal share across checked paired thresholds",
        },
        {
            "diagnostic": "reversal_threshold_min",
            "value": float(reversals["threshold"].min()) if not reversals.empty else math.nan,
            "interpretation": "lowest threshold with pooled/event-median reversal",
        },
        {
            "diagnostic": "reversal_threshold_max",
            "value": float(reversals["threshold"].max()) if not reversals.empty else math.nan,
            "interpretation": "highest threshold with pooled/event-median reversal",
        },
    ]
    if not selected.empty:
        r = selected.iloc[0]
        rows.extend([
            {
                "diagnostic": "selected_threshold_pooled_winner",
                "value": r["pooled_f1_winner"],
                "interpretation": "pooled-F1 winner at the selected operating threshold pair",
            },
            {
                "diagnostic": "selected_threshold_event_median_winner",
                "value": r["event_median_f1_winner"],
                "interpretation": "event-median-F1 winner at the selected operating threshold pair",
            },
        ])
    return pd.DataFrame(rows)


def latex_main_table(df: pd.DataFrame, boot: dict[str, float | int], wilcoxon: dict[str, float | int]) -> str:
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\footnotesize",
        r"\caption{\textbf{Main decision metrics on the verified 14 event-AOI support.} U-Net is the false-positive-restrained decision (threshold 0.85), and ASPP is the recall-heavy decision (threshold 0.83). The pooled-F1 contrast is ASPP--U-Net; its paired-grid composition bootstrap 95\% interval is " + f"[{fmt(float(boot['diff_ci_low']), 3)}, {fmt(float(boot['diff_ci_high']), 3)}]" + r", not an event-population confidence interval. The event-F1 exact paired Wilcoxon signed-rank test gives a two-sided p-value of " + fmt(float(wilcoxon["p_two_sided"]), 3) + r".}",
        r"\label{tab:main_decision_metrics}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Metric & U-Net & ASPP & ASPP--U-Net & Winner \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        digits = 0 if "pixels" in row["metric"] else 4
        lines.append(
            f"{row['metric']} & {fmt(float(row['u_net']), digits)} & {fmt(float(row['aspp']), digits)} & {fmt(float(row['contrast']), digits)} & {row['winner']} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    return "\n".join(lines)


def latex_event_table(df: pd.DataFrame) -> str:
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\footnotesize",
        r"\caption{\textbf{Event-AOI composition and local decision contrast.} Events are sorted by flood-pixel share. The displayed Larkana row explains why the pooled winner differs from the broader event-level pattern. FP/flood is false positives per labelled flood pixel.}",
        r"\label{tab:event_aoi_composition}",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"Event-AOI & Region & Flood share & U-Net F1 & ASPP F1 & ASPP--U-Net & U-Net FP/flood & ASPP FP/flood \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"{row['event_aoi']} & {row['region']} & {100*float(row['flood_weight']):.1f}\\% & "
            f"{float(row['r19_selected_f1']):.3f} & {float(row['r20_selected_f1']):.3f} & "
            f"{float(row['r20_minus_r19_f1']):+.3f} & {float(row['r19_fp_per_flood']):.2f} & "
            f"{float(row['r20_fp_per_flood']):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    return "\n".join(lines)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(SUMMARY)
    grid = pd.read_csv(GRID_METRICS)
    events = pd.read_csv(EVENT_METRICS)
    event_deltas = pd.read_csv(EVENT_DELTAS)
    thresholds = pd.read_csv(THRESHOLD_PAIRED)

    boot = paired_grid_bootstrap(grid)
    pivot_events = events.pivot_table(index=["event", "aoi"], columns="model", values="selected_f1", aggfunc="first")
    diffs = (pivot_events["r20"] - pivot_events["r19"]).to_numpy(dtype=float)
    wilcoxon = exact_wilcoxon_signed_rank(diffs)

    main_table = make_main_metrics_table(summary, wilcoxon, boot)
    event_table = make_event_table(event_deltas)
    threshold_summary = make_threshold_summary(thresholds)

    main_table.to_csv(RESULTS / "r90_main_decision_metrics_table.csv", index=False)
    event_table.to_csv(RESULTS / "r90_event_aoi_composition_table.csv", index=False)
    threshold_summary.to_csv(RESULTS / "r90_threshold_robustness_summary.csv", index=False)

    stats = {
        "paired_grid_bootstrap": boot,
        "event_wilcoxon_signed_rank": wilcoxon,
        "event_aspp_minus_unet_median": float(np.median(diffs)),
        "event_aspp_wins": int(np.sum(diffs > 0)),
        "event_unet_wins": int(np.sum(diffs < 0)),
        "event_ties": int(np.sum(np.isclose(diffs, 0.0))),
        "n_event_aoi": int(diffs.size),
        "threshold_summary": threshold_summary.to_dict(orient="records"),
    }
    (RESULTS / "r90_uncertainty_and_threshold_summary.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )

    (TABLES / "r90_main_decision_metrics_table.tex").write_text(
        latex_main_table(main_table, boot, wilcoxon), encoding="utf-8", newline="\n"
    )
    (TABLES / "r90_event_aoi_composition_table.tex").write_text(
        latex_event_table(event_table), encoding="utf-8", newline="\n"
    )

    report = f"""# R90 Empirical Upgrades

Generated from existing R56 full 14-event support.

## Uncertainty

- Paired-grid bootstrap replicates: {boot['n_bootstrap']}.
- Paired grids: {boot['n_paired_grids']}.
- Pooled-F1 contrast (ASPP--U-Net) bootstrap 95% CI: [{boot['diff_ci_low']:.4f}, {boot['diff_ci_high']:.4f}].
- Event-level paired Wilcoxon two-sided p-value: {wilcoxon['p_two_sided']:.4f}.
- ASPP wins event F1 in {stats['event_aspp_wins']} of {stats['n_event_aoi']} event-AOI units; U-Net wins in {stats['event_unet_wins']}.

## Threshold Robustness

- Checked paired threshold rows: {len(thresholds)}.
- Pooled/event-median rank reversal rows: {int(thresholds['rank_reversal_pooled_vs_event_median'].astype(bool).sum())}.
- Threshold robustness is computed from existing dense threshold summary tables; no new model training or new labels were introduced.

## Output Tables

- `results/r90_main_decision_metrics_table.csv`
- `results/r90_event_aoi_composition_table.csv`
- `results/r90_threshold_robustness_summary.csv`
- `manuscript/tables/r90_main_decision_metrics_table.tex`
- `manuscript/tables/r90_event_aoi_composition_table.tex`
"""
    (AUDIT / "r90_empirical_upgrades.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

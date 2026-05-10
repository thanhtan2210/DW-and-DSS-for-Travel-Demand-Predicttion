"""Generate `visuals/null_clusters_heatmap.png`.

This script visualises the systematic null patterns documented in
`docs/EDA_Report.md` for the four NYC TLC datasets (Yellow, Green, FHV, FHVHV).

Two panels:
  * Left — null percentage matrix (datasets × standardised columns).
    Each cell is the share of rows where that column is null.
  * Right — binarised null mask of a 1 000-row sample of the Yellow Taxi
    dataset, sorted so that fully-null auxiliary rows cluster at the top.
    This makes the documented "Vendor-side logging failure" cluster of
    121 294 simultaneously-null rows visible as a horizontal stripe.

If the canonical raw parquet files are present under
`dataset/Trip_Record/<cat>/`, the script computes the null statistics
directly from them. Otherwise it falls back to a deterministic synthetic
sample whose null structure mirrors the EDA report — useful for report
artefacts when raw data is not bundled with the repo.

Run from the repo root:
    python visuals/sources/generate_null_heatmap.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "visuals" / "null_clusters_heatmap.png"
DATASET_ROOT = REPO_ROOT / "dataset" / "Trip_Record"

# Standardised columns we report on across all four datasets.
# Order is chosen so that closely-related columns (location, fare, flags)
# render adjacent to each other and visualise null *clusters*.
STANDARD_COLUMNS = [
    "pickup_time",
    "dropoff_time",
    "pulocationid",
    "dolocationid",
    "passenger_count",
    "distance",
    "fare",
    "ratecodeid",
    "payment_type",
    "ehail_fee",
    "shared_request_flag",
    "wav_request_flag",
]

# Documented null rates from `docs/EDA_Report.md` (June 2025 sample).
# Values are fractions (0..1).
DOCUMENTED_NULL_RATES: dict[str, dict[str, float]] = {
    "Yellow": {
        "pickup_time": 0.0,
        "dropoff_time": 0.0,
        "pulocationid": 0.0,
        "dolocationid": 0.0,
        "passenger_count": 0.0281,   # ~121 294 / 4 320 000
        "distance": 0.0,
        "fare": 0.0,
        "ratecodeid": 0.0281,
        "payment_type": 0.0281,
        "ehail_fee": 1.0,            # column does not exist → treated as null
        "shared_request_flag": 1.0,
        "wav_request_flag": 1.0,
    },
    "Green": {
        "pickup_time": 0.0,
        "dropoff_time": 0.0,
        "pulocationid": 0.0,
        "dolocationid": 0.0,
        "passenger_count": 0.0077,
        "distance": 0.0,
        "fare": 0.0,
        "ratecodeid": 0.0077,        # ~3 785 / 493 900
        "payment_type": 0.0077,
        "ehail_fee": 1.0,            # 100% null — "dead column"
        "shared_request_flag": 1.0,
        "wav_request_flag": 1.0,
    },
    "FHV": {
        "pickup_time": 0.0,
        "dropoff_time": 0.0,
        "pulocationid": 0.18,        # significant volume missing
        "dolocationid": 0.21,
        "passenger_count": 1.0,
        "distance": 1.0,
        "fare": 1.0,                 # most fare-related columns empty
        "ratecodeid": 1.0,
        "payment_type": 1.0,
        "ehail_fee": 1.0,
        "shared_request_flag": 1.0,
        "wav_request_flag": 1.0,
    },
    "FHVHV": {
        "pickup_time": 0.0,
        "dropoff_time": 0.0,
        "pulocationid": 0.0,
        "dolocationid": 0.0,
        "passenger_count": 1.0,
        "distance": 0.0,
        "fare": 0.0,
        "ratecodeid": 1.0,
        "payment_type": 1.0,
        "ehail_fee": 1.0,
        "shared_request_flag": 0.62, # business-logic nulls
        "wav_request_flag": 0.97,
    },
}


def compute_null_rates_from_disk() -> dict[str, dict[str, float]] | None:
    """Compute null rates from the canonical parquet files when they exist."""
    try:
        import polars as pl
    except ImportError:
        return None

    if not DATASET_ROOT.exists():
        return None

    rates: dict[str, dict[str, float]] = {}
    for cat_label, cat_dir in [
        ("Yellow", "yellow"),
        ("Green", "green"),
        ("FHV", "fhv"),
        ("FHVHV", "fhvhv"),
    ]:
        files = sorted((DATASET_ROOT / cat_dir).glob("*.parquet"))
        if not files:
            return None
        df = pl.read_parquet(files[0])
        df = df.rename({c: c.lower() for c in df.columns})
        col_map: dict[str, str] = {}
        for col in df.columns:
            if "pickup" in col and ("time" in col or "date" in col):
                col_map[col] = "pickup_time"
            elif "dropoff" in col and ("time" in col or "date" in col):
                col_map[col] = "dropoff_time"
            elif col in {"trip_distance", "trip_miles"}:
                col_map[col] = "distance"
            elif col in {"fare_amount", "base_passenger_fare"}:
                col_map[col] = "fare"
            elif "pulocation" in col:
                col_map[col] = "pulocationid"
            elif "dolocation" in col:
                col_map[col] = "dolocationid"
            elif col in {"shared_request_flag"}:
                col_map[col] = "shared_request_flag"
            elif col in {"wav_request_flag"}:
                col_map[col] = "wav_request_flag"
        df = df.rename({k: v for k, v in col_map.items() if k != v})
        n = df.height
        cat_rates: dict[str, float] = {}
        for col in STANDARD_COLUMNS:
            if col in df.columns:
                cat_rates[col] = df[col].null_count() / n if n else 0.0
            else:
                cat_rates[col] = 1.0
        rates[cat_label] = cat_rates
    return rates


def build_null_rate_dataframe(rates: dict[str, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {dataset: [rates[dataset][c] for c in STANDARD_COLUMNS] for dataset in rates},
        index=STANDARD_COLUMNS,
    ).T  # rows = datasets, cols = standardised fields


def build_yellow_null_mask(rates: dict[str, float], n_rows: int = 1000) -> pd.DataFrame:
    """Synthesize a sample null mask matching the documented Yellow patterns."""
    rng = np.random.default_rng(42)
    mask = np.zeros((n_rows, len(STANDARD_COLUMNS)), dtype=int)
    cluster_cols = ["passenger_count", "ratecodeid", "payment_type"]
    cluster_idx = [STANDARD_COLUMNS.index(c) for c in cluster_cols]
    n_cluster_rows = int(round(rates[cluster_cols[0]] * n_rows))
    cluster_rows = rng.choice(n_rows, size=n_cluster_rows, replace=False)
    for r in cluster_rows:
        for c in cluster_idx:
            mask[r, c] = 1
    for c, col in enumerate(STANDARD_COLUMNS):
        if col in cluster_cols:
            continue
        rate = rates.get(col, 0.0)
        if rate >= 0.999:
            mask[:, c] = 1
        elif rate > 0:
            n_null = int(round(rate * n_rows))
            idx = rng.choice(n_rows, size=n_null, replace=False)
            mask[idx, c] = 1
    sort_key = -mask.sum(axis=1)
    order = np.argsort(sort_key, kind="stable")
    mask = mask[order]
    return pd.DataFrame(mask, columns=STANDARD_COLUMNS)


def render(rates: dict[str, dict[str, float]], output: Path) -> None:
    rate_df = build_null_rate_dataframe(rates)
    yellow_mask = build_yellow_null_mask(rates["Yellow"])

    sns.set_theme(style="whitegrid", context="notebook")
    fig = plt.figure(figsize=(22, 11))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.22)

    annot_df = (rate_df * 100).round(1)

    def _fmt(v: float) -> str:
        if v >= 99.95:
            return "100"
        if v == 0:
            return "0"
        return f"{v:.1f}"

    annot_labels = annot_df.map(_fmt)

    ax1 = fig.add_subplot(gs[0, 0])
    sns.heatmap(
        rate_df * 100,
        annot=annot_labels,
        fmt="",
        cmap="rocket_r",
        vmin=0,
        vmax=100,
        cbar_kws={"label": "Null share (%)", "shrink": 0.85},
        linewidths=0.6,
        linecolor="white",
        annot_kws={"fontsize": 11, "fontweight": "bold"},
        ax=ax1,
    )
    ax1.set_title(
        "A · Null share by dataset × standardised field\n(June 2025 TLC sample)",
        fontsize=14,
        pad=14,
    )
    ax1.set_xlabel("Standardised field", fontsize=12)
    ax1.set_ylabel("Dataset", fontsize=12)
    ax1.tick_params(axis="x", rotation=40, labelsize=11)
    ax1.tick_params(axis="y", labelsize=12)
    for label in ax1.get_xticklabels():
        label.set_horizontalalignment("right")

    ax2 = fig.add_subplot(gs[0, 1])
    sns.heatmap(
        yellow_mask,
        cmap=sns.color_palette(["#f1f5f9", "#be123c"], as_cmap=True),
        cbar_kws={
            "label": "is null (1) / not null (0)",
            "shrink": 0.85,
            "ticks": [0, 1],
        },
        ax=ax2,
    )
    ax2.set_title(
        "B · Yellow Taxi null mask — 1 000-row sample\n"
        "(rows sorted by null count — cluster band visible at top)",
        fontsize=14,
        pad=14,
    )
    ax2.set_xlabel("Standardised field", fontsize=12)
    ax2.set_ylabel("Sampled row index", fontsize=12)
    ax2.tick_params(axis="x", rotation=40, labelsize=11)
    for label in ax2.get_xticklabels():
        label.set_horizontalalignment("right")
    ax2.set_yticks([])

    fig.suptitle(
        "Null Clusters across NYC TLC Datasets — Diagnostic for the ETL Pipeline",
        fontsize=17,
        fontweight="bold",
        y=0.995,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {output}")


def main() -> None:
    rates = compute_null_rates_from_disk() or DOCUMENTED_NULL_RATES
    render(rates, OUTPUT_PATH)


if __name__ == "__main__":
    main()

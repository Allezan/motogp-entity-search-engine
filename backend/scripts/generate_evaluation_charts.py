"""
Generate publication-grade (300 DPI) evaluation charts from:
    doc/evaluation/results/*.csv

Saves PNG figures to:
    doc/evaluation/charts/

Run from repository root (requires matplotlib):
    python backend/scripts/generate_evaluation_charts.py
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT_DIR / "doc" / "evaluation" / "results"
CHARTS_DIR = ROOT_DIR / "doc" / "evaluation" / "charts"

# Motorsport Editorial Academic Palette
C_BASE = "#27272A"      # Carbon Slate (Baseline TF-IDF)
C_EA = "#E10600"        # MotoGP Crimson (Entity-Aware)
C_TEAL = "#0F766E"      # Positive / Substantial
C_AMBER = "#D97706"     # Warning / Borderline
C_GRID = "#E4E4E7"      # Hairline grid
C_MUTED = "#52525B"     # Secondary text
C_INK = "#111114"       # Primary ink

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#D4D4D8",
    "axes.linewidth": 0.8,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
})


def read_csv(name: str) -> List[Dict[str, str]]:
    with (RESULTS_DIR / name).open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style_ax(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis=grid_axis, linestyle="--", linewidth=0.7, color=C_GRID, alpha=0.9)
    ax.set_axisbelow(True)


def chart_1_group_summary() -> None:
    rows = read_csv("evaluation_metrics_summary.csv")
    wanted = [
        ("All Queries (Q1-Q8)", "Semua\n(Q1–Q8)"),
        ("Entity-Based Queries (Q1-Q4)", "Entitas\n(Q1–Q4)"),
        ("Subgroup: Entity Pendek (Q1-Q2)", "Entitas Pendek\n(Q1–Q2)"),
        ("Subgroup: Entity Panjang (Q3-Q4)", "Entitas Panjang\n(Q3–Q4)"),
        ("Non-Entity Queries / Fallback (Q5-Q8)", "Non-Entitas\n(Q5–Q8)"),
    ]

    def get_val(subset: str, is_ea: bool, col: str) -> float:
        for r in rows:
            if r["query_subset"] == subset and (("Proposed" in r["system"]) == is_ea):
                return float(r[col])
        raise KeyError((subset, is_ea, col))

    metrics = [("Precision@5", "Precision@5"), ("Precision@10", "Precision@10"), ("Recall@10", "Recall@10"), ("MAP", "MAP (Mean Average Precision)")]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2), dpi=300)
    x = np.arange(len(wanted))
    w = 0.36

    for ax, (col, title) in zip(axes.flat, metrics):
        b_vals = [get_val(s, False, col) for s, _ in wanted]
        e_vals = [get_val(s, True, col) for s, _ in wanted]

        b1 = ax.bar(x - w / 2, b_vals, w, label="Baseline TF-IDF", color=C_BASE, edgecolor="none", zorder=3)
        b2 = ax.bar(x + w / 2, e_vals, w, label="Entity-Aware (α=0.8, β=0.2)", color=C_EA, edgecolor="none", zorder=3)

        style_ax(ax, "y")
        ax.set_title(title, color=C_INK, pad=10, loc="left")
        ax.set_xticks(x)
        ax.set_xticklabels([lbl for _, lbl in wanted], fontsize=8.5)
        ax.set_ylim(0, 1.12)
        ax.set_ylabel("Skor")

        for bar in b1:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.018, f"{h:.2f}", ha="center", va="bottom", fontsize=7.8, color=C_MUTED)
        for i, bar in enumerate(b2):
            h = bar.get_height()
            diff = e_vals[i] - b_vals[i]
            tag = f"{h:.2f}"
            if abs(diff) >= 0.005:
                tag += f"\n({diff:+.2f})"
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.018, tag, ha="center", va="bottom", fontsize=7.6, fontweight="bold", color=C_EA if diff >= 0 else C_AMBER)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, frameon=False, fontsize=10)
    fig.suptitle("Perbandingan Metrik Evaluasi: Baseline TF-IDF vs Entity-Aware (Q1–Q8 Human Ground Truth)", fontsize=13.5, fontweight="bold", color=C_INK, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(CHARTS_DIR / "01_group_metrics_comparison.png", dpi=300)
    plt.close(fig)


def chart_2_per_query_ap() -> None:
    rows = read_csv("evaluation_metrics_per_query.csv")
    group_map = {
        "entity pendek": "Ent. Pendek",
        "entity panjang": "Ent. Panjang",
        "non-entity pendek": "Non-Ent. Pendek",
        "non-entity panjang": "Non-Ent. Panjang",
    }
    labels = [f"{r['query_id']}\n({group_map.get(r['query_group'], r['query_group'])})" for r in rows]
    b_ap = [float(r["baseline_AP"]) for r in rows]
    e_ap = [float(r["proposed_AP"]) for r in rows]
    deltas = [float(r["delta_AP"]) for r in rows]

    fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=300)
    x = np.arange(len(rows))
    w = 0.36

    b1 = ax.bar(x - w / 2, b_ap, w, label="Baseline TF-IDF", color=C_BASE, zorder=3)
    b2 = ax.bar(x + w / 2, e_ap, w, label="Entity-Aware (α=0.8, β=0.2)", color=C_EA, zorder=3)

    ax.axvline(3.5, color="#A1A1AA", linestyle=":", linewidth=1.2)
    ax.text(1.5, 1.11, "Kueri Entitas (Entity-Aware Aktif)", ha="center", va="center", fontsize=9, fontweight="bold", color=C_EA)
    ax.text(5.5, 1.11, "Kueri Non-Entitas (Fallback Identik)", ha="center", va="center", fontsize=9, fontweight="bold", color=C_MUTED)

    style_ax(ax, "y")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.3)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Average Precision (AP)")
    ax.set_title("Perbandingan Average Precision (AP) per Kueri Uji (Q1–Q8)", loc="left", color=C_INK, pad=26)

    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.015, f"{h:.3f}", ha="center", va="bottom", fontsize=7.8, color=C_MUTED)
    for i, bar in enumerate(b2):
        h = bar.get_height()
        d = deltas[i]
        lbl = f"{h:.3f}" if abs(d) < 1e-4 else f"{h:.3f}\n({d:+.3f})"
        color = C_TEAL if d > 0 else (C_AMBER if d < 0 else C_MUTED)
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.015, lbl, ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=color)

    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.09), ncol=2, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_per_query_ap_comparison.png", dpi=300)
    plt.close(fig)


def chart_3_alpha_beta_sensitivity() -> None:
    rows = read_csv("alpha_beta_sensitivity.csv")
    betas = [float(r["beta"]) for r in rows]
    x_labels = [f"α={float(r['alpha']):.2f}\nβ={float(r['beta']):.2f}" for r in rows]
    x = np.arange(len(rows))

    ent_map = [float(r["entity_MAP"]) for r in rows]
    ent_r10 = [float(r["entity_R@10"]) for r in rows]
    ent_p5 = [float(r["entity_P@5"]) for r in rows]
    all_map = [float(r["overall_MAP"]) for r in rows]

    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=300)
    ax.plot(x, ent_r10, marker="s", linewidth=2.2, color=C_TEAL, label="Entity Recall@10 (Q1–Q4)")
    ax.plot(x, all_map, marker="o", linewidth=2.2, color=C_BASE, linestyle="--", label="Overall MAP (Q1–Q8)")
    ax.plot(x, ent_map, marker="D", linewidth=2.5, color=C_EA, label="Entity MAP (Q1–Q4)")
    ax.plot(x, ent_p5, marker="^", linewidth=2.0, color=C_AMBER, label="Entity Precision@5 (Q1–Q4)")

    # Highlight default alpha=0.80, beta=0.20 (index 3) and peak P@5/R@10 at alpha=0.85, beta=0.15 (index 2)
    ax.axvline(3, color=C_EA, linestyle=":", linewidth=1.3, alpha=0.8)
    ax.text(3.08, 0.675, "Default v5\n(α=0.80, β=0.20)", fontsize=8.3, color=C_EA, fontweight="bold")
    ax.annotate("Puncak R@10 (0.942)\n& P@5 (0.800)", xy=(2, ent_r10[2]), xytext=(1.1, 0.965),
                arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=1.1), fontsize=8.2, color=C_TEAL, fontweight="bold")

    for i in (0, 2, 3, 5, 7):
        ax.text(x[i], ent_map[i] - 0.025, f"{ent_map[i]:.3f}", ha="center", va="top", fontsize=7.8, color=C_EA, fontweight="bold")

    style_ax(ax, "y")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=8.5)
    ax.set_ylim(0.65, 1.01)
    ax.set_ylabel("Skor Metrik")
    ax.set_xlabel("Kombinasi Bobot Hybrid (S_final = α·S_text + β·S_entity)")
    ax.set_title("Analisis Sensitivitas Bobot (α, β) pada Ground Truth Manusia (Q1–Q8)", loc="left", color=C_INK, pad=12)
    ax.legend(loc="lower right", frameon=True, facecolor="#FFFFFF", edgecolor=C_GRID, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "03_alpha_beta_sensitivity.png", dpi=300)
    plt.close(fig)


def chart_4_cohens_kappa() -> None:
    rows = read_csv("cohens_kappa_report.csv")
    overall_all = float(next(r["cohens_kappa"] for r in rows if r["scope"] == "Overall (All 16 Sheets)"))
    overall_dedup = float(next(r["cohens_kappa"] for r in rows if "BASE-first" in r["scope"]))
    per_q = [r for r in rows if r["scope"].startswith("Per-Query")]

    labels = [f"{r['query_id']} ({r['query_group']})" for r in per_q][::-1]
    kappas = [float(r["cohens_kappa"]) for r in per_q][::-1]
    pos = [float(r["observed_agreement_po"]) * 100 for r in per_q][::-1]
    colors = [C_TEAL if k >= 0.61 else (C_AMBER if k >= 0.41 else C_EA) for k in kappas]

    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=300)
    y = np.arange(len(labels))
    bars = ax.barh(y, kappas, height=0.56, color=colors, zorder=3)

    # Landis & Koch threshold lines + overall reference line
    ax.axvline(0.60, color="#71717A", linestyle="--", linewidth=1.0, zorder=2)
    ax.axvline(0.80, color=C_TEAL, linestyle="--", linewidth=1.0, zorder=2)
    ax.axvline(overall_all, color=C_BASE, linestyle="-", linewidth=1.8, zorder=4,
               label=f"Overall κ = {overall_all:.4f} (N=240)  |  Dedup κ = {overall_dedup:.4f} (N=138)")

    ax.text(0.59, len(labels) - 0.18, "Substantial (0.60)", fontsize=8, color="#52525B", ha="right", va="bottom")
    ax.text(0.81, len(labels) - 0.18, "Almost Perfect (0.80)", fontsize=8, color=C_TEAL, ha="left", va="bottom")

    for bar, k, po in zip(bars, kappas, pos):
        ax.text(k + 0.015, bar.get_y() + bar.get_height() / 2, f"κ = {k:.4f}  (agree {po:.1f}%)",
                va="center", ha="left", fontsize=8.3, fontweight="bold", color=C_INK)

    style_ax(ax, "x")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(-0.6, len(labels) + 0.15)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Skor Cohen's Kappa (κ)")
    ax.set_title("Inter-Annotator Agreement (Cohen's Kappa): Judge 1 (Dwimas) vs Judge 2 (Marshall)", loc="left", color=C_INK, pad=28)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.075), frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "04_cohens_kappa_per_query.png", dpi=300)
    plt.close(fig)


def main() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_1_group_summary()
    chart_2_per_query_ap()
    chart_3_alpha_beta_sensitivity()
    chart_4_cohens_kappa()
    print("Generated 4 high-DPI PNG charts in:", CHARTS_DIR)


if __name__ == "__main__":
    main()

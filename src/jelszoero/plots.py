"""Kiértékelő ábrák mentése PNG-be (matplotlib, képernyő nélküli backend)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from . import LEVEL_COLORS, LEVEL_NAMES  # noqa: E402

ACCENT = "#2D5446"   # a felület mély zöldesszürke színe
MUTED = "#AEB8B3"
INK = "#1E2522"
INK_MUTED = "#5E6964"
GRID = "#DCE1DE"

SEQ = LinearSegmentedColormap.from_list("zold", ["#F1F4F2", "#2D5446"])

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_MUTED,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "axes.titlecolor": INK,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def plot_model_comparison(summary: dict, out: Path) -> None:
    rows = [(m["name"], m["f1"], m["name"].startswith("Alapmodell")) for m in summary["models"]]
    rows.append((summary["rule_based"]["name"], summary["rule_based"]["f1"], True))
    rows.sort(key=lambda r: r[1])
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = [MUTED if r[2] else ACCENT for r in rows]

    fig, ax = plt.subplots(figsize=(8, 0.6 * len(rows) + 1.2))
    bars = ax.barh(names, vals, color=colors, height=0.55)
    for b, v in zip(bars, vals):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", color=INK, fontsize=9)
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Makro F1-pontszám (teszthalmaz)")
    ax.set_title("Modellek összehasonlítása")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_confusion_matrices(summary: dict, out: Path) -> None:
    entries = summary["models"] + [summary["rule_based"]]
    n = len(entries)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 3.9 * rows))
    axes = np.atleast_1d(axes).ravel()
    labels = [LEVEL_NAMES[i] for i in range(3)]
    for ax, e in zip(axes, entries):
        cm = np.array(e["confusion"])
        norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
        ax.imshow(norm, cmap=SEQ, vmin=0, vmax=1)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cm[i, j]}\n{norm[i, j]:.0%}", ha="center", va="center",
                        fontsize=8, color="white" if norm[i, j] > 0.55 else INK)
        ax.set_xticks(range(3), labels)
        ax.set_yticks(range(3), labels)
        ax.set_xlabel("Előrejelzett")
        ax.set_ylabel("Valós")
        ax.set_title(e["name"], fontsize=9)
        for s in ax.spines.values():
            s.set_visible(False)
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle("Tévesztési mátrixok (confusion matrix)", fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_feature_importance(summary: dict, out: Path) -> None:
    imp = summary.get("feature_importances")
    if not imp:
        return
    top = imp[:12][::-1]
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.barh([t[0] for t in top], [t[1] for t in top], color=ACCENT, height=0.55)
    ax.set_xlabel("Fontosság (Random Forest, Gini)")
    ax.set_title("A 12 legfontosabb jellemző")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_class_distribution(summary: dict, out: Path) -> None:
    dist = summary["class_distribution"]
    names = [LEVEL_NAMES[i] for i in range(3)]
    vals = [dist.get(n, 0) for n in names]
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    bars = ax.bar(names, vals, color=[LEVEL_COLORS[i] for i in range(3)], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}".replace(",", " "),
                ha="center", va="bottom", color=INK, fontsize=9)
    ax.set_ylabel("Jelszavak száma")
    ax.set_title("Osztályeloszlás az adathalmazban")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def save_all_plots(summary: dict, reports_dir: Path) -> None:
    reports_dir = Path(reports_dir)
    plot_model_comparison(summary, reports_dir / "model_comparison.png")
    plot_confusion_matrices(summary, reports_dir / "confusion_matrices.png")
    plot_feature_importance(summary, reports_dir / "feature_importance.png")
    plot_class_distribution(summary, reports_dir / "class_distribution.png")

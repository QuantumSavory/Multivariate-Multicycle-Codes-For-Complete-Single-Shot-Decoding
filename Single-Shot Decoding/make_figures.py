#!/usr/bin/env python3
"""Publication figures for the single-shot decoding experiment.

Figure 1 (single_shot_main.pdf/.png), two panels, double-column width:
  a, b  X- and Z-basis memory: logical error rate per round vs p after N noisy rounds
  Colour/marker = code. Solid line, filled marker: single stage with the metacheck rows
  [[H, I], [0, M]]; dashed line, open marker: single stage on [H, I] (the only option when the code
  has no metachecks in that sector).
  Error bars: Wilson 95% intervals. Points without failures, and saturated points with a
  failure probability P_L >= 0.9 over the whole run, are not drawn.

Figure 2 (single_shot_decoders.pdf/.png): the decoder comparison for one code, as in
  Higgott & Breuckmann Fig. 5: single stage with metachecks, single stage without, two-stage.

Usage:
  python3 make_figures.py --vs-p results_vs_p.csv \
      --codes "MM [[144,12,12]] W9" "TT [[135,12,6]]" "BB [[144,12,12]]" \
      --labels "MM $[[144,12,\\leq 12]]$" "TT $[[135,12,(14,6)]]$" "BB $[[144,12,12]]$" \
      --rounds 8 --decoder-code "MM [[144,12,12]] W9"
"""
import argparse, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, LogLocator

COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]   # validated: CVD-safe with marker shapes
MARKERS = ["o", "s", "^", "D"]
SATURATION = 0.9

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7, "legend.fontsize": 6,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
    "lines.linewidth": 1.0, "lines.markersize": 3.5, "errorbar.capsize": 1.5,
    "legend.frameon": False, "savefig.dpi": 600, "pdf.fonttype": 42,
})


def load(path):
    return list(csv.DictReader(open(path))) if path else []


def pick(rows, code, sector, variant, key, val):
    pts = []
    for r in rows:
        if r["code"] == code and r["sector"] == sector and r["variant"] == variant and abs(float(r[key]) - val) < 1e-12:
            pts.append(r)
    return pts


def best_variant(rows, code, sector):
    vs = {r["variant"] for r in rows if r["code"] == code and r["sector"] == sector}
    return "meta" if "meta" in vs else ("nometa" if "nometa" in vs else None)


def draw(ax, pts, xkey, color, marker, filled, ls="-", label=None):
    # drop points without failures, and saturated points (P_L >= 0.9), where the logical state is
    # essentially random and the per-round conversion is meaningless
    pts = [r for r in pts if int(r["failures"]) > 0 and r["p_L_round"] not in ("nan", "")
           and float(r["P_L"]) < SATURATION]
    if not pts:
        return
    pts.sort(key=lambda r: float(r[xkey]))
    x = np.array([float(r[xkey]) for r in pts])
    y = np.array([float(r["p_L_round"]) for r in pts])
    lo = np.array([float(r["p_L_round_lo"]) for r in pts])
    hi = np.array([float(r["p_L_round_hi"]) if r["p_L_round_hi"] not in ("nan", "") else 1.0 for r in pts])
    ax.errorbar(x, y, yerr=[y - lo, hi - y], color=color, ls=ls, marker=marker,
                mfc=color if filled else "white", mec=color, mew=0.8, elinewidth=0.6, label=label)


PANEL_ASPECT = 0.8   # height / width of each panel, as the 10 x 8 in figures of the paper


def p_axis(ax):
    ax.set_box_aspect(PANEL_ASPECT)
    # same convention as the other figures of the paper: log axis labelled in powers of ten
    ax.set_xscale("log")
    ax.set_xlim(2e-3, 1e-1)
    ax.xaxis.set_major_locator(LogLocator(base=10, numticks=10))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=10))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_locator(LogLocator(base=10, numticks=10))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=10))
    ax.yaxis.set_minor_formatter(NullFormatter())


def diag(ax):
    xs = np.logspace(-3, -1, 50)
    ax.plot(xs, xs, color="0.55", lw=0.7, ls=(0, (3, 2)), zorder=0)


def panel_label(ax, s):
    ax.text(-0.2, 1.02, s, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom")


VARIANT_STYLE = {  # decoder -> (filled marker, line style, x offset factor so error bars do not overlap)
    "meta": (True, "-", 0.985),
    "nometa": (False, (0, (3.5, 1.8)), 1.015),
}


def n_axis(ax):
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator([1, 2, 4, 8, 16, 32, 64, 128]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_locator(LogLocator(base=10, numticks=10))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=10))
    ax.yaxis.set_minor_formatter(NullFormatter())


def draw_variants(ax, rows, code, sector, xkey, key, val, color, marker):
    for v, (filled, ls, dx) in VARIANT_STYLE.items():
        pts = pick(rows, code, sector, v, key, val)
        if not pts:
            continue
        pts = [dict(r, **{xkey: str(float(r[xkey]) * dx)}) for r in pts]
        draw(ax, pts, xkey, color, marker, filled, ls=ls)


def fig_main(a):
    """1 x 2: X- and Z-basis memory, logical error rate per round vs p after N noisy rounds."""
    rows_p = load(a.vs_p)
    fig, axs = plt.subplots(1, 2, figsize=(7.1, 3.55), sharey=True)
    for col, (sector, tag) in enumerate([("X", "a"), ("Z", "b")]):
        ax = axs[col]
        for i, code in enumerate(a.codes):
            draw_variants(ax, rows_p, code, sector, "p", "rounds", a.rounds, COLORS[i], MARKERS[i])
        diag(ax)
        ax.set_yscale("log"); ax.set_ylim(1e-7, 1)
        p_axis(ax)
        ax.set_xlabel(r"Physical Error Rate $p$")
        ax.set_title(f"({tag}) ${sector}$ memory experiment", loc="left", pad=3)
    axs[0].set_ylabel(r"Logical Error Rate per Round $p_L$")
    handles = [Line2D([], [], color=COLORS[i], marker=MARKERS[i], ls="-", mfc=COLORS[i], label=l)
               for i, l in enumerate(a.labels)]
    handles += [Line2D([], [], color="0.25", marker="o", mfc="0.25", ls="-", label="with metachecks"),
                Line2D([], [], color="0.25", marker="o", mfc="white", ls=(0, (3.5, 1.8)), label="without metachecks"),
                Line2D([], [], color="0.55", lw=0.7, ls=(0, (3, 2)), label="$p_L = p$")]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), bbox_to_anchor=(0.5, -0.005),
               handlelength=2.6, columnspacing=1.4)
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=0.8)
    for ext in ("pdf", "png"):
        fig.savefig(f"{a.out_prefix}single_shot_main.{ext}", bbox_inches="tight")
    print("wrote", f"{a.out_prefix}single_shot_main.pdf/.png")


def fig_decoders(a):
    rows = load(a.vs_p)
    code = a.decoder_code
    fig, axs = plt.subplots(1, 2, figsize=(7.1, 3.55), sharey=True)
    spec = [("meta", "single stage, with metachecks", COLORS[0], "o"),
            ("nometa", "single stage, without metachecks", COLORS[1], "s"),
            ("twostage", "two-stage", COLORS[2], "^")]
    for ax, sector in zip(axs, ["X", "Z"]):
        for v, lab, c, mk in spec:
            draw(ax, pick(rows, code, sector, v, "rounds", a.rounds), "p", c, mk, True, label=lab)
        diag(ax)
        ax.set_yscale("log"); ax.set_ylim(1e-7, 1)
        p_axis(ax)
        ax.set_xlabel(r"Physical Error Rate $p$")
        ax.set_title(f"({'a' if sector == 'X' else 'b'}) ${sector}$ memory experiment", loc="left", pad=3)
    axs[0].set_ylabel(r"Logical Error Rate per Round $p_L$")
    h, l = axs[0].get_legend_handles_labels()
    h.append(Line2D([], [], color="0.55", lw=0.7, ls=(0, (3, 2)))); l.append("$p_L = p$")
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.01), columnspacing=1.2)
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=0.8)
    for ext in ("pdf", "png"):
        fig.savefig(f"{a.out_prefix}single_shot_decoders.{ext}", bbox_inches="tight")
    print("wrote", f"{a.out_prefix}single_shot_decoders.pdf/.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vs-p", required=True)
    ap.add_argument("--codes", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--decoder-code")
    ap.add_argument("--out-prefix", default="")
    a = ap.parse_args()
    assert len(a.codes) == len(a.labels)
    fig_main(a)
    if a.decoder_code:
        fig_decoders(a)

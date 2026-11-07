#!/usr/bin/env python3
"""Redraw the two-panel overlapping-window (OWD) figures (Figs. 9 and 10) from the archived data.

    python3 plot_plateau_xz.py Figure09 15      # writes Figure09/figures/plateau_xz_T15_reconstructed.{png,pdf}
    python3 plot_plateau_xz.py Figure10 10      # writes Figure10/figures/plateau_xz_T10_reconstructed.{png,pdf}

Input: <folder>/results/plateau_{X,Z}_T<T>.csv (Sinter CSV, one row per batch). Rows are summed per
code and window size w. The per-round logical error rate uses the convention of the paper's memory
experiments,
    p_L = (1 - (1 - 2 P_L)^(1/T)) / 2            for P_L <= 1/2,
    p_L = 1 - (1 - (2 P_L - 1)^(1/T)) / 2        for P_L >  1/2,
with T the number of noisy rounds. Error bars are Wilson 95% intervals of P_L mapped through the same
function. (The plateau_summary_*.txt files use p_L = 1 - (1 - P_L)^(1/T) instead; the two agree when
P_L is small and differ only at w = 1, where nearly every shot fails.)

This script reproduces the content of the published figures (plateau_xz_T15moreshots.png and
circ_plateau_xz_T101.png, archived next to it); the original plotting script was not preserved,
so styling differs.
"""
import csv, json, math, os, sys, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def per_round(P, T):
    P = min(max(P, 0.0), 1.0)
    if P <= 0.5:
        return 0.5 * (1 - (1 - 2 * P) ** (1 / T))
    return 1 - 0.5 * (1 - (2 * P - 1) ** (1 / T))

def wilson(e, s, z=1.96):
    if s == 0:
        return 0.0, 1.0
    ph = e / s
    den = 1 + z * z / s
    c = (ph + z * z / (2 * s)) / den
    h = z * math.sqrt(ph * (1 - ph) / s + z * z / (4 * s * s)) / den
    return max(0.0, c - h), min(1.0, c + h)

def load(path):
    agg = collections.defaultdict(lambda: [0, 0])
    meta = {}
    for r in csv.DictReader(open(path), skipinitialspace=True):
        m = json.loads(r["json_metadata"])
        key = (m["code_name"], int(m["window_size"]))
        agg[key][0] += int(r["shots"])
        agg[key][1] += int(r["errors"])
        meta[m["code_name"]] = m
    return agg, meta

def main():
    folder, T = sys.argv[1], int(sys.argv[2])
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(here, folder)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    p_phys = None
    for ax, basis in zip(axs, "XZ"):
        agg, meta = load(os.path.join(base, "results", f"plateau_{basis}_T{T}.csv"))
        codes = sorted({c for c, _ in agg})
        for code in codes:
            ws = sorted(w for c, w in agg if c == code)
            xs, ys, lo, hi = [], [], [], []
            for w in ws:
                s, e = agg[(code, w)]
                if e == 0:
                    continue
                a, b = wilson(e, s)
                y = per_round(e / s, T)
                xs.append(w); ys.append(y)
                lo.append(y - per_round(a, T)); hi.append(per_round(b, T) - y)
            ax.errorbar(xs, ys, yerr=[lo, hi], marker="o", ms=3, capsize=2, label=code)
            p_phys = meta[code]["p"]
        ax.axhline(p_phys, color="0.5", ls="--", lw=0.8, label=f"$p = {p_phys:g}$")
        ax.set_yscale("log")
        ax.set_xlabel("window size $w$")
        ax.set_title(f"{basis} memory, T = {T}, commit c = 1")
        ax.grid(True, which="both", alpha=0.3)
    axs[0].set_ylabel("logical error rate per round $p_L$")
    axs[1].legend(fontsize=7)
    os.makedirs(os.path.join(base, "figures"), exist_ok=True)
    for ext in ("png", "pdf"):
        out = os.path.join(base, "figures", f"plateau_xz_T{T}_reconstructed.{ext}")
        fig.savefig(out, dpi=200, bbox_inches="tight")
        print("wrote", out)

if __name__ == "__main__":
    main()

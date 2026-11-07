# Figure 9: overlapping-window decoding, phenomenological noise

Per-round logical error rate versus window size `w` for overlapping-window decoding (OWD) at
`p = 0.01`, with `T = 15` noisy rounds and commit size `c = 1`, in the X and Z memory experiments.
Codes: AMC [[180,6,12]], BB [[144,12,12]], MM [[144,12,12]] (weight 9), MM [[486,24,12]], TT [[135,12,6]].
Each window is decoded with min-sum BP (at most 1000 iterations) followed by OSD of order 0
(see the header of `results/plateau_summary_*.txt`). Runs of 17 May 2026 (`logs/`).

| Path | Content |
|---|---|
| `results/plateau_{X,Z}_T15.csv` | Raw Sinter statistics (one row per batch; sum per code and window size). |
| `results/plateau_summary_{X,Z}_T15.txt` | Per-window totals and per-round rates. |
| `figures/plateau_xz_T15moreshots.png` | Fig. 9 exactly as published in the paper. |
| `figures/plateau_xz_T15_reconstructed.{png,pdf}` | The same data redrawn by `../plot_plateau_xz.py Figure09 15`. |
| `figures/plateau_{X,Z}_T15.png` | Single-basis plots made at run time. |
| `logs/` | Run logs. |

**Per-round normalization.** The published figure (and the reconstruction) use the paper's convention
`p_L = (1 - (1 - 2 P_L)^(1/T)) / 2`. The summary files use `p_L = 1 - (1 - P_L)^(1/T)`. The two agree
for small `P_L` and differ only at `w = 1`, where nearly every shot fails (for MM [[144,12,12]],
X basis: 0.092 versus 0.042).

**Stopping rule.** Not stored in the logs. The archived counts are consistent with sampling until
about 100 failures, with at most 10^7 shots per point (AMC at large `w`).

The original two-panel plotting script was not preserved; `../plot_plateau_xz.py` reproduces the
plotted values but not the styling.

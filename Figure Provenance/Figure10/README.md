# Figure 10: overlapping-window decoding, circuit-level noise

Per-round logical error rate versus window size `w` for overlapping-window decoding (OWD) at
`p = 0.001`, with `T = 10` noisy rounds and commit size `c = 1`, in the X and Z memory experiments.
Codes: BB [[144,12,12]], MM [[486,24,12]] and TT [[72,6,6]] (a different TT code from Fig. 9).
Decoder: min-sum BP (at most 1000 iterations) followed by OSD of order 0. Runs of 29 April 2026 (`logs/`).

| Path | Content |
|---|---|
| `results/plateau_{X,Z}_T10.csv` | Raw Sinter statistics (one row per batch; sum per code and window size). |
| `results/plateau_summary_{X,Z}_T10.txt` | Per-window totals and per-round rates. |
| `figures/circ_plateau_xz_T101.png` | Fig. 10 exactly as published in the paper. |
| `figures/plateau_xz_T10_reconstructed.{png,pdf}` | The same data redrawn by `../plot_plateau_xz.py Figure10 10`. |
| `figures/plateau_{X,Z}_T10.png` | Single-basis plots made at run time. |
| `logs/` | Run logs. |

**Stopping rule.** Not stored in the logs. Every archived point with `w >= 2` contains exactly 50,000 shots. At `w = 2` the MM code has only 6 (X) and 5 (Z)
failures, hence the wide confidence bands. At `w = 1` every code fails in most shots
(MM 100%, BB and TT about 80%).

The per-round normalization is the same as for Fig. 9 (see `../Figure09/README.md`).

# Figures 13 and 14: left-right (LRC) versus default circuits, weight-6 MM codes

Circuit-level X and Z memory experiments (Appendix C of the paper) comparing the left-right
circuit (LRC) schedule with the default coloration schedule for three codes:

| Name in the files | Matrices | Code parameters | Distance evidence |
|---|---|---|---|
| `BB_144_12_12` | `../MM_QECC_Database/BB_QECC_144_12_12.h5` | BB [[144,12,12]] | literature (gross code) |
| `MM_144_6_8_W6` | `../MM_QECC_Database/MM_QECC_144_6_8_W6.h5` | MM [[144,6,(8,8)]] | same row spaces as `table2_row002`, certified (8,8) by the connected-cluster campaign |
| `MM_216_6_12_W6` | `../MM_QECC_Database/MM_QECC_216_6_12_W6.h5` | MM [[216,6,(≤6,≤6)]] | weight-6 logical operators in both sectors, see below |

## Correction: the distance of `MM_216_6_12_W6` is 6, not 12

The run logs, summaries and figure legends label this code `MM [[216,6,12]]`, and the runs use
`T = 24` rounds (`2d` with `d = 12`). That value was never verified. The archive contains nontrivial
logical operators of weight 6 in both sectors:

* `MM_216_6_W6_weight6_witnesses.toml`: the two operators (one-based supports).
* `verify_216_witnesses.py`: checks that the checks measured in the archived circuit
  (`lr_cache/MM_216_6_12_W6/output/circuits/*_p0.0001_r24.stim`) have the same row spaces as the
  HDF5 matrices, and that each operator has zero syndrome and lies outside the stabilizer row space
  on both. Run `python3 verify_216_witnesses.py` (needs `numpy`, `h5py`).

So `d_X ≤ 6` and `d_Z ≤ 6`. An exact integer-programming search over all six logical classes
(SciPy/HiGHS) found no lighter nontrivial operator, giving `d_X = d_Z = 6`; this lower bound has not
yet been reproduced with the connected-cluster runner of `Distance Audit/connected_cluster/`.

This code is a different instance from the [[216,6]] entry `table2_row004` of Table II
(see `Distance Audit/connected_cluster/match_simulation_matrices.csv`). The label `12` in the files
below is the value used to set the number of rounds; the sampled data themselves are unaffected.
The pseudo-thresholds in `results/summary_*` remain valid as measured.

## Contents

| Path | Content |
|---|---|
| `results/results_{X,Z}_tesseract-custom_both_threshold.csv` | Raw Sinter statistics. |
| `results/summary_{X,Z}_tesseract-custom_both_threshold.txt` | Pseudo-thresholds per code and schedule. |
| `figures/threshold_{X,Z}_tesseract-custom_both_threshold.png` | Figures 13 (X) and 14 (Z). |
| `lr_cache/` | LRC split, colourings, CNOT orders and the Stim circuits for each code. |
| `logs/` | Run logs (6 May 2026). |
| `inspect/` | Circuit inspection output. |

Circuit resources of these schedules are reported in Table XIV of the paper.

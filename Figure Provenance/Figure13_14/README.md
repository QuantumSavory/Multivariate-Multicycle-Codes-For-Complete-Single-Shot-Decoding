# Figures 13 and 14: left-right (LRC) versus default circuits, weight-6 MM codes

Circuit-level X and Z memory experiments (Appendix C of the paper) comparing the left-right
circuit (LRC) schedule with the default coloration schedule for three codes:

| Name in the files | Matrices | Code parameters | Distance evidence |
|---|---|---|---|
| `BB_144_12_12` | `../MM_QECC_Database/BB_QECC_144_12_12.h5` | BB [[144,12,12]] | literature (gross code) |
| `MM_144_6_8_W6` | `../MM_QECC_Database/MM_QECC_144_6_8_W6.h5` | MM [[144,6,(8,8)]] | same row spaces as `table2_row002`, certified (8,8) by the connected-cluster campaign |
| `MM_216_6_12_W6` | `../MM_QECC_Database/MM_QECC_216_6_12_W6.h5` | MM [[216,6,6]] | exhaustive exclusion through weight 5 and a weight-6 logical in each sector |

## Correction: the distance of `MM_216_6_12_W6` is 6, not 12

The historical filename and PNG legends retain the original distance label of 12. The simulation used 24 noisy rounds. The corrected submission figures identify this code as MM [[216,6]], check weight 6. Only the legend text changed; the plotted data and the round count are unchanged.

The [Unity verification archive](MM_216_6_W6_exact_distance_Unity.zip) establishes **dX = dZ = 6** for this instance. In all 24 rounds of the archived LRC circuit at p = 0.0001, the measured X and Z checks matched those in the HDF5 input up to row ordering. Both binary check matrices have rank 105, giving k = 216 − 105 − 105 = 6.

In each sector the Python verifier found a weight-six operator with zero syndrome outside the stabilizer row space. To exclude lighter logicals, the exhaustive search split each candidate support of weight at most five into parts of sizes at most two and three. A zero-syndrome candidate must have equal syndromes on its two parts. The search checked these collisions for stabilizer membership. Both sectors passed. This exclusion was performed in Python; the dist-m4ri attempt did not complete.

To reproduce from the archive (Python 3.10+ with h5py):

```bash
unzip MM_216_6_W6_exact_distance_Unity.zip
cd mm216_verify
python3 verify.py
cd cc_216_W6_20261107T005259Z
python3 exclude_below_six.py
```

The original output is in `exclude_below_six.log`. The Unity witnesses use zero-based qubit indices. The separate `MM_216_6_W6_weight6_witnesses.toml` lists another pair of witnesses with one-based indices; `verify_216_witnesses.py` checks those upper bounds.

This code is a different instance from the [[216,6]] entry `table2_row004` of Table II
(see `Distance Audit/connected_cluster/match_simulation_matrices.csv`). The label `12` in the files
below is the value used to set the number of rounds; the sampled data themselves are unaffected.
The pseudo-thresholds in `results/summary_*` remain valid as measured.

## Contents

| Path | Content |
|---|---|
| `results/results_{X,Z}_tesseract-custom_both_threshold.csv` | Raw Sinter statistics. |
| `results/summary_{X,Z}_tesseract-custom_both_threshold.txt` | Pseudo-thresholds per code and schedule. |
| `figures/threshold_{X,Z}_tesseract-custom_both_threshold.png` | Historical plots with the original distance label. |
| `figures/LRCXBasisweight6circuitlevel.pdf`, `figures/LRCZBasisweight6circuitlevel.pdf` | Corrected submission figures (X and Z, respectively). |
| `lr_cache/` | LRC split, colourings, CNOT orders and the Stim circuits for each code. |
| `logs/` | Run logs (6 May 2026). |
| `inspect/` | Circuit inspection output. |

Circuit resources of these schedules are reported in Table XIV of the paper.

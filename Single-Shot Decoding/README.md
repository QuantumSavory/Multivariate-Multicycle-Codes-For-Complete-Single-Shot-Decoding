# Single-Shot Decoding

Data and scripts for the single-shot decoding experiment of the paper
*Multivariate Multicycle Codes for Complete Single-Shot Decoding*:
Sec. VII 3 (Fig. 6) and Appendix G (Fig. 18).

Every round is decoded on its own with the single-stage decoder of Higgott and Breuckmann
[PRX Quantum 4, 020332 (2023)]. After each noisy round, BP+OSD decodes the data errors and the
syndrome errors together from the syndrome `s` alone, using the check matrix
`[[H, I], [0, M]]` with right-hand side `(s, M s)`, where `M` is the metacheck matrix (`M H = 0`).
The correction is applied immediately. After `N = 8` noisy rounds, one perfect round
(a transversal readout) is decoded with `H` alone, and the shot fails if the remaining error is a
nontrivial logical operator. The logical error rate per round is `p_L = 1 - (1 - P_L)^(1/N)`.

## Codes

All check and metacheck matrices are exported directly from QuantumClifford.jl
(`MultivariateMulticycle`, `parity_matrix_x/z`, `metacheck_matrix_x/z`).

| Name in the files     | Code in the paper        | Metachecks  | Distances (sQetch, upper bounds) |
|-----------------------|--------------------------|-------------|----------------------------------|
| `MM [[144,12,12]] W9` | MM [[144,12,(≤12,≤12)]]  | M_X and M_Z | d_X ≤ 12, d_Z ≤ 12               |
| `TT [[135,12,6]]`     | TT [[135,12,(14,6)]]     | M_Z only    | d_X ≤ 14, d_Z ≤ 6                |
| `BB [[144,12,12]]`    | BB [[144,12,12]]         | none        | d_X ≤ 12, d_Z ≤ 12               |

## Files

| File | Content |
|------|---------|
| `export_from_quantumclifford.jl` | Builds the three codes with QuantumClifford.jl and writes their check and metacheck matrices to `qc_matrices/`, checking `M H = 0`. |
| `qc_matrices/*.mtx` | The exported matrices (Matrix Market format): `HX`, `HZ`, and `MX`, `MZ` where they exist. |
| `codes_qc.json` | Which matrices belong to which code. |
| `single_shot_metachecks.py` | The simulation: single-stage decoder with (`meta`) and without (`nometa`) the metacheck rows, and the two-stage decoder (`twostage`). Resumable. |
| `run_single_shot_qc.sh` | Runs every point of Figs. 6 and 18 and makes the figures. |
| `make_figures.py` | Makes the two figures from `results_qc.csv`. |
| `results_qc.csv` | Results: one row per code, memory basis (`sector`), decoder (`variant`) and `p`, with shots, failures, `P_L`, `p_L` per round and Wilson 95% intervals. |
| `run_qc.log` | Log of the run that produced `results_qc.csv`. |
| `qc_single_shot_main.pdf/.png` | Fig. 6 of the paper. |
| `qc_single_shot_decoders.pdf/.png` | Fig. 18 of the paper. |
| `verify_distances_sqetch.jl` | Distance check of the exported matrices with sQetch (100 million trials per sector, sketch dimension 64). |
| `distances_sqetch.csv` | Its output. |

## Settings

* Phenomenological noise: in each round every data qubit gets an `X` (Z memory) or `Z` (X memory) error with probability `p`, and every syndrome bit is flipped with probability `p`.
* `N = 8` noisy rounds followed by one perfect round.
* 13 values of `p`: 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05.
* At each `p`: sampling stops at 1000 failures or 2,000,000 shots. Shots are taken in batches of 2000 per worker (48,000 with 24 workers), so points at large `p` end with more than 1000 failures.
* Decoder (`ldpc` package, `BpOsdDecoder`): min-sum BP with scaling factor 0.625 and at most 30 iterations, followed by exhaustive OSD (`OSD_E`) of order 10.
* Error bars: Wilson 95% intervals.

## Reproducing

```bash
julia export_from_quantumclifford.jl            # only if qc_matrices/ is missing (needs QuantumClifford.jl and Oscar)
WORKERS=24 bash run_single_shot_qc.sh 2>&1 | tee -a run_qc.log
```

The run is resumable: finished points in `results_qc.csv` are skipped. With 24 cores it takes
several hours. To only redraw the figures from the stored results:

```bash
python3 make_figures.py --vs-p results_qc.csv \
    --codes "MM [[144,12,12]] W9" "TT [[135,12,6]]" "BB [[144,12,12]]" \
    --labels "MM [[144,12,≤12]]" "TT [[135,12,(14,6)]]" "BB [[144,12,12]]" \
    --rounds 8 --decoder-code "MM [[144,12,12]] W9" --out-prefix qc_
```

Python requirements: `numpy`, `scipy`, `matplotlib`, `ldpc` (tested with 2.4.1), Python 3.13.

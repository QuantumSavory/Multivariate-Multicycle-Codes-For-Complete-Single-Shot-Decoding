# Connected-cluster addendum: the three Table I MM codes without a certified counterpart

`../connected_cluster/match_simulation_matrices.py` shows that five MM codes of Table I
([[96,44]], [[216,12]], [[486,24]], [[486,66]], [[576,64]]) and the MM [[144,12]] code of the
simulations have exactly the same X- and Z-check row spaces as instances whose distances the
connected-cluster campaign certified. The remaining three MM codes of Table I have no such
counterpart, and their Table I distances are still the upper bounds of the original search,
with no saved logical operator:

| id | matrices | Table I entry |
|---|---|---|
| `TabI_MM_96_12_4_W12` | `QECCs/MM/MM_96_12_4_W12` | [[96,12,(<=4,<=4)]], weight 12 |
| `TabI_MM_96_12_8` | `QECCs/MM/MM_96_12_8` | [[96,12,(<=8,<=8)]], weights 12-16 |
| `TabI_MM_144_40_4` | `QECCs/MM/MM_144_40_4` | [[144,40,(<=4,<=4)]], weight 12 |

This folder runs the same `run_cc.py` (unchanged copy) on these matrices. No witness is bundled,
so the runner searches weight 1, 2, ... up to the Table I value; a codeword found by dist-m4ri at
weight w, after all smaller weights were excluded, makes that sector EXACT with distance w. If
the search excludes every weight up to the Table I value, the status is LOWER_BOUND_ONLY and the
Table I value is wrong (the distance is larger).

```bash
cd "Distance Audit/connected_cluster_tableI"
python3 run_cc.py --dry-run
bash run_campaign.sh --jobs 4 --threads 1 --seconds 900 --session-seconds 25200
# or: sbatch submit_cc.sbatch
```

Results go to `cc_results/` with the same layout as `../connected_cluster/cc_results/`.

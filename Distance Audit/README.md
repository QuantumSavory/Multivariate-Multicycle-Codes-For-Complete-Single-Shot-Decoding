# Distance audit for the explicit MM code tables

This folder contains everything used to recompute and verify the code parameters reported in
Tables II–XI of *Multivariate Multicycle Codes* (revised version): the registry of printed
construction inputs, the audit code, the raw search outputs, and the logical operators that
back the reported distance bounds.

**All distances are upper bounds.** A reported entry `[[n, k, (<= dX, <= dZ)]]` means that
nontrivial logical operators of those weights were found. No lower bounds or exact distances
are claimed.

## How the reported numbers were obtained

1. **Construction and structure** (`code/audit_mm.jl`). Every table entry is rebuilt from its
   printed polynomials and moduli with `MultivariateMulticycle` in QuantumClifford.jl over
   Oscar. The audit checks CSS commutation and the metacheck identities over GF(2), and computes
   `k = n - rank(HX) - rank(HZ)` by exact GF(2) elimination. An independent pure-Python
   reconstruction (`code/independent_audit.py`) agrees on n, k, ranks and check weights for all
   437 registered instances.
2. **sQetch** (GPU randomized information-set search, Bhardwaj et al., arXiv:2607.28795,
   appendix). 10^8 trials per sector, sketch dimension 64, no early stopping, seed
   1234 + registry index (`results/sqetch_100M`). The 38 rows whose bound exceeded the
   originally published value in at least one sector were rerun with 1.5x10^8 trials and seed
   5678 + registry index (`results/sqetch_150M_rerun38`).
3. **dist-m4ri cross-check** (random-window algorithm, version 0.9.0, commit `1f46277`).
   60 s per sector, one fixed seed per instance, for all 368 rows kept in the tables
   (`code/run_distm4ri.sh`, `results/distm4ri`). Every logical operator it reports is saved.
4. **Reported bound** = the smaller, per sector, of the sQetch result(s), the lightest verified
   dist-m4ri operator, and any verified referee witness. The cross-check lowered at least one
   sector bound in 58 of the 368 rows (for example `[[864,12]]`: sQetch gave
   `(<= 18, <= 42)`, while weight-18 Z logical operators exist).

## Files

| Path | Contents |
|---|---|
| `code/instances.toml`, `code/instances.json` | Registry: printed n, k, distances, variables, moduli, polynomials and exponent supports for every audited entry |
| `code/audit_mm.jl` | Construction, structural checks, logical-basis witnesses and sQetch driver (`run_audit`) |
| `code/sqetch_wrapper_qt.jl` | Julia wrapper around sQetch, used unchanged for both runs |
| `code/independent_audit.py`, `code/independent_reference.toml`, `code/independent_structural_audit.csv` | Independent Python reconstruction and its reference values |
| `code/run_distm4ri.sh` | Builds dist-m4ri and runs the cross-check |
| `code/rerun_38_sqetch_150M.jl` | The 150M-trial sQetch rerun |
| `code/verify_witnesses.py` | Checks every saved operator against the saved matrices (numpy only) |
| `code/verify_witnesses.jl` | The same check, rebuilding the codes from the polynomials with QuantumClifford |
| `results/sqetch_100M/` | `summary.csv`, `environment.toml` (versions), Julia Project/Manifest, and per entry: `result.toml`, `HX.mtx`, `HZ.mtx`, logical-basis witnesses |
| `results/sqetch_150M_rerun38/` | Summary and per-entry results of the rerun |
| `results/distm4ri/results_cluster_60s.csv` | Lightest weight found by dist-m4ri per row and sector |
| `final/distance_bounds_final.csv` | Final bound per row and sector, with each source and whether it is witnessed |
| `final/table_vs_audit_final.csv` | Every table row: printed entry, all sources, removal status, comparison with the original manuscript |
| `final/dist_m4ri_witnesses.toml` | The 736 saved logical operators (368 rows x 2 sectors) |

## Conventions

* Matrices are the QuantumClifford `HX`, `HZ` produced by `construct()` in `audit_mm.jl`,
  saved in Matrix Market format with one-based indices.
* Sector **x**: `HZ v = 0` and `v` outside the row space of `HX`.
  Sector **z**: `HX v = 0` and `v` outside the row space of `HZ`.
* Witness supports are one-based column indices into these matrices.
* Instance ids (`table7_row084`, ...) refer to the table and row order of the registry.
  Rows with `d <= 6` were removed from the tables, except three instances used in the main text.

## Reproduce

```bash
# check every reported operator (seconds; needs Python >= 3.11 and numpy)
python3 code/verify_witnesses.py final/dist_m4ri_witnesses.toml results/sqetch_100M

# same check through QuantumClifford (needs the Julia environment in results/sqetch_100M)
julia --project=<env> code/verify_witnesses.jl

# structural audit without Julia
python3 code/independent_audit.py

# sQetch search (GPU; needs a working sQetch install)
cd code && julia --project=<env> -e 'include("audit_mm.jl"); MMManuscriptAudit.run_audit(trials=100_000_000, seed=1234, outdir="audit_sqetch_100M")'

# dist-m4ri cross-check (CPU)
MATDIR=$PWD/results/sqetch_100M bash code/run_distm4ri.sh
```

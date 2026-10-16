# Prioritized MM connected-cluster distance certification

**Status (15 October 2026):** this folder now contains the completed results of running this package on the
authors' cluster in two sessions (budgets of 900 s and then 3600 s per sector, one CPU thread per sector).
`validate_certificates.py` and `validation.csv` (added afterwards) check every EXACT sector independently.
The sentence below about no searches having been performed describes the package before it was run.

This package contains 88 candidates (176 CSS sectors), the exact input matrices,
audited witness supports where available, a resumable Python runner, and a selection CSV.
No real CC searches have been performed by this package yet. Run it on your cluster.

## Run on the cluster

Upload `mm_cc_priority.zip` to `~/sqetch_work/mm_manuscript_audit/`, then:

```bash
cd ~/sqetch_work/mm_manuscript_audit
unzip mm_cc_priority.zip
cd mm_cc_priority
python3 run_cc.py --dry-run
bash run_campaign.sh --jobs 4 --threads 1 --seconds 900 --session-seconds 25200
```

Requires Python >=3.10 (standard library only) and your installed dist-m4ri 0.9.0 CLI.
The default executable is `~/distm4ri_tools/dist-m4ri/src/dist_m4ri`.
Use `--binary /absolute/path/to/dist_m4ri` if different.
`--seconds 900` is the total budget per sector per invocation, not per weight.
The campaign stops after about seven hours, leaving room within an eight-hour allocation.
Four independent sector jobs each use one CPU thread; no GPU is needed.
Run within an allocated compute session, not a login node.

Alternatively, from this directory use `sbatch submit_cc.sbatch`, adding the account or
partition required by your cluster. The script requests four CPUs and 16 GB RAM.

Run the same command next session: exact sectors are skipped and partial sectors continue
from their last completely excluded weight. An interrupted weight is restarted from scratch;
this is not an in-weight CC checkpoint. Every attempt has its own directory and logs.
An optional first pass through weight eight is `--max-weight 8`; omit that option next time
for deeper searches. Increase `--seconds` when a single weight cannot complete within 900 s.
The output directory is locked against simultaneous runners.

## Selection and identity

Source: repository commit f6743db75a1b7d795ca9adc1d8a5a54a737ed498 and
`multivariate_multicycle (20).zip`, reviewed October 15, 2026.

1. `table4_row022` ([[648,60]], search estimates 9,9) comes first.
2. Main-text candidates and explicitly identified matrices come next.
3. Remaining audited, nonzero-k instances with n < 200 follow.

The selection uses all 84 eligible entries in the independent audit registry, plus the
three exact matrix sets in the new single-shot experiment and the explicit R5 index-12
worked example. The latter has n=30, k=6 when its displayed matrices are expanded.

Matching main-text (n,k) is deliberately a conservative candidate selection, NOT proof
that two instances are the same code. All such ambiguities are marked in selection.csv.
Transfer a certificate to the manuscript only after matching its polynomials/matrices.
We retain low-bound n<200 registry rows even if they were omitted from the revised tables.
The package does not reconstruct every external literature comparator in Table I.
Unmatched main-text parameter pairs are recorded in coverage_notes.json.

The bundled matrices are authoritative for this campaign: it does not silently read or
replace matrices from your existing audit folders. Each run checks SHA-256 hashes, CSS
commutation, GF(2) ranks and k, and logical-witness validity. No existing cluster search
logs are overwritten or automatically imported. The earlier table4_row022 Z-sector
search is therefore repeated here unless you separately retain and report that certificate.

## What constitutes exactness

For sector z, use H=HX, G=HZ. For sector x, use H=HZ, G=HX.
A witness must have zero syndrome under H and lie outside rowspace(G), over GF(2).
The runner checks this independently with binary integer arithmetic.

Each CC invocation uses method=2, noscan=0, smax=0 and searches one weight w, with dmin=w.
The supplied dmin is justified only by all previous completed weight exclusions, starting
from the trivial bound 1. No randomized estimate is ever supplied as a lower bound.
The runner recognizes the explicit completed-weight log line from dist-m4ri 0.9.0.
On a successful call, a completed exclusion at weight w advances the bound to w+1.
A timeout, unfinished scan, or failed process does not advance that bound.

EXACT requires equality between this certified lower bound and the weight of an
independently verified nontrivial logical operator. Witnesses found by CC are exported
in one-based NZLIST format and independently checked too. The runner does not trust a
bare numerical upper bound or two searches agreeing as an exactness certificate.

Bundled witnesses include verified dist-m4ri supports and valid basis witnesses from the
audit. Basis witnesses can be heavier than the reported search estimate. In that case,
the initial search stops after testing the estimated weight if no exact certificate is
obtained; inspect that discrepancy. Use --ignore-estimates to continue toward the verified
witness bound if desired. CONFLICT means a witness and certified lower bound disagree:
do not use such a result in the manuscript.

## Outputs

- campaign.log: human-readable progress, including every completed sector result.
- cc_results/summary.csv: sector status, certified lower bound, verified upper bound,
  and the separate search estimate. PENDING means not attempted in the current results set.
- cc_results/<id>/<x|z>/result.json: checkpoint, matrix hashes, verified witness, proof-log references.
- cc_results/<id>/<x|z>/wNNN_<timestamp>/: exact command, stdout, stderr, exit status, and any witness.
- cc_results/environment_<timestamp>.json: executable version and hash, invocation, manifest hash.
- cc_results/errors_<timestamp>.json: any validation/processing exceptions; none are silently certified.

Statuses PARTIAL and LOWER_BOUND_ONLY are NOT exact distances. A changed executable hash
requires a new output directory to prevent silently mixing certificates across binaries.
Each checkpoint's supporting completed-weight logs are hash-checked when resuming.

To spend longer on one unfinished instance:

```bash
bash run_campaign.sh --ids table4_row022 --jobs 2 --seconds 12000
```

To archive results for review, run from the parent directory:

```bash
zip -qr mm_cc_priority_results.zip mm_cc_priority
```

## Validation performed before delivery

All 88 bundled matrix pairs passed hash, GF(2) dimension, CSS commutation, and bundled
witness checks. The runner was tested with an exhaustive small-CSS test executable for
weight checkpoints, witness-based exactness, interrupted/timeout behavior, resume skips,
and rejecting changed inputs. The real dist-m4ri executable is on your cluster; this
package does not claim to have run or certified these 88 codes locally.

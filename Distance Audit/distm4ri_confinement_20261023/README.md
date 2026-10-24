# Native dist-m4ri confinement runs

This package is a Python batch wrapper around your installed `dist_m4ri`. It contains NO custom enumeration engine. Every search is performed by that executable. No software update, compilation, or change to dist-m4ri is performed.

## Run

Use an allocation with at least four CPU cores. No GPU is needed.

```bash
cd ~/sqetch_work/mm_manuscript_audit
unzip distm4ri_confinement_20261023.zip
cd distm4ri_confinement_20261023
python3 run_distm4ri.py --dry-run
set -o pipefail
python3 -u run_distm4ri.py --threads 4 --seconds 900 \
  --session-seconds 25200 2>&1 | tee -a campaign.log
```

The default executable is `~/distm4ri_tools/dist-m4ri/src/dist_m4ri`. Override with `--binary /absolute/path/to/dist_m4ri` if necessary. The uploaded 0.9.0 source advertises all parameters used here. The wrapper saves the actual binary, its SHA-256, version and help outputs for each campaign. It does not silently install a newer version.

There are 16 sequential calls: both sectors of eight MM instances. Each call uses four threads and a 900-second native timeout. At these settings, allow roughly four hours plus overhead; individual runs may finish much sooner. The seven-hour campaign limit leaves a buffer for an eight-hour allocation.

`--ids MM_96_12_8` restricts to one instance. `--seconds 1800` increases each sector's budget, but all 16 sectors may no longer fit the campaign limit. Each invocation creates a new timestamped results directory and starts fresh; this wrapper does NOT resume within a sector or import the separate enumerator's results.

## Exact commands and meaning

The commands saved in each sector's `command.sh` use:

- `method=2`: native connected-cluster search.
- Z errors: `finH=HX`, `finG=HZ`. X errors: `finH=HZ`, `finG=HX`.
- `wmax`: the length of that MM row's historical profile.
- `smax`: the number of check rows, so no positive syndrome weight is excluded by this cap.
- `dmin=1`, `noscan=0`: start the scan at weight one. Skipping initial weights disables profile tracking in the uploaded version.
- `wmin=0`: disable this particular low-weight stopping threshold.
- `outC`: save discovered logical codewords and enable native codeword collection. Other native stopping conditions still apply; this does not guarantee all requested weights will appear.
- `debug=3`: save progress and per-weight observed-profile lines.

No `dmax`, restricted start columns, or custom recursion is used. The wrapper only checks input hashes, calls the binary, saves files, and copies reported profile lines into CSV.

## Evidence and limitations

The upstream README calls these minimum nonzero syndrome weights OBSERVED during the CC traversal:
https://github.com/QEC-pages/dist-m4ri/blob/master/README.md#confinement-profile

They are not automatically exact minima over every connected support of the same weight. Do not describe them as an exhaustive connected-error confinement bound. An exit code of zero also does not establish that every requested weight was fully searched: the native program may stop at its time limit or distance stopping condition. Preserve and inspect the raw logs.

`logical_codewords.nz` contains zero-syndrome logical operators found by the distance search. It is NOT a witness file for positive-syndrome profile entries. This wrapper cannot supply witnesses that the native binary does not export.

`observed_profiles.csv` labels printed entries OBSERVED_ONLY and absent ones NOT_REPORTED. Blank does not mean zero. The raw stdout/stderr, exact command, matrices, binary and metadata are the evidence; the CSV is a mechanical summary, not a new certificate.

The bundled matrices are unchanged copies from the eight `QECCs/MM/` directories at manuscript-repository commit `5b9ee22c1d0ddcd6813451f03d8ea8642e38d225`. `manifest.json` records exact paths and hashes. Original check rows are retained. This establishes which matrices the new campaign runs, not that every older confinement run used those matrices. The historical profile fields are reference metadata only and are not passed to dist-m4ri.

## Keep runs separate

Do not delete or overwrite the earlier `confinement_campaign_20261023` custom-enumerator output. It comes from different software and a different enumeration procedure. Do not label it dist-m4ri output. This package writes only inside its own directory.

After completion, archive this whole folder (including campaign.log and the timestamped results directory):

```bash
cd ..
zip -r distm4ri_confinement_cluster_results_20261023.zip distm4ri_confinement_20261023 \
  -x '*/__pycache__/*' '*.pyc'
```

This wrapper has been checked for syntax, manifest integrity and log parsing. No manuscript-code confinement search was run during package preparation. These eight MM runs do not validate the comparison-code rows of Table I. Manuscript and response wording must distinguish observed native profiles from exhaustive claims.

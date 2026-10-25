# Figures 4, 5, 7, 8: simulations with original Sinter plotting style

Activate your existing qecc_venv. Unpack this ZIP alongside MM_QECC_Database in qecc_suite. No GPU is used. The worker count must not exceed the allocated CPUs. Many workers can consume substantial memory; 190 workers is permitted with a 190-core allocation but is not a guarantee of proportionate speedup.

```bash
unzip mm_figures_sinter_200k_20261024.zip
cd mm_figures_sinter_200k_20261024
set -o pipefail
bash run.sh --data-path ../MM_QECC_Database --output smoke_sinter_200k \
  --smoke --workers 2 2>&1 | tee smoke_sinter_200k.log
```

After the smoke test succeeds:

```bash
bash run.sh --data-path ../MM_QECC_Database --output revision_sinter_200k \
  --workers 190 2>&1 | tee campaign.log
```

Resume after interruption (do not leave the old process running):

```bash
bash run.sh --output revision_sinter_200k --resume --workers 190 \
  2>&1 | tee -a campaign.log
```

Use a new production folder. Keep the earlier revision_run results unchanged. The new folder prevents accidental merging or replacement of the old campaign. Existing outputs cause an error unless --resume is used. Do not run two sampling processes on the same output folder.

## Automatic figures

After each group's sampling finishes, its CSV is plotted with sinter.plot_error_rate. PDF and 600-dpi PNG output is saved to revision_sinter_200k/figures/figure04, figure05, figure07 and figure08. Individual plotting records and immutable CSV snapshots are saved under plot_records/. Missing later figures simply mean their group has not yet finished. Smoke figures have a SMOKE_ prefix; unfinished statistical targets have PARTIAL_ prefixes.

Style checked against the original four archived images: 10x8 inch layout; AMC blue circles, BB orange downward triangles, MM green stars, TT red squares; clean [[n,k,d]] legend labels; upper-left legend; original two-line Tesseract memory-experiment titles; both axes 1e-4 to 1e-1; dashed p_L=p line; light grid; shaded Sinter likelihood regions. No custom Wilson plotting routine is used. TT's displayed d=6 is the minimum sector distance, not a claim that both sector distances equal six.

The plotting source and Sinter version are archived. Sinter handles per-round conversion with failure_units_per_shot_func=r. The shaded likelihood region uses highlight_max_likelihood_factor=1000. This replaces the earlier rerun script's custom normalization/uncertainty display; the manuscript formula must agree with the installed Sinter implementation. No invented simulation data are included.

## Sampling and provenance

There are 144 production tasks: four codes, both X/Z bases, both noise models, nine log-spaced probabilities 1e-4 to 1e-1. Historical round counts are fixed: MM/AMC/BB 24, TT 12. Phenomenological: at most 100,000 shots or target 1,000 failures; circuit-level: 200,000 shots or 5,000 failures. Actual stopping can exceed a target because of sampling batches. Failure is Sinter's default any-observable prediction failure.

Tesseract options match the supplied original scripts: detector beam 8, beam climbing, no revisiting detectors, merged errors, queue limit 10,000, 10 DetIndex orderings, seed 2384753. Unsupported options cause an error, not a silent change. Scheduler seed is 20261024; Sinter/Stim sampling seeds are not fixed. Installed package versions are recorded and checked on resume.

Circuit noise follows the previous package: before-round data depolarization and premeasurement flips at p in the phenomenological model; all six uploaded noise arguments at p in the circuit model. Exact arguments are in manifest.json.

Every circuit is saved, reloaded, audited, and used to derive an explicit undecomposed DEM. Sampling reloads these exact archived circuit/DEM files and verifies their hashes and Sinter task strong_id. Each task also saves resources.json, including repeated-block and interval-level details. Inputs and source snapshots are retained. Thus the new plots and extracted resources refer to the same saved circuits; this is not a claim that they match the older historical schedules.

CNOT-containing TICK intervals are literal schedule depths; check target disjointness before interpreting parallel layers. Whole-circuit counts include initialization and termination. DEPOLARIZE1 targets can represent round-start data noise or idle noise; the output preserves targets and overlaps rather than calling every one an idle location.

## Plotting only

No simulation is needed to redraw an existing completed new run:

```bash
python3 redraw.py --run-dir revision_sinter_200k
```

This writes a fresh figures_sinter_TIMESTAMP folder. The same plotting script can read the earlier revision_run directory if desired; no new sampling is necessary purely for style changes.

## Validation

Python syntax compilation passed for all scripts. The matrix loader and resource extractor already ran successfully on the user's cluster. The newly integrated workflow has not been executed in the preparation environment, where simulation dependencies are unavailable. Run the short smoke test before production.

## Export

From qecc_suite after completion:

```bash
zip -r mm_figures_sinter_200k_cluster_results.zip mm_figures_sinter_200k_20261024 \
  -x '*/__pycache__/*' '*/smoke_sinter_200k/*'
```

This is a fresh campaign, not a continuation of the earlier shot budget. The circuit-level shot and failure limits are both ten times the original 20,000/500 limits. Runtime is data-dependent and may exceed the cluster allocation; CSV progress can be resumed with this package. No guarantee of completing before the submission deadline is implied.

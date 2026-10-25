# Figures 4, 5, 7 and 8: simulation archive

This folder contains everything used to produce Figures 4, 5, 7 and 8 of the revised manuscript (phenomenological and circuit-level memory experiments for the MM [[144,12,12]], BB [[144,12,12]], AMC [[180,6,12]] and TT [[135,12,(14,6)]] codes). The campaign was run on 24 October 2026 on a computing cluster and completed all 144 tasks. Instructions for re-running or re-plotting are in `RUN_INSTRUCTIONS.md`.

## Contents

| Path | What it is |
|---|---|
| `revision_sinter_200k/inputs/` | Check matrices (HDF5). Byte-identical to the files in `Figure Provenance/MM_QECC_Database/`. |
| `revision_sinter_200k/tasks/<model>_<basis>/<code>/pXX/` | For each task: the exact Stim circuit (`circuit.stim`), its detector error model (`detector_error_model.dem`) and the extracted circuit resources (`resources.json.gz`). |
| `revision_sinter_200k/manifest.json` | All noise arguments, decoder settings, stopping rules, software versions, and SHA-256 hashes of inputs, circuits, DEMs and resource files. |
| `revision_sinter_200k/results/` | Raw Sinter statistics (CSV) and completion records. |
| `revision_sinter_200k/figures/` | Figures 4, 5, 7, 8 (PDF and 600-dpi PNG) as used in the manuscript. |
| `revision_sinter_200k/plot_records/` | Immutable CSV snapshot, plotting record and archived Sinter plotting source for each figure. |
| `rerun_figures.py`, `run.sh`, `redraw.py`, `resource_helpers.py`, `revision_sinter_200k/generator_source.py` | Sampling, plotting, resource-extraction and circuit-generation code. |
| `campaign.log.gz`, `smoke.log` | Logs of the production campaign and of the preceding smoke test. |

`resources.json` files and `campaign.log` are gzip-compressed to keep the repository small; the hashes in `manifest.json` refer to the uncompressed `resources.json` files (`gunzip -k` restores them).

## Settings

* Rounds: T = 2d, i.e. 24 for MM, BB and AMC and 12 for TT (d = 6 is TT's smaller sector distance).
* Physical error rates: nine log-spaced values from 1e-4 to 1e-1.
* Phenomenological model: data depolarization p before each round, measurement flip p. Stopping rule: 1,000 failures or 100,000 shots.
* Circuit-level model: all six noise arguments (after-CNOT, before-round data, before-measure, after-reset, idle during CNOT for active and inactive qubits) equal to p. Stopping rule: 5,000 failures or 200,000 shots.
* Circuits: `make_css_code_memory_circuit` (ldpc), one ancilla per check, X checks then Z checks, each scheduled by a minimum edge colouring.
* Decoder: Tesseract via Sinter; detector beam 8, beam climbing, no revisiting detectors, merged errors, priority-queue limit 10,000, 10 DetIndex detector orderings, seed 2384753.
* Failure: any logical observable mispredicted (Sinter default).
* Per-round rate: `sinter.plot_error_rate` with `failure_units_per_shot_func = r`, i.e. p_L = (1 - (1 - 2 P_L)^(1/T))/2 for P_L <= 1/2. Shaded bands: Sinter likelihood region, factor 1000.
* Software: Python 3.13.3, Stim 1.15.0, Sinter 1.15.0, tesseract-decoder 0.1.1.dev20260414023431, ldpc 2.4.1, NumPy 2.2.6, SciPy 1.17.1, matplotlib 3.10.8. Sinter/Stim sampling seeds are not fixed; the archived counts are the record.

## Circuit resources (per round, repeated bulk; identical for X and Z bases)

| Code | n | X ancillas | Z ancillas | (w_X, w_Z) | CNOT layers | CNOTs | Idle-noise locations | Data-noise locations |
|---|---|---|---|---|---|---|---|---|
| MM [[144,12,12]] | 144 | 96 | 96 | (9,9) | 18 | 1728 | 2592 | 144 |
| BB [[144,12,12]] | 144 | 72 | 72 | (6,6) | 12 | 864 | 1728 | 144 |
| AMC [[180,6,12]] | 180 | 120 | 120 | (6,6) | 12 | 1440 | 2160 | 180 |
| TT [[135,12,(14,6)]] | 135 | 45 | 135 | (9,6) | 15 | 1215 | 2295 | 135 |

An idle-noise location is one qubit target of a DEPOLARIZE1 channel inside a CNOT layer; CNOT targets are disjoint in every layer and never overlap these targets.

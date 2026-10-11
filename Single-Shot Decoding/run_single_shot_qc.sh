#!/bin/bash
# Single-shot decoding with explicit metachecks, with all check and metacheck matrices taken
# directly from QuantumClifford.jl (MultivariateMulticycle), see export_from_quantumclifford.jl.
#     WORKERS=24 bash run_single_shot_qc.sh 2>&1 | tee -a run_qc.log
# Resumable: finished points in results_qc.csv are skipped, so rerun the same command if cut off.
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=${WORKERS:-$(nproc)}
[ -f qc_matrices/MM_144_12_12_MX.mtx ] || julia export_from_quantumclifford.jl
PS="0.005 0.0075 0.01 0.0125 0.015 0.0175 0.02 0.025 0.03 0.035 0.04 0.045 0.05"
MAIN=("MM [[144,12,12]] W9" "TT [[135,12,6]]" "BB [[144,12,12]]")
COMMON=(--rounds 8 --max-shots 2000000 --max-failures 1000 --batch 2000 --workers "$WORKERS" --out results_qc.csv)

python3 -W ignore single_shot_metachecks.py --codes codes_qc.json --variants meta nometa --ps $PS "${COMMON[@]}"
python3 -W ignore single_shot_metachecks.py --codes codes_qc.json --only "MM [[144,12,12]] W9" --variants twostage --ps $PS "${COMMON[@]}"
python3 make_figures.py --vs-p results_qc.csv \
    --codes "${MAIN[@]}" --labels "MM [[144,12,≤12]]" "TT [[135,12,(14,6)]]" "BB [[144,12,12]]" \
    --rounds 8 --decoder-code "MM [[144,12,12]] W9" --out-prefix qc_
echo "done: results_qc.csv qc_single_shot_main.pdf qc_single_shot_decoders.pdf"

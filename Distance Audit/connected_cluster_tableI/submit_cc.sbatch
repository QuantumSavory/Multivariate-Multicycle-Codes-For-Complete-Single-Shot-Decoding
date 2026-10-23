#!/usr/bin/env bash
#SBATCH --job-name=mm-cc-exact
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --output=mm-cc-%j.log
set -euo pipefail
# Submit from this package directory. Add your cluster's account/partition if required.
cd "${SLURM_SUBMIT_DIR}"
bash run_campaign.sh --jobs 4 --threads 1 --seconds 900 --session-seconds 25200

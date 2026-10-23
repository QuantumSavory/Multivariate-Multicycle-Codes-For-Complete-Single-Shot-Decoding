#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3 -u run_cc.py "$@" 2>&1 | tee -a campaign.log

#!/usr/bin/env bash
set -euo pipefail

base="$HOME/sqetch_work/mm_manuscript_audit"
bin="$HOME/distm4ri_tools/dist-m4ri/src/dist_m4ri"
out="$base/four_codes_rw_$(date -u +%Y%m%dT%H%M%SZ)"

ids=(table3_row025 table3_row027 table4_row023 table4_row026)

# Check every input before starting.
test -x "$bin"
for id in "${ids[@]}"; do
    test -s "$base/audit_sqetch_100M/$id/HX.mtx"
    test -s "$base/audit_sqetch_100M/$id/HZ.mtx"
done

mkdir -p "$out"
sha256sum "$bin" > "$out/binary_sha256.txt"
"$bin" --help > "$out/dist_m4ri_help.txt" 2>&1
cp "$0" "$out/run_script.sh"

seed=202610160
for id in "${ids[@]}"; do
    mkdir -p "$out/$id"
    cp "$base/audit_sqetch_100M/$id/"{HX,HZ}.mtx "$out/$id/"
    sha256sum "$out/$id/"{HX,HZ}.mtx > "$out/$id/matrix_sha256.txt"

    for sector in x z; do
        seed=$((seed + 1))
        dest="$out/$id/$sector"
        mkdir -p "$dest"

        if [[ "$sector" == x ]]; then
            H="$out/$id/HZ.mtx"
            G="$out/$id/HX.mtx"
        else
            H="$out/$id/HX.mtx"
            G="$out/$id/HZ.mtx"
        fi

        cmd=("$bin" method=1 "finH=$H" "finG=$G"
             steps=100000000 timeout=1800 threads=1
             smax=0 "seed=$seed" "outC=$dest/witness.nz")

        printf '%q ' "${cmd[@]}" > "$dest/command.sh"
        printf '\n' >> "$dest/command.sh"
        date -u +%FT%TZ > "$dest/started_utc.txt"
        echo "RUN $id d${sector^^}: up to 1800 seconds"

        set +e
        "${cmd[@]}" > "$dest/stdout.txt" 2> "$dest/stderr.log"
        rc=$?
        set -e

        printf '%s\n' "$rc" > "$dest/exit_code.txt"
        date -u +%FT%TZ > "$dest/finished_utc.txt"
        echo "FINISHED $id d${sector^^}: exit=$rc"
    done
done

echo "Saved results: $out"

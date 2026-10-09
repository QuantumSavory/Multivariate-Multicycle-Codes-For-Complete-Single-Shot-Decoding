#!/bin/bash
# Cross-check the MM table distances with dist-m4ri (random-window mode, CPU only).
# Saves every logical operator it finds, so each bound can be verified independently.
#
# Usage (from the folder that contains audit_sqetch_100M/):
#     bash run_distm4ri.sh                 # defaults: 60 s per sector, all CPU cores
#     SECS=120 JOBS=8 bash run_distm4ri.sh # longer search, 8 codes in parallel
#
# Results: distm4ri_results/results.csv  and  distm4ri_results/witness/<id>_<x|z>.nz
# Re-running skips (id, sector) pairs that are already done.
set -euo pipefail

SECS=${SECS:-60}                         # wall-clock seconds per code per sector
NCPU=${NCPU:-$(nproc)}
JOBS=${JOBS:-$(( NCPU >= 8 ? NCPU / 4 : 1 ))}   # codes run in parallel
THREADS=$(( NCPU / JOBS > 0 ? NCPU / JOBS : 1 ))  # threads per dist-m4ri run
MATDIR=${MATDIR:-$PWD/audit_sqetch_100M}  # where table*_row*/HX.mtx, HZ.mtx live
TOOLS=${TOOLS:-$HOME/distm4ri_tools}
OUT=${OUT:-$PWD/distm4ri_results}
PREFIX=$TOOLS/local

[ -f "$MATDIR/table3_row026/HX.mtx" ] || { echo "Cannot find matrices under $MATDIR (set MATDIR=...)"; exit 1; }
mkdir -p "$TOOLS" "$OUT/witness" "$OUT/log"

# ---------------------------------------------------------------- 1. build m4ri (once)
if [ ! -f "$PREFIX/include/m4ri/m4ri.h" ]; then
  echo ">> building m4ri into $PREFIX"
  command -v autoreconf >/dev/null || { echo "autoreconf not found: try 'module load autoconf automake libtool' (or ask me for a conda alternative)"; exit 1; }
  cd "$TOOLS"; [ -d m4ri ] || git clone -q https://github.com/malb/m4ri.git
  cd m4ri; autoreconf --install >/dev/null 2>&1
  ./configure --prefix="$PREFIX" --enable-openmp=no >"$TOOLS/build.log" 2>&1 || { tail -20 "$TOOLS/build.log"; exit 1; }
  { make -j"$NCPU" && make install; } >>"$TOOLS/build.log" 2>&1 || { tail -20 "$TOOLS/build.log"; exit 1; }
  cd - >/dev/null
fi

# ---------------------------------------------------------------- 2. build dist-m4ri (once, pinned commit)
BIN=$TOOLS/dist-m4ri/src/dist_m4ri
if [ ! -x "$BIN" ]; then
  echo ">> building dist-m4ri"
  cd "$TOOLS"; [ -d dist-m4ri ] || git clone -q https://github.com/QEC-pages/dist-m4ri.git
  cd dist-m4ri; git checkout -q 1f46277bbf453f2585486ac8862344cc3d667a77
  cd src; make dist_m4ri CC="gcc -I$PREFIX/include -L$PREFIX/lib -Wl,-rpath,$PREFIX/lib" >>"$TOOLS/build.log" 2>&1 \
    || { tail -20 "$TOOLS/build.log"; exit 1; }
  cd - >/dev/null
fi
"$BIN" --version

# ---------------------------------------------------------------- 3. the rows still in Tables II-XI
cat > "$OUT/ids.txt" <<'IDS'
table2_row001
table2_row002
table2_row004
table2_row005
table2_row006
table2_row007
table2_row008
table2_row009
table2_row010
table2_row011
table2_row012
table2_row015
table2_row016
table2_row017
table2_row018
table2_row019
table2_row020
table2_row021
table2_row022
table2_row023
table2_row024
table2_row025
table2_row029
table2_row030
table2_row031
table2_row032
table2_row033
table2_row034
table2_row035
table2_row036
table2_row037
table2_row038
table2_row039
table2_row040
table2_row041
table2_row042
table2_row043
table2_row046
table2_row047
table2_row048
table2_row049
table2_row050
table2_row051
table2_row052
table2_row053
table2_row054
table2_row055
table2_row056
table2_row057
table2_row058
table2_row059
table2_row060
table2_row061
table2_row062
table2_row063
table2_row064
table2_row065
table2_row069
table2_row070
table2_row071
table3_row001
table3_row002
table3_row003
table3_row004
table3_row006
table3_row007
table3_row008
table3_row009
table3_row010
table3_row011
table3_row012
table3_row013
table3_row014
table3_row015
table3_row016
table3_row017
table3_row018
table3_row019
table3_row020
table3_row021
table3_row022
table3_row023
table3_row024
table3_row025
table3_row026
table3_row027
table3_row028
table3_row029
table3_row030
table4_row001
table4_row002
table4_row003
table4_row004
table4_row005
table4_row006
table4_row007
table4_row008
table4_row009
table4_row010
table4_row011
table4_row012
table4_row013
table4_row014
table4_row015
table4_row016
table4_row017
table4_row018
table4_row019
table4_row020
table4_row021
table4_row022
table4_row023
table4_row024
table4_row026
table5_row002
table5_row004
table5_row005
table5_row006
table5_row008
table5_row009
table5_row010
table6_row002
table6_row003
table6_row004
table6_row005
table6_row006
table6_row007
table6_row009
table6_row010
table6_row011
table6_row012
table6_row013
table6_row014
table6_row015
table6_row016
table6_row017
table6_row018
table6_row019
table6_row020
table6_row021
table6_row022
table6_row023
table6_row024
table6_row025
table6_row026
table6_row027
table6_row028
table6_row029
table6_row030
table6_row031
table6_row033
table6_row034
table6_row035
table6_row036
table6_row037
table6_row038
table6_row039
table6_row041
table6_row042
table6_row043
table6_row044
table6_row045
table6_row046
table6_row047
table6_row048
table6_row049
table6_row050
table6_row051
table6_row052
table6_row053
table6_row054
table6_row055
table6_row056
table6_row057
table6_row058
table6_row059
table6_row060
table6_row061
table6_row062
table6_row063
table7_row018
table7_row020
table7_row021
table7_row022
table7_row025
table7_row027
table7_row028
table7_row030
table7_row031
table7_row032
table7_row033
table7_row034
table7_row035
table7_row036
table7_row037
table7_row038
table7_row039
table7_row041
table7_row043
table7_row044
table7_row045
table7_row046
table7_row048
table7_row049
table7_row050
table7_row051
table7_row052
table7_row053
table7_row054
table7_row055
table7_row056
table7_row057
table7_row058
table7_row059
table7_row060
table7_row061
table7_row062
table7_row063
table7_row064
table7_row065
table7_row066
table7_row067
table7_row068
table7_row069
table7_row070
table7_row071
table7_row072
table7_row073
table7_row074
table7_row075
table7_row076
table7_row077
table7_row078
table7_row080
table7_row081
table7_row082
table7_row083
table7_row084
table7_row085
table7_row086
table7_row087
table7_row088
table7_row089
table7_row090
table7_row091
table7_row092
table7_row093
table7_row094
table7_row095
table7_row096
table7_row097
table7_row098
table7_row099
table7_row100
table7_row101
table7_row102
table7_row103
table7_row104
table7_row105
table7_row106
table7_row107
table7_row108
table8_row004
table8_row005
table8_row006
table8_row007
table8_row008
table8_row009
table8_row010
table8_row011
table8_row012
table8_row013
table8_row014
table8_row015
table8_row016
table8_row017
table8_row018
table8_row019
table8_row020
table8_row021
table8_row022
table8_row023
table8_row024
table8_row025
table8_row026
table8_row027
table8_row028
table8_row029
table8_row030
table8_row031
table8_row032
table8_row033
table8_row034
table8_row035
table8_row036
table8_row037
table8_row038
table8_row039
table8_row040
table8_row041
table8_row042
table8_row043
table8_row044
table8_row045
table8_row046
table8_row047
table8_row048
table8_row049
table8_row050
table8_row051
table8_row052
table8_row053
table8_row054
table8_row055
table8_row056
table8_row057
table8_row058
table8_row059
table8_row060
table8_row061
table8_row062
table9_row004
table9_row006
table9_row007
table9_row008
table9_row009
table9_row010
table9_row011
table9_row012
table9_row013
table9_row014
table9_row015
table9_row016
table9_row017
table9_row018
table9_row019
table9_row020
table9_row021
table9_row022
table9_row023
table9_row024
table9_row025
table9_row026
table10_row001
table10_row002
table10_row003
table10_row004
table10_row005
table10_row006
table10_row007
table10_row008
table10_row009
table10_row010
table10_row011
table10_row012
table10_row013
table10_row014
table10_row015
table10_row016
table10_row017
table10_row018
table10_row019
table10_row020
table10_row021
table11_row002
table11_row003
table11_row004
table11_row005
IDS

# ---------------------------------------------------------------- 4. run (x sector: HZ v=0, v not in rowspace HX; z sector: HX v=0, v not in rowspace HZ)
run_one() {   # args: index id sector
  local idx=$1 id=$2 sec=$3 H G
  [ -s "$OUT/log/${id}_${sec}.done" ] && return 0
  if [ "$sec" = x ]; then H=HZ; G=HX; else H=HX; G=HZ; fi
  local res
  res=$("$BIN" method=1 finH="$MATDIR/$id/$H.mtx" finG="$MATDIR/$id/$G.mtx" \
        steps=2000000000 timeout="$SECS" seed=$((1000 + idx)) threads="$THREADS" nothrottle=1 \
        debug=0 outC="$OUT/witness/${id}_${sec}.nz" 2>"$OUT/log/${id}_${sec}.err" | grep -v '^#' | tail -1)
  echo "$id,$sec,$(echo "$res" | awk '{print $2}')" > "$OUT/log/${id}_${sec}.done"
  echo "$id $sec -> weight $(echo "$res" | awk '{print $2}')"
}
export -f run_one; export BIN MATDIR OUT SECS THREADS

N=$(wc -l < "$OUT/ids.txt")
echo ">> $N codes x 2 sectors, ${SECS}s each, $JOBS in parallel x $THREADS threads"
echo ">> expected wall time: about $(( N * 2 * SECS / JOBS / 60 )) minutes"
awk '{print NR, $1, "x"; print NR, $1, "z"}' "$OUT/ids.txt" | xargs -P "$JOBS" -n 3 bash -c 'run_one "$@"' _

echo "id,sector,weight" > "$OUT/results.csv"
cat "$OUT"/log/*.done | sort >> "$OUT/results.csv"
echo ">> done: $OUT/results.csv  ($(($(wc -l < "$OUT/results.csv") - 1)) sector results)"
echo ">> zip for upload:  zip -qr distm4ri_results.zip $(basename "$OUT")"

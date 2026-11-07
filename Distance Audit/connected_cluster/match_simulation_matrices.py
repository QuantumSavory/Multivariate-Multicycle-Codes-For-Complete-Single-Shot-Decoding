#!/usr/bin/env python3
"""Match saved matrices of Table I and simulation codes to audited instances.

For each pair below, the script loads the X- and Z-check matrices of both
files and reports whether they have the same row spaces over GF(2)
(equal reduced row-echelon forms). Equal row spaces mean the two files define
the same CSS code with the same qubit labels, so a distance certificate for
one applies to the other.

Usage (from the repository root or from this folder):
    python3 match_simulation_matrices.py            # writes match_simulation_matrices.csv

Only the Python standard library is needed for .mtx files; h5py is needed
for the HDF5 entries of Figure Provenance/MM_QECC_Database (skipped if absent).
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CC = os.path.join(ROOT, "Distance Audit", "connected_cluster", "matrices")
SQ = os.path.join(ROOT, "Distance Audit", "results", "sqetch_100M")
QM = os.path.join(ROOT, "QECCs", "MM")
DB = os.path.join(ROOT, "Figure Provenance", "MM_QECC_Database")
SS = os.path.join(ROOT, "Single-Shot Decoding", "qc_matrices")

# (label, source X file, source Z file, audited instance folder holding HX.mtx/HZ.mtx)
PAIRS = [
    ("Table I MM [[96,44]]",  f"{QM}/MM_96_44_4/MM_96_44_4_HX.mtx",       f"{QM}/MM_96_44_4/MM_96_44_4_HZ.mtx",       f"{CC}/table4_row001"),
    ("Table I MM [[216,12]]", f"{QM}/MM_216_12_12/MM_216_12_12_HX.mtx",   f"{QM}/MM_216_12_12/MM_216_12_12_HZ.mtx",   f"{CC}/table4_row004"),
    ("Table I MM [[486,24]]", f"{QM}/MM_486_24_12/MM_486_24_12_HX.mtx",   f"{QM}/MM_486_24_12/MM_486_24_12_HZ.mtx",   f"{CC}/table4_row017"),
    ("Table I MM [[486,66]]", f"{QM}/MM_486_66_9/MM_486_66_9_HX.mtx",     f"{QM}/MM_486_66_9/MM_486_66_9_HZ.mtx",     f"{CC}/table4_row018"),
    ("Table I MM [[576,64]]", f"{QM}/MM_576_64_6/MM_576_64_6_HX.mtx",     f"{QM}/MM_576_64_6/MM_576_64_6_HZ.mtx",     f"{CC}/table4_row020"),
    ("Worked example MM [[648,60]]", f"{QM}/MM_648_60_9/MM_648_60_9_HX.mtx", f"{QM}/MM_648_60_9/MM_648_60_9_HZ.mtx", f"{CC}/table4_row022"),
    ("Single-shot MM [[144,12]] W9", f"{SS}/MM_144_12_12_HX.mtx", f"{SS}/MM_144_12_12_HZ.mtx", f"{CC}/simulation_MM_144_12_12"),
    ("Simulation MM [[144,12]] W9 vs Table III", f"{CC}/simulation_MM_144_12_12/HX.mtx", f"{CC}/simulation_MM_144_12_12/HZ.mtx", f"{CC}/table3_row002"),
    ("QECCs/MM/MM_144_6_4 vs table2_row002", f"{QM}/MM_144_6_4/MM_144_6_4_HX.mtx", f"{QM}/MM_144_6_4/MM_144_6_4_HZ.mtx", f"{SQ}/table2_row002"),
]
H5PAIRS = [
    ("DB MM_QECC_144_6_8_W6 (Figs. 13-14)",   "MM_QECC_144_6_8_W6.h5",   f"{SQ}/table2_row002"),
    ("DB MM_QECC_96_12_8 (Figs. 11-12)",      "MM_QECC_96_12_8.h5",      f"{SQ}/table5_row002"),
    ("DB MM_QECC_144_12_12 (Figs. 11-12)",    "MM_QECC_144_12_12.h5",    f"{SQ}/table5_row010"),
    ("DB MM_QECC_144_12_12_W9",               "MM_QECC_144_12_12_W9.h5", f"{SQ}/table3_row002"),
    ("DB MM_QECC_486_24_12",                  "MM_QECC_486_24_12.h5",    f"{SQ}/table4_row017"),
    ("DB MM_QECC_486_66_9",                   "MM_QECC_486_66_9.h5",     f"{SQ}/table4_row018"),
    ("DB MM_QECC_648_60_9",                   "MM_QECC_648_60_9.h5",     f"{SQ}/table4_row022"),
    ("DB MM_QECC_216_6_12_W6 (Figs. 13-14) vs table2_row004", "MM_QECC_216_6_12_W6.h5", f"{SQ}/table2_row004"),
]

def load_mtx(path):
    with open(path) as f:
        assert f.readline().startswith("%%MatrixMarket")
        line = f.readline()
        while line.startswith("%"):
            line = f.readline()
        rows, cols, _ = map(int, line.split()[:3])
        R = [0] * rows
        for line in f:
            p = line.split()
            if not p or p[0].startswith("%"):
                continue
            v = int(float(p[2])) if len(p) > 2 else 1
            if v % 2:
                R[int(p[0]) - 1] ^= 1 << (int(p[1]) - 1)
    return R, cols

def load_h5(path):
    import h5py, numpy as np
    with h5py.File(path, "r") as f:
        out = []
        for key in ("parity_matrix_x", "parity_matrix_z"):
            M = np.asarray(f[key]).T % 2      # stored column-major by Julia
            rows = []
            for r in M:
                v = 0
                for j in np.nonzero(r)[0]:
                    v |= 1 << int(j)
                rows.append(v)
            out.append(rows)
        return out[0], out[1], M.shape[1]

def rref(rows):
    piv = {}
    for r in rows:
        x = r
        while x:
            p = x.bit_length() - 1
            if p in piv:
                x ^= piv[p]
            else:
                piv[p] = x
                break
    keys = sorted(piv, reverse=True)
    for p in keys:
        for q in keys:
            if q != p and (piv[q] >> p) & 1:
                piv[q] ^= piv[p]
    return tuple(sorted(piv.values()))

def compare(ax, az, na, folder):
    bx, nb = load_mtx(os.path.join(folder, "HX.mtx"))
    bz, _ = load_mtx(os.path.join(folder, "HZ.mtx"))
    if na != nb:
        return "different n"
    A, B = (rref(ax), rref(az)), (rref(bx), rref(bz))
    if A == B:
        return "same"
    if A == B[::-1]:
        return "same with X and Z exchanged"
    return "different"

def main():
    out = []
    for label, fx, fz, folder in PAIRS:
        ax, n = load_mtx(fx); az, _ = load_mtx(fz)
        out.append((label, os.path.relpath(fx, ROOT), os.path.relpath(folder, ROOT), compare(ax, az, n, folder)))
    try:
        import h5py  # noqa: F401
        for label, h5, folder in H5PAIRS:
            ax, az, n = load_h5(os.path.join(DB, h5))
            out.append((label, os.path.relpath(os.path.join(DB, h5), ROOT), os.path.relpath(folder, ROOT), compare(ax, az, n, folder)))
    except ImportError:
        print("h5py not installed: HDF5 entries skipped", file=sys.stderr)
    with open(os.path.join(HERE, "match_simulation_matrices.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "source_matrices", "audited_instance", "row_spaces"])
        w.writerows(out)
    for r in out:
        print(f"{r[3]:30s} {r[0]}")

if __name__ == "__main__":
    main()

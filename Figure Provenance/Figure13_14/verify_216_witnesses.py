#!/usr/bin/env python3
"""Check the weight-6 logical operators of the weight-6 MM [[216,6]] code (Figs. 13-14).

1. Reads the X and Z checks from the archived HDF5 matrices
   (../MM_QECC_Database/MM_QECC_216_6_12_W6.h5).
2. Reads the checks actually measured in one bulk round of the archived
   left-right circuit (lr_cache/MM_216_6_12_W6/output/circuits/*_p0.0001_r24.stim):
   CX data->ancilla gives a Z check, CX ancilla->data gives an X check.
3. Confirms both sets of checks have the same row spaces (k = 6).
4. For each witness in MM_216_6_W6_weight6_witnesses.toml, confirms that it has
   zero syndrome and lies outside the stabilizer row space, on both sets of checks.

Sector "x": HZ v = 0 and v not in rowspace(HX). Sector "z": HX v = 0 and v not in rowspace(HZ).
Needs numpy and h5py; Python >= 3.11 (tomllib).
"""
import glob, os, tomllib, collections
import numpy as np, h5py

HERE = os.path.dirname(os.path.abspath(__file__))
N = 216

def rows_from(M):
    out = []
    for r in np.asarray(M) % 2:
        v = 0
        for j in np.nonzero(r)[0]:
            v |= 1 << int(j)
        out.append(v)
    return out

def echelon(rows):
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
    return piv

def rref(rows):
    piv = echelon(rows)
    keys = sorted(piv, reverse=True)
    for p in keys:
        for q in keys:
            if q != p and (piv[q] >> p) & 1:
                piv[q] ^= piv[p]
    return tuple(sorted(piv.values()))

def in_span(v, piv):
    x = v
    while x:
        p = x.bit_length() - 1
        if p not in piv:
            return False
        x ^= piv[p]
    return True

def circuit_checks(path):
    lines = open(path).read().split("\n")
    s = next(i for i, l in enumerate(lines) if l.strip().startswith("REPEAT"))
    depth, body = 0, []
    for l in lines[s:]:
        depth += l.count("{") - l.count("}")
        body.append(l)
        if depth == 0:
            break
    zc, xc = collections.defaultdict(int), collections.defaultdict(int)
    for l in body:
        t = l.split()
        if t and t[0] == "CX":
            q = list(map(int, t[1:]))
            for a, b in zip(q[::2], q[1::2]):
                if a < N <= b:
                    zc[b] ^= 1 << a
                elif b < N <= a:
                    xc[a] ^= 1 << b
    return [xc[k] for k in sorted(xc)], [zc[k] for k in sorted(zc)]

def main():
    with h5py.File(os.path.join(HERE, "..", "MM_QECC_Database", "MM_QECC_216_6_12_W6.h5"), "r") as f:
        HX = rows_from(np.asarray(f["parity_matrix_x"]).T)
        HZ = rows_from(np.asarray(f["parity_matrix_z"]).T)
    circ = glob.glob(os.path.join(HERE, "lr_cache", "MM_216_6_12_W6", "output", "circuits", "*_p0.0001_r24.stim"))[0]
    CX, CZ = circuit_checks(circ)
    k = N - len(echelon(HX)) - len(echelon(HZ))
    same = rref(HX) == rref(CX) and rref(HZ) == rref(CZ)
    print(f"HDF5 code: n={N}, k={k}; circuit checks equal HDF5 checks: {same}")
    W = tomllib.load(open(os.path.join(HERE, "MM_216_6_W6_weight6_witnesses.toml"), "rb"))["witness"]
    ok_all = same
    for w in W:
        v = 0
        for i in w["support_one_based"]:
            v |= 1 << (i - 1)
        for name, (X, Z) in (("HDF5", (HX, HZ)), ("circuit", (CX, CZ))):
            comm, stab = (Z, X) if w["sector"] == "x" else (X, Z)
            zero = all(bin(r & v).count("1") % 2 == 0 for r in comm)
            nontrivial = not in_span(v, echelon(stab))
            ok = zero and nontrivial and bin(v).count("1") == w["weight"]
            ok_all &= ok
            print(f"sector {w['sector']} weight {w['weight']} on {name} checks: zero syndrome={zero}, nontrivial={nontrivial}")
    print("ALL CHECKS PASS" if ok_all else "CHECK FAILED")

if __name__ == "__main__":
    main()

"""Verify the saved logical operators against the saved check matrices (no Julia needed).

usage:  python3 verify_witnesses.py final/dist_m4ri_witnesses.toml results/sqetch_100M

Conventions (one-based supports on the QuantumClifford matrices HX, HZ):
  sector "x":  HZ v = 0 (mod 2)  and  v not in rowspace(HX)
  sector "z":  HX v = 0 (mod 2)  and  v not in rowspace(HZ)
A vector passing both tests is a nontrivial logical operator, so the distance of that
sector is at most its weight. Requires numpy and Python >= 3.11 (tomllib).
"""
import sys, tomllib
import numpy as np


def load_mtx(path):
    with open(path) as f:
        lines = [l for l in f if not l.startswith('%')]
    r, c, _ = map(int, lines[0].split())
    M = np.zeros((r, c), np.uint8)
    for l in lines[1:]:
        i, j, v = map(int, l.split())
        M[i - 1, j - 1] ^= v & 1
    return M


def echelon(M):
    """Row-echelon form over GF(2) on bit-packed rows; returns (rows, {pivot_col: row_index})."""
    R = np.packbits(M, axis=1, bitorder='little')
    piv, r = {}, 0
    for c in range(M.shape[1]):
        if r == R.shape[0]:
            break
        byte, bit = c >> 3, np.uint8(1 << (c & 7))
        hits = np.nonzero(R[r:, byte] & bit)[0]
        if len(hits) == 0:
            continue
        p = r + hits[0]
        if p != r:
            R[[r, p]] = R[[p, r]]
        mask = (R[:, byte] & bit).astype(bool)
        mask[r] = False
        R[mask] ^= R[r]
        piv[c] = r
        r += 1
    return R[:r], piv


def in_rowspace(v, R, piv):
    v = np.packbits(v, bitorder='little')
    for c, i in piv.items():
        if v[c >> 3] & (1 << (c & 7)):
            v ^= R[i]
    return not v.any()


wit_file, mat_dir = sys.argv[1], sys.argv[2]
W = tomllib.load(open(wit_file, 'rb'))['witness']
ok_count, cache = 0, {}
for w in W:
    rid, sec = w['id'], w['sector']
    if rid not in cache:
        cache.clear()
        HX, HZ = load_mtx(f'{mat_dir}/{rid}/HX.mtx'), load_mtx(f'{mat_dir}/{rid}/HZ.mtx')
        cache[rid] = (HX, HZ, {})
    HX, HZ, ech = cache[rid]
    check, stab = (HZ, HX) if sec == 'x' else (HX, HZ)
    v = np.zeros(HX.shape[1], np.uint8)
    v[np.array(w['support_one_based']) - 1] = 1
    zero_syndrome = not (check[:, v.astype(bool)].sum(axis=1) % 2).any()
    if sec not in ech:
        ech[sec] = echelon(stab)
    nontrivial = not in_rowspace(v, *ech[sec])
    ok = zero_syndrome and nontrivial and int(v.sum()) == w['weight']
    ok_count += ok
    if not ok:
        print(f'FAILED  {rid} sector={sec} weight={int(v.sum())} zero_syndrome={zero_syndrome} nontrivial={nontrivial}')
print(f'{ok_count} of {len(W)} witnesses are valid nontrivial logical operators')
sys.exit(0 if ok_count == len(W) else 1)

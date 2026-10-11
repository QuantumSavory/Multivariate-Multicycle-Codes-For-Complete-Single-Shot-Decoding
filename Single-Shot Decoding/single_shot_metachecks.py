#!/usr/bin/env python3
"""
Single-shot decoding with explicit metachecks (phenomenological noise).

Implements the single-stage decoder of Higgott & Breuckmann, PRX Quantum 4, 020332 (2023),
arXiv:2206.03122, Sec. III: in every noisy round the decoder solves

        [ H  I ] [ e ]   [ s     ]
        [ 0  M ] [ m ] = [ M s   ]

for a data-error estimate e and a measurement-error estimate m with BP+OSD, applies e, and
carries the residual error into the next round. M is the metacheck matrix (M H = 0), so the
metacheck rows act only on the measurement-error variables. After N noisy rounds, one perfect
round (a destructive readout of the data qubits) is decoded with H alone, and the shot fails
if the remaining error is a nontrivial logical operator.

Variants (--variants):
  meta      single stage on [[H, I], [0, M]] with syndrome (s, M s)   (Higgott-Breuckmann, Eq. 10; needs M)
  nometa    single stage on [H, I] with syndrome s                     (Higgott-Breuckmann, Eq. 9)
  twostage  two-stage decoding (Quintavalle et al., PRX Quantum 2, 020340 (2021), as described in
            Higgott-Breuckmann Sec. III A): stage 1 decodes the metasyndrome M s with BP+OSD on M to
            repair the syndrome; if the repaired syndrome is not in im H (a metacode failure) stage 1 is
            repeated with M' = [M; L_M], where L_M completes M to all linear relations of the checks;
            stage 2 decodes the repaired syndrome with BP+OSD on H. Needs M.

Sectors (--sectors):
  X   X-basis memory: Z data errors, checked by H_X with metachecks M_X (M_X H_X = 0)
  Z   Z-basis memory: X data errors, checked by H_Z with metachecks M_Z (M_Z H_Z = 0)
A code has single-shot metachecks in a sector only if the corresponding M is nonempty.

Noise: in every round each data qubit gets the relevant Pauli error with probability p_data
and each syndrome bit is flipped with probability q. By default p_data = q = p, as in
Higgott & Breuckmann; --depolarizing uses p_data = 2p/3, the X (or Z) marginal of a
single-qubit depolarizing channel of strength p, as in the Stim phenomenological model.

Output: one CSV row per (code, sector, variant, p, N) with shots, failures, the failure
probability P_L of the whole run, the per-round rate p_L = 1-(1-P_L)^(1/N), a Wilson 95% interval
for both, and the exact decoder settings that were used (read back from the decoder objects).
"""
import argparse, csv, itertools, json, math, os, sys, time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import scipy.io as sio
import scipy.sparse as sp

# ----------------------------------------------------------------------------- GF(2) helpers

def gf2_rref(A):
    A = (np.array(A, dtype=np.uint8) % 2).copy()
    rows, cols = A.shape
    piv = []
    r = 0
    for c in range(cols):
        if r == rows:
            break
        nz = np.nonzero(A[r:, c])[0]
        if len(nz) == 0:
            continue
        p = nz[0] + r
        if p != r:
            A[[r, p]] = A[[p, r]]
        others = np.nonzero(A[:, c])[0]
        others = others[others != r]
        A[others] ^= A[r]
        piv.append(c)
        r += 1
    return A[:r], piv


def gf2_rank(A):
    return len(gf2_rref(A)[1])


def gf2_nullspace(A):
    """Basis (rows) of {x : A x = 0}."""
    A = np.array(A, dtype=np.uint8) % 2
    n = A.shape[1]
    R, piv = gf2_rref(A)
    free = [c for c in range(n) if c not in set(piv)]
    basis = []
    for f in free:
        v = np.zeros(n, dtype=np.uint8)
        v[f] = 1
        for i, pc in enumerate(piv):
            if R[i, f]:
                v[pc] = 1
        basis.append(v)
    return np.array(basis, dtype=np.uint8).reshape(len(basis), n)


def logical_basis(H_detect, H_same):
    """Logical operators that detect nontrivial errors of the type checked by H_detect.

    Errors R with H_detect R = 0 are trivial iff R lies in rowspace(H_same) (stabilizers of the
    same Pauli type as R). The returned rows L span ker(H_same) modulo rowspace(H_detect); R is a
    logical error iff L R != 0.
    """
    K = gf2_nullspace(H_same)                 # candidates commuting with same-type stabilizers
    base = gf2_rref(H_detect)[0]
    r0 = base.shape[0]
    L = []
    cur = base
    for v in K:
        test = np.vstack([cur, v])
        if gf2_rank(test) > cur.shape[0]:
            cur = gf2_rref(test)[0]
            L.append(v)
    return np.array(L, dtype=np.uint8)

# ----------------------------------------------------------------------------- code loading

def load_mtx(path):
    return (sio.mmread(path).toarray().astype(np.int64) % 2).astype(np.uint8)


def load_h5_checks(path):
    import h5py
    with h5py.File(path, "r") as h:
        Hx = (np.array(h["parity_matrix_x"][()]) % 2).T.astype(np.uint8)   # Julia column-major
        Hz = (np.array(h["parity_matrix_z"][()]) % 2).T.astype(np.uint8)
    return Hx, Hz


def recover_block_metachecks(H, b):
    """Find a one-block-row metacheck matrix M = [B_1 ... B_r] with M H = 0 for a group-algebra
    code whose check matrix H is made of b x b blocks, trying every assignment of the distinct
    nonzero blocks of H (and their transposes). Returns M or None."""
    if H.shape[0] % b or H.shape[1] % b:
        return None
    rb, cb = H.shape[0] // b, H.shape[1] // b
    cand = []
    for i in range(rb):
        for j in range(cb):
            blk = H[i * b:(i + 1) * b, j * b:(j + 1) * b]
            for v in (blk, blk.T):
                if v.any() and not any((v == u).all() for u in cand):
                    cand.append(v.copy())
    Hi = H.astype(np.int64)
    for combo in itertools.product(range(len(cand)), repeat=rb):
        M = np.hstack([cand[k] for k in combo])
        if not ((M.astype(np.int64) @ Hi) % 2).any():
            return M.astype(np.uint8)
    return None


def load_code(spec):
    """spec: dict with keys name, and either (hx, hz, [mx], [mz]) .mtx paths or (h5, [block])."""
    if "h5" in spec:
        Hx, Hz = load_h5_checks(spec["h5"])
        Mx = Mz = None
        if spec.get("block"):
            Mx = recover_block_metachecks(Hx, spec["block"])
            Mz = recover_block_metachecks(Hz, spec["block"])
    else:
        Hx, Hz = load_mtx(spec["hx"]), load_mtx(spec["hz"])
        Mx = load_mtx(spec["mx"]) if spec.get("mx") else None
        Mz = load_mtx(spec["mz"]) if spec.get("mz") else None
    assert not ((Hx.astype(np.int64) @ Hz.T) % 2).any(), "H_X H_Z^T != 0"
    if Mx is not None:
        assert not ((Mx.astype(np.int64) @ Hx) % 2).any(), "M_X H_X != 0"
    if Mz is not None:
        assert not ((Mz.astype(np.int64) @ Hz) % 2).any(), "M_Z H_Z != 0"
    return Hx, Hz, Mx, Mz

# ----------------------------------------------------------------------------- simulation

# Higgott & Breuckmann use BP with at most 30 iterations and OSD with exhaustive search of order
# w = 10. We keep both but use the min-sum update with scaling factor 0.625: with product-sum
# updates the explicit metacheck rows (which add short cycles to the Tanner graph) degrade BP for
# the MM codes, while with min-sum they help, and min-sum is never worse in our tests.
DEFAULT_BPOSD = dict(bp_method="minimum_sum", ms_scaling_factor=0.625, max_iter=30,
                     schedule="parallel", osd_method="osd_e", osd_order=10)


def make_decoder(H, priors, cfg):
    from ldpc import BpOsdDecoder
    return BpOsdDecoder(sp.csr_matrix(H), error_channel=list(map(float, priors)), **cfg)


def decoder_settings(dec):
    out = {}
    for k in ("bp_method", "max_iter", "ms_scaling_factor", "schedule", "osd_method", "osd_order"):
        try:
            v = getattr(dec, k)
            out[k] = v if isinstance(v, (int, float, str)) else str(v)
        except Exception:
            pass
    return out


def left_kernel(H):
    """Rows spanning {r : r H = 0}: all linear relations among the checks."""
    return gf2_nullspace(H.T)


def completion(M, K):
    """Rows L_M of K that extend rowspace(M) to rowspace(K)."""
    cur = gf2_rref(M)[0] if M.shape[0] else np.zeros((0, K.shape[1]), dtype=np.uint8)
    out = []
    for v in K:
        t = np.vstack([cur, v])
        if gf2_rank(t) > cur.shape[0]:
            cur = gf2_rref(t)[0]
            out.append(v)
    return np.array(out, dtype=np.uint8).reshape(len(out), K.shape[1])


def build_round_matrix(H, M, variant):
    m, n = H.shape
    I = np.eye(m, dtype=np.uint8)
    top = np.hstack([H, I])
    if variant == "meta":
        bot = np.hstack([np.zeros((M.shape[0], n), dtype=np.uint8), M])
        return np.vstack([top, bot])
    return top


def worker(args):
    (H, M, L, variant, p_data, q, N, shots, seed, cfg) = args
    rng = np.random.default_rng(seed)
    m, n = H.shape
    Hi = H.astype(np.uint8)
    dec_final = make_decoder(H, [p_data] * n, cfg)
    if variant == "twostage":
        K = left_kernel(H)                      # z is a valid syndrome iff K z = 0
        Mp = np.vstack([M, completion(M, K)])   # M' = [M; L_M]
        dec_meta = make_decoder(M, [q] * m, cfg)
        dec_meta_full = make_decoder(Mp, [q] * m, cfg)
        dec_data = make_decoder(H, [p_data] * n, cfg)
        dec_round = dec_data
    else:
        Hround = build_round_matrix(H, M, variant)
        dec_round = make_decoder(Hround, [p_data] * n + [q] * m, cfg)
    fails = 0
    metacode_failures = 0
    for _ in range(shots):
        E = np.zeros(n, dtype=np.uint8)          # accumulated physical error
        C = np.zeros(n, dtype=np.uint8)          # accumulated correction
        for _t in range(N):
            E ^= (rng.random(n) < p_data).astype(np.uint8)
            meas = (rng.random(m) < q).astype(np.uint8)
            s = ((Hi @ (E ^ C)) % 2).astype(np.uint8) ^ meas   # syndrome of the residual, noisy
            if variant == "twostage":
                mhat = dec_meta.decode(((M @ s) % 2).astype(np.uint8)).astype(np.uint8)
                z = s ^ mhat
                if ((K @ z) % 2).any():               # metacode failure: retry with M'
                    metacode_failures += 1
                    mhat = dec_meta_full.decode(((Mp @ s) % 2).astype(np.uint8)).astype(np.uint8)
                    z = s ^ mhat
                C ^= dec_data.decode(z).astype(np.uint8)
                continue
            if variant == "meta":
                synd = np.concatenate([s, (M @ s) % 2]).astype(np.uint8)
            else:
                synd = s
            est = dec_round.decode(synd)
            C ^= est[:n].astype(np.uint8)
        s = ((Hi @ (E ^ C)) % 2).astype(np.uint8)              # perfect final round
        C ^= dec_final.decode(s).astype(np.uint8)
        R = E ^ C
        assert not ((Hi @ R) % 2).any()
        if ((L @ R) % 2).any():
            fails += 1
    return fails, shots, decoder_settings(dec_round), metacode_failures


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def per_round(P, N):
    if not (0 <= P < 1):
        return float("nan")
    return 1 - (1 - P) ** (1.0 / N)

# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codes", required=True, help="JSON file: list of code specs (see codes_example.json)")
    ap.add_argument("--only", nargs="*", help="run only these code names")
    ap.add_argument("--sectors", nargs="+", default=["X", "Z"], choices=["X", "Z"])
    ap.add_argument("--variants", nargs="+", default=["meta", "nometa"], choices=["meta", "nometa", "twostage"])
    ap.add_argument("--ps", nargs="+", type=float, default=[0.01, 0.02, 0.03, 0.04])
    ap.add_argument("--rounds", nargs="+", type=int, default=[8])
    ap.add_argument("--depolarizing", action="store_true", help="p_data = 2p/3 instead of p")
    ap.add_argument("--max-shots", type=int, default=10000)
    ap.add_argument("--max-failures", type=int, default=200)
    ap.add_argument("--batch", type=int, default=200, help="shots per worker task")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--bposd", type=str, default="{}", help="JSON overrides of the BP+OSD settings")
    ap.add_argument("--out", type=str, default="single_shot_results.csv")
    a = ap.parse_args()

    cfg = dict(DEFAULT_BPOSD)
    cfg.update(json.loads(a.bposd))
    specs = json.load(open(a.codes))
    base = Path(a.codes).resolve().parent
    for s in specs:
        for k in ("hx", "hz", "mx", "mz", "h5"):
            if s.get(k) and not os.path.isabs(s[k]):
                s[k] = str(base / s[k])
    if a.only:
        specs = [s for s in specs if s["name"] in a.only]

    new = not os.path.exists(a.out)
    # resume: points already in the output file are skipped (a point is written only when finished)
    done = set()
    if not new:
        for r in csv.DictReader(open(a.out)):
            done.add((r["code"], r["sector"], r["variant"], round(float(r["p"]), 10), int(r["rounds"])))
        print(f"resuming: {len(done)} finished points found in {a.out}", flush=True)
    fh = open(a.out, "a", newline="")
    wr = csv.writer(fh)
    if new:
        wr.writerow(["code", "n", "k", "sector", "variant", "has_metachecks", "m_checks", "m_meta",
                     "rank_meta", "dim_check_redundancy", "p", "p_data", "q", "rounds", "shots", "failures",
                     "P_L", "P_L_lo", "P_L_hi", "p_L_round", "p_L_round_lo", "p_L_round_hi", "seconds",
                     "metacode_failures", "decoder"])
    seed = a.seed
    with Pool(a.workers) as pool:
        for spec in specs:
            Hx, Hz, Mx, Mz = load_code(spec)
            n = Hx.shape[1]
            k = n - gf2_rank(Hx) - gf2_rank(Hz)
            print(f"== {spec['name']}: n={n} k={k}  H_X {Hx.shape}  H_Z {Hz.shape}  "
                  f"M_X {None if Mx is None else Mx.shape}  M_Z {None if Mz is None else Mz.shape}", flush=True)
            for sector in a.sectors:
                H, M, Hother = (Hx, Mx, Hz) if sector == "X" else (Hz, Mz, Hx)
                L = logical_basis(H, Hother)   # X memory: Z errors (checked by H_X), trivial iff in rowspace(H_Z)
                assert L.shape[0] == k, (L.shape, k)
                red = H.shape[0] - gf2_rank(H)
                rkM = 0 if M is None else gf2_rank(M)
                for variant in a.variants:
                    if variant in ("meta", "twostage") and M is None:
                        print(f"   {sector}: no metachecks, skipping '{variant}'", flush=True)
                        continue
                    for N in a.rounds:
                        for p in a.ps:
                            if (spec["name"], sector, variant, round(p, 10), N) in done:
                                print(f"   {sector} {variant:6s} N={N:3d} p={p:.4f}: done, skipping", flush=True)
                                continue
                            p_data = 2 * p / 3 if a.depolarizing else p
                            q = p
                            t0 = time.time()
                            shots = fails = 0
                            settings = None
                            mcf = 0
                            while shots < a.max_shots and fails < a.max_failures:
                                nb = min(a.max_shots - shots, a.batch * a.workers)
                                chunks = [a.batch] * (nb // a.batch) + ([nb % a.batch] if nb % a.batch else [])
                                jobs = []
                                for c in chunks:
                                    seed += 1
                                    jobs.append((H, M, L, variant, p_data, q, N, c, seed, cfg))
                                for f_, s_, st, mc in pool.map(worker, jobs):
                                    fails += f_
                                    shots += s_
                                    settings = st
                                    mcf += mc
                            P = fails / shots
                            lo, hi = wilson(fails, shots)
                            row = [spec["name"], n, k, sector, variant, M is not None, H.shape[0],
                                   0 if M is None else M.shape[0], rkM, red, p, p_data, q, N, shots, fails,
                                   P, lo, hi, per_round(P, N), per_round(lo, N), per_round(hi, N),
                                   round(time.time() - t0, 1), mcf, json.dumps(settings, sort_keys=True)]
                            wr.writerow(row)
                            fh.flush()
                            print(f"   {sector} {variant:6s} N={N:3d} p={p:.4f}: {fails}/{shots}  "
                                  f"P_L={P:.3e}  p_L/round={per_round(P, N):.3e}  ({time.time() - t0:.0f}s)", flush=True)
    fh.close()


if __name__ == "__main__":
    main()

"""Independent check of every connected-cluster (CC) certificate in cc_results/.

usage (from this folder):  python3 validate_certificates.py
For each sector marked EXACT it checks, with its own GF(2) code and without dist-m4ri:
  * the witness has zero syndrome under H and lies outside rowspace(G)
    (sector x: H=HZ, G=HX; sector z: H=HX, G=HZ), and its weight equals the bound;
  * for every weight w below the bound there is a dist-m4ri log, unchanged (SHA-256), whose
    command is method=2 with the right H/G, dmin=w and wmax=w, that exited with status 0 and
    reports "CC w=<w> completed ... no codewords found -> dmin=<w+1>";
  * whether the bundled matrices are identical to the audit's results/sqetch_100M/<id>.
Writes validation.csv next to this script.
"""
import json, csv, hashlib, re, sys, os
from pathlib import Path
B = Path(__file__).resolve().parent
AUD = B.parent/'results'/'sqetch_100M'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    rows = []; n = 0
    with open(p) as f:
        L = [l for l in f if l.strip() and not l.startswith('%')]
    m, n, _ = map(int, L[0].split()); rows = [0]*m
    for l in L[1:]:
        i, j, v = map(int, l.split())
        if v % 2: rows[i-1] ^= 1 << (j-1)
    return rows, n
def basis(rows):
    piv = {}
    for a in rows:
        while a:
            p = a.bit_length()-1
            if p in piv: a ^= piv[p]
            else: piv[p] = a; break
    return piv
def inspan(v, piv):
    while v:
        p = v.bit_length()-1
        if p not in piv: return False
        v ^= piv[p]
    return True
man = json.load(open(B/'manifest.json'))
entries = man['instances'] if isinstance(man, dict) and 'instances' in man else man
E = {e['id']: e for e in entries}
summ = list(csv.DictReader(open(B/'cc_results/summary.csv')))
out = []; problems = []
cache = {}
for r in summ:
    id, s = r['id'], r['sector']; e = E[id]
    hxp, hzp = B/e['hx'], B/e['hz']
    if id not in cache:
        hx, n = load(hxp); hz, _ = load(hzp)
        cache[id] = (hx, hz, basis(hx), basis(hz), n)
    hx, hz, bx, bz, n = cache[id]
    # repo identity
    rep = AUD/id
    same_repo = (rep/'HX.mtx').exists() and sha(rep/'HX.mtx') == sha(hxp) and sha(rep/'HZ.mtx') == sha(hzp)
    if id.startswith('simulation_'):   # matrices of the single-shot experiment (Fig. 6)
        q = B.parent.parent/'Single-Shot Decoding'/'qc_matrices'; nm = id[len('simulation_'):]
        same_repo = (q/f'{nm}_HX.mtx').exists() and sha(q/f'{nm}_HX.mtx') == sha(hxp) and sha(q/f'{nm}_HZ.mtx') == sha(hzp)
    st = json.load(open(B/'cc_results'/id/s/'result.json'))
    check, stab = (hz, bx) if s == 'x' else (hx, bz)
    H, G = (e['hz'], e['hx']) if s == 'x' else (e['hx'], e['hz'])
    sup = st.get('witness_support_one_based')
    wit_ok = False
    if sup:
        v = sum(1 << (i-1) for i in sup)
        wit_ok = all((a & v).bit_count() % 2 == 0 for a in check) and not inspan(v, stab)
    lb = st['lower_bound']; ub = st['verified_upper_bound']
    # evidence chain
    ev = {x['weight']: x for x in st['evidence']}
    chain_ok = True; why = ''
    for w in range(1, lb):
        x = ev.get(w)
        if not x: chain_ok = False; why = f'missing w={w}'; break
        p = B/'cc_results'/x['stderr']
        if not p.exists() or sha(p) != x['stderr_sha256']: chain_ok = False; why = f'log hash w={w}'; break
        txt = p.read_text()
        if not re.search(rf'CC w={w} completed in [0-9.]+s .*no codewords found -> dmin={w+1}\b', txt):
            chain_ok = False; why = f'no completion line w={w}'; break
        d = p.parent
        cmd = json.load(open(d/'command.json'))['argv']
        ex = json.load(open(d/'exit.json'))
        if ex.get('returncode') != 0 or ex.get('externally_interrupted'): chain_ok = False; why = f'exit w={w}'; break
        a = ' '.join(cmd)
        if not (f'finH=' in a and a.split('finH=')[1].split()[0].endswith(H) and a.split('finG=')[1].split()[0].endswith(G)
                and 'method=2' in cmd and f'dmin={w}' in cmd and f'wmax={w}' in cmd):
            chain_ok = False; why = f'command w={w}: {a[:200]}'; break
    exact = (r['status'] == 'EXACT')
    good = exact and wit_ok and chain_ok and lb == ub == len(sup)
    if exact and not good: problems.append((id, s, wit_ok, chain_ok, why, lb, ub))
    out.append(dict(id=id, sector=s, n=e['n'], k=e['k'], status=r['status'], lower=lb, upper=ub,
                    witness_ok=wit_ok, chain_ok=chain_ok, same_as_repo=same_repo, validated_exact=good, note=why))
w = csv.DictWriter(open(B/'validation.csv', 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
import collections
print('sectors', len(out), collections.Counter(o['status'] for o in out))
print('validated exact', sum(o['validated_exact'] for o in out), 'problems', problems)
print('exact sectors whose matrices differ from / absent in repo audit:', sorted({(o['id']) for o in out if o['validated_exact'] and not o['same_as_repo']}))

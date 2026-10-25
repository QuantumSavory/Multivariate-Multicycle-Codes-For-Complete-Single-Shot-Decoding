#!/usr/bin/env python3
"""Reconstruct Figure 4/5/7/8 circuits and count resources; no sampling/decoding."""
import argparse, hashlib, importlib.metadata, inspect, json, platform, random, sys
from datetime import datetime, timezone
from pathlib import Path

CODES = {
    'MM_144_12_12_W9': ('MM_QECC_144_12_12_W9.h5', 144, 12, 24),
    'AMC_180_6_12_W6': ('AMC_QECC_180_6_12_W6.h5', 180, 6, 24),
    'BB_144_12_12': ('BB_QECC_144_12_12.h5', 144, 12, 24),
    'TT_135_12_6': ('TT_QECC_135_12_6.h5', 135, 12, 12),
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')

def rank(a):
    a = a.copy(); r = 0
    for j in range(a.shape[1]):
        piv = [i for i in range(r, a.shape[0]) if a[i,j]]
        if not piv: continue
        i = piv[0]; a[[i,r]] = a[[r,i]]
        for k in range(r+1, a.shape[0]):
            if a[k,j]: a[k] ^= a[r]
        r += 1
        if r == a.shape[0]: break
    return r

def load(path, n, k):
    import h5py
    import numpy as np
    with h5py.File(path) as f:
        arrays = [np.asarray(f[x][()]) for x in ('parity_matrix_x','parity_matrix_z','logx_ops','logz_ops')]
    for a in arrays:
        if not np.isin(a, [0,1]).all(): raise ValueError('Nonbinary HDF5 input')
    hx, hz, lx, lz = [a.astype(np.uint8) for a in arrays]
    # Same Julia/HDF5 orientation as the uploaded experiment scripts.
    hx, hz = hx.T, hz.T
    if lx.shape != (2*n,k) or lz.shape != (2*n,k): raise ValueError('Unexpected logical tableau shape')
    lx, lz = lx[:n,:].T, lz[n:,:].T
    if hx.shape[1] != n or hz.shape[1] != n: raise ValueError('Unexpected parity matrix shape')
    if (hx @ hz.T % 2).any(): raise ValueError('Noncommuting CSS checks')
    if n-rank(hx)-rank(hz) != k: raise ValueError('Rank-derived k mismatch')
    if (hz @ lx.T % 2).any() or (hx @ lz.T % 2).any(): raise ValueError('Logical syndrome nonzero')
    if rank(lx @ lz.T % 2) != k: raise ValueError('Logical pairing is singular')
    return hx, hz, lx, lz

def describe(circuit, n):
    """Literal TICK intervals, not an optimized circuit-depth calculation."""
    import stim
    layers=[]; cur={'cnot_pairs': [], 'idle_depolarize1_targets': [], 'resets': [], 'measurements': []}
    def flush():
        nonlocal cur
        if any(cur.values()): layers.append(cur)
        cur={'cnot_pairs': [], 'idle_depolarize1_targets': [], 'resets': [], 'measurements': []}
    ticks=0; touched=set()
    for ins in circuit.flattened():
        if ins.name == 'TICK': ticks+=1; flush(); continue
        qs=[t.value for t in ins.targets_copy() if t.is_qubit_target]
        touched.update(qs)
        if ins.name in ('CX','CNOT'):
            cur['cnot_pairs'] += [qs[i:i+2] for i in range(0,len(qs),2)]
        elif ins.name == 'DEPOLARIZE1': cur['idle_depolarize1_targets'] += qs
        elif ins.name in ('R','RX','RY'): cur['resets'].append({'gate': ins.name,'targets':qs})
        elif ins.name in ('M','MX','MY','MR','MRX','MRY'): cur['measurements'].append({'gate':ins.name,'targets':qs})
    flush()
    for l in layers:
        used=[q for pair in l['cnot_pairs'] for q in pair]
        l['cnot_targets_disjoint']=len(used)==len(set(used))
        # DEPOLARIZE1 can also be round-start data noise; do not call every such target idle.
        l['depolarize1_overlaps_cnot_targets']=sorted(set(used)&set(l['idle_depolarize1_targets']))
        l['depolarize1_targets']=l.pop('idle_depolarize1_targets')
    return {'tick_count':ticks, 'cnot_containing_tick_intervals':sum(bool(l['cnot_pairs']) for l in layers),
            'cnot_count':sum(len(l['cnot_pairs']) for l in layers),
            'depolarize1_qubit_locations':sum(len(l['depolarize1_targets']) for l in layers),
            'used_ancilla_indices':sorted(q for q in touched if q>=n), 'intervals':layers}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-path',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--p',type=float,default=0.01)
    ap.add_argument('--seed',type=int,default=20261024)
    ap.add_argument('--validate-only',action='store_true')
    args=ap.parse_args()
    if not 0 < args.p < 1: ap.error('--p must be between zero and one')
    import numpy as np
    loaded={}
    for name,(filename,n,k,r) in CODES.items():
        loaded[name]=load(args.data_path/filename,n,k)
        print(f'VALID {name}: n={n}, k={k}, historical rounds={r}',flush=True)
    if args.validate_only: return
    import stim
    from scipy import sparse
    import ldpc.ckt_noise.css_code_memory_circuit as mem_circ
    out=args.output or Path('circuit_resources_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    out.mkdir(parents=True,exist_ok=False) # Never overwrite historical outputs.
    import shutil
    shutil.copy2(__file__,out/'extract_resources.py')
    versions={}
    for pkg in ['stim','ldpc','numpy','scipy','h5py','networkx']:
        try: versions[pkg]=importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError: versions[pkg]='not installed'
    source=Path(inspect.getfile(mem_circ));shutil.copy2(source,out/'css_code_memory_circuit_source.py')
    save(out/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':versions,
         'generator_path':str(source),'generator_sha256':sha(source),'command':sys.argv,
         'status':'RECONSTRUCTED; not verified as identical to historical circuits',
         'warning':'No shots sampled, no decoder called. Seeds do not establish historical schedule identity.'})
    summary=[]
    for name,(filename,n,k,r) in CODES.items():
      hx,hz,lx,lz=loaded[name]
      for model in ['phenomenological','circuit']:
       for basis in ['X','Z']:
        random.seed(args.seed);np.random.seed(args.seed)
        p=args.p; full=model=='circuit'
        kw=dict(num_rounds=r,basis=basis,after_clifford_depolarization=p if full else 0,
                before_round_data_depolarization=p,before_measure_flip_probability=p,
                after_reset_flip_probability=p if full else 0,idle_during_clifford_depolarization=p if full else 0,
                idle_inactive_measure_qubits_during_clifford_depolarization=p if full else 0,
                include_opposite_basis_detectors=False)
        c=mem_circ.make_css_code_memory_circuit(x_stabilizers=sparse.csr_matrix(hx),z_stabilizers=sparse.csr_matrix(hz),
                x_logicals=sparse.csr_matrix(lx),z_logicals=sparse.csr_matrix(lz),**kw)
        dest=out/name/model/basis;dest.mkdir(parents=True)
        c.to_file(str(dest/'circuit.stim'))
        info=describe(c,n)
        info['repeat_blocks']=[{'top_level_index':i,'repetitions':v.repeat_count,'body':describe(v.body_copy(),n)}
                              for i,v in enumerate(c) if isinstance(v,stim.CircuitRepeatBlock)]
        info.update(code=name,n=n,k=k,rounds=r,model=model,basis=basis,settings=kw,
            input_file=str((args.data_path/filename).resolve()),input_sha256=sha(args.data_path/filename),
            circuit_sha256=sha(dest/'circuit.stim'),hx_rows=len(hx),hz_rows=len(hz),
            x_check_weights=sorted(set(map(int,hx.sum(axis=1)))),z_check_weights=sorted(set(map(int,hz.sum(axis=1)))))
        save(dest/'resources.json',info)
        summary.append({key:val for key,val in info.items() if key not in ['intervals','repeat_blocks']})
        save(out/'summary.json',summary)
        print(f'SAVED {name} {model} {basis}: {len(info["used_ancilla_indices"])} ancillas, '
              f'{info["cnot_containing_tick_intervals"]} CNOT-containing intervals over the entire circuit',flush=True)
    print(f'DONE: {out.resolve()}',flush=True)
if __name__=='__main__': main()

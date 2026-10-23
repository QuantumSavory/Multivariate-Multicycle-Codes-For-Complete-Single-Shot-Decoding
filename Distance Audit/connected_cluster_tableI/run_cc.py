#!/usr/bin/env python3
"""Resumable, per-weight CSS connected-cluster certification. Python 3.10+, stdlib only."""
import argparse
import concurrent.futures
import csv
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parent
STOP = threading.Event()
PRINT_LOCK = threading.Lock()


def say(s):
    with PRINT_LOCK:
        print(s, flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, default=str) + '\n')
    os.replace(tmp, path)


def matrix(path):
    with open(path) as f:
        header = f.readline().lower().strip()
        if header != '%%matrixmarket matrix coordinate integer general':
            raise ValueError(f'Unsupported Matrix Market header: {header}')
        lines = (s for s in f if s.strip() and not s.startswith('%'))
        m, n, nnz = map(int, next(lines).split())
        rows = [0] * m
        count = 0
        for s in lines:
            i, j, v = map(int, s.split())
            if not (1 <= i <= m and 1 <= j <= n):
                raise ValueError('Matrix coordinate out of range')
            if v % 2:
                rows[i-1] ^= 1 << (j-1)
            count += 1
        if count != nnz:
            raise ValueError('Matrix Market entry count mismatch')
    return rows, n


def basis(rows):
    piv = {}
    for a in rows:
        while a:
            p = a.bit_length()-1
            if p in piv:
                a ^= piv[p]
            else:
                piv[p] = a
                break
    return piv


def member(v, piv):
    while v:
        p = v.bit_length()-1
        if p not in piv:
            return False
        v ^= piv[p]
    return True


def valid(support, check, stab_basis, n):
    if not support or len(set(support)) != len(support) or any(i < 1 or i > n for i in support):
        return False
    v = sum(1 << (i-1) for i in support)
    return all((a & v).bit_count() % 2 == 0 for a in check) and not member(v, stab_basis)


def read_nz(path):
    if not path.exists():
        return []
    result = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('%'):
            continue
        x = list(map(int, line.split()))
        if x[0] != len(x)-1:
            raise ValueError(f'Malformed NZLIST witness: {path}')
        result.append(x[1:])  # dist-m4ri NZLIST is one-based, weight then support.
    return result


def load_instance(e):
    hx_path, hz_path = ROOT/e['hx'], ROOT/e['hz']
    if sha(hx_path) != e['hx_sha256'] or sha(hz_path) != e['hz_sha256']:
        raise ValueError(f"Matrix hash mismatch: {e['id']}")
    hx, n = matrix(hx_path)
    hz, nz = matrix(hz_path)
    if n != nz or n != e['n']:
        raise ValueError('Column count mismatch')
    bx, bz = basis(hx), basis(hz)
    if n-len(bx)-len(bz) != e['k'] or e['k'] <= 0:
        raise ValueError('Dimension mismatch or no logical qubits')
    if any((a & b).bit_count() % 2 for a in hx for b in hz):
        raise ValueError('CSS commutation failed')
    for sec, h, b in [('x', hz, bx), ('z', hx, bz)]:
        support = e['witnesses'].get(sec)
        if support and not valid(support, h, b, n):
            raise ValueError(f"Invalid bundled witness: {e['id']} {sec}")
    return hx, hz, bx, bz


def certify(e, sec, args, deadline, exe_hash):
    hx, hz, bx, bz = load_instance(e)
    check, stab = (hz, bx) if sec == 'x' else (hx, bz)
    hpath, gpath = (ROOT/e['hz'], ROOT/e['hx']) if sec == 'x' else (ROOT/e['hx'], ROOT/e['hz'])
    dest = args.out/e['id']/sec
    statefile = dest/'result.json'
    identity = {k: e[k] for k in ['id', 'n', 'k', 'hx_sha256', 'hz_sha256']}
    identity.update(sector=sec, binary_sha256=exe_hash)
    if statefile.exists():
        state = json.loads(statefile.read_text())
        if any(state.get(k) != v for k, v in identity.items()):
            raise ValueError('Checkpoint identity differs: use a new output directory')
    else:
        support = e['witnesses'].get(sec)
        state = dict(identity, lower_bound=1, witness_support_one_based=support,
                     verified_upper_bound=len(support) if support else None,
                     search_estimate=e['estimates'].get(sec), status='PENDING', evidence=[])
    support = state.get('witness_support_one_based')
    if support and (not valid(support, check, stab, e['n']) or len(support) != state['verified_upper_bound']):
        raise ValueError('Checkpoint witness failed verification')
    # Check evidence files are still present and unaltered before using a saved lower bound.
    for ev in state['evidence']:
        if sha(args.out/ev['stderr']) != ev['stderr_sha256']:
            raise ValueError('Saved CC log missing or altered')
    if state['status'] == 'EXACT':
        say(f"SKIP {e['id']} d{sec.upper()}={state['lower_bound']} (already certified)")
        return
    dest.mkdir(parents=True, exist_ok=True)
    budget_end = min(deadline, time.monotonic()+args.seconds)
    while not STOP.is_set():
        lo, upper = state['lower_bound'], state['verified_upper_bound']
        if upper is not None and lo > upper:
            state['status'] = 'CONFLICT'
            break
        if upper == lo:
            state['status'] = 'EXACT'
            break
        estimate = state['search_estimate']
        # With a witness, exclude through upper-1; without a matching witness, also search
        # the estimated weight so CC can return a logical operator to verify independently.
        target = upper-1 if upper else e['n']
        if not args.ignore_estimates and estimate and (upper is None or estimate < upper):
            target = min(target, estimate)
        if args.max_weight:
            target = min(target, args.max_weight)
        if lo > target:
            state['status'] = 'LOWER_BOUND_ONLY'
            break
        remaining = int(budget_end-time.monotonic())
        if remaining < 2:
            state['status'] = 'PARTIAL'
            break
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run = dest/f'w{lo:03d}_{stamp}'
        run.mkdir()
        cmd = [str(args.binary), 'method=2', f'finH={hpath}', f'finG={gpath}',
               f'dmin={lo}', f'wmax={lo}', 'noscan=0', 'smax=0', f'timeout={remaining}',
               f'threads={args.threads}', 'nothrottle=1', 'debug=1', 'maxC=1',
               f'outC={run / "witness.nz"}']
        atomic(run/'command.json', dict(argv=cmd, started_utc=stamp,
               supplied_lower_bound=lo, timeout_seconds=remaining, binary_sha256=exe_hash))
        (run/'command.sh').write_text(shlex.join(cmd)+'\n')
        say(f"RUN {e['id']} d{sec.upper()}: weight {lo}, budget {remaining}s")
        forced = False
        with (run/'stdout.txt').open('w') as out, (run/'stderr.log').open('w') as err:
            proc = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True)
            cutoff = time.monotonic()+remaining+15
            while proc.poll() is None:
                if STOP.is_set() or time.monotonic() > cutoff:
                    forced = True
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    break
                time.sleep(0.2)
        atomic(run/'exit.json', dict(returncode=proc.returncode, externally_interrupted=forced))
        log = (run/'stderr.log').read_text(errors='replace')
        completed = re.search(rf'CC w={lo} completed[^\n]*no codewords found -> dmin={lo+1}\b', log)
        # A witness can be checked even after an interrupted call, but an interrupted
        # or failed call never advances the lower bound here.
        for support in read_nz(run/'witness.nz'):
            if not valid(support, check, stab, e['n']):
                raise ValueError(f'CC returned an invalid logical witness: {run}')
            if state['verified_upper_bound'] is None or len(support) < state['verified_upper_bound']:
                state['verified_upper_bound'] = len(support)
                state['witness_support_one_based'] = support
                state['witness_source'] = str((run/'witness.nz').relative_to(args.out))
        if completed and proc.returncode == 0 and not forced:
            state['lower_bound'] = lo+1
            state['evidence'].append(dict(weight=lo, stderr=str((run/'stderr.log').relative_to(args.out)),
                                          stderr_sha256=sha(run/'stderr.log')))
            state['status'] = 'PARTIAL'
        elif state['verified_upper_bound'] == lo:
            state['status'] = 'EXACT'  # all lower weights were already excluded before this run.
        else:
            state['status'] = 'PARTIAL' if proc.returncode == 0 or forced else 'ERROR'
        state['last_run'] = str(run.relative_to(args.out))
        atomic(statefile, state)
        if not completed or forced or proc.returncode != 0:
            break
    if state['verified_upper_bound'] is not None:
        if state['lower_bound'] > state['verified_upper_bound']:
            state['status'] = 'CONFLICT'
        elif state['lower_bound'] == state['verified_upper_bound']:
            state['status'] = 'EXACT'
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    atomic(statefile, state)
    u = state['verified_upper_bound']
    say(f"{state['status']} {e['id']} d{sec.upper()}: {state['lower_bound']} <= d <= {u or '?'}")


def summary(args, entries):
    fields = ['id','n','k','sector','status','lower_bound','verified_upper_bound','search_estimate']
    tmp = args.out/'summary.csv.tmp'
    with tmp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in entries:
            for sec in ['x','z']:
                p = args.out/e['id']/sec/'result.json'
                r = json.loads(p.read_text()) if p.exists() else dict(id=e['id'],n=e['n'],k=e['k'],sector=sec,status='PENDING')
                w.writerow({k:r.get(k,'') for k in fields})
    os.replace(tmp, args.out/'summary.csv')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, default=Path.home()/'distm4ri_tools/dist-m4ri/src/dist_m4ri')
    p.add_argument('--out', type=Path, default=ROOT/'cc_results')
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--threads', type=int, default=1)
    p.add_argument('--seconds', type=int, default=900, help='Budget per sector in this invocation')
    p.add_argument('--session-seconds', type=int, default=25200, help='Stop safely after seven hours')
    p.add_argument('--max-weight', type=int, default=0, help='Optional first-pass cap; 0 means no cap')
    p.add_argument('--ignore-estimates', action='store_true', help='Continue past unverified search estimates')
    p.add_argument('--ids', nargs='+', help='Run only these manifest IDs')
    p.add_argument('--dry-run', action='store_true', help='Validate bundled inputs and list selection; no binary required')
    args = p.parse_args()
    if min(args.jobs,args.threads,args.seconds,args.session_seconds) < 1 or args.max_weight < 0:
        p.error('Budgets and worker counts must be positive; max-weight must be nonnegative')
    entries = json.loads((ROOT/'manifest.json').read_text())['instances']
    if args.ids:
        unknown = set(args.ids)-{e['id'] for e in entries}
        if unknown:
            p.error(f'Unknown IDs: {sorted(unknown)}')
        entries = [e for e in entries if e['id'] in args.ids]
    if args.dry_run:
        for e in entries:
            load_instance(e)
            say(f"VALID {e['id']} n={e['n']} k={e['k']} priority={e['priority']}")
        say(f'{len(entries)} codes, {2*len(entries)} sectors. No CC searches launched.')
        return
    args.binary = args.binary.expanduser().resolve()
    args.out = args.out.expanduser().resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'runner.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            p.error('Another runner is using this output directory')
        exe_hash = sha(args.binary)
        version = subprocess.run([str(args.binary),'--version'], capture_output=True, text=True, check=True)
        atomic(args.out/f'environment_{time.time_ns()}.json', dict(binary=str(args.binary), binary_sha256=exe_hash,
               version=version.stdout+version.stderr, manifest_sha256=sha(ROOT/'manifest.json'), args=vars(args)),)
        deadline = time.monotonic()+args.session_seconds
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda *_: STOP.set())
        failures = []
        tasks = [(e,sec) for e in entries for sec in ['z','x']]
        def task(e, sec):
            if STOP.is_set() or time.monotonic()+2 >= deadline:
                return
            certify(e,sec,args,deadline,exe_hash)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            future = {pool.submit(task,e,s):(e['id'],s) for e,s in tasks}
            for f in concurrent.futures.as_completed(future):
                try:
                    f.result()
                except Exception as err:
                    item = dict(id=future[f][0],sector=future[f][1],error=repr(err))
                    failures.append(item)
                    say(f'ERROR {item}')
                summary(args,entries)
        if failures:
            atomic(args.out/f'errors_{time.time_ns()}.json', failures)
        say(f'Saved {args.out / "summary.csv"}. Rerun the same command to resume.')
        if failures:
            raise SystemExit(1)


if __name__ == '__main__':
    main()

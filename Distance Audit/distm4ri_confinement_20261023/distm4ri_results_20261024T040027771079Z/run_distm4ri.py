#!/usr/bin/env python3
"""Batch wrapper only. ALL searches are performed by the specified dist_m4ri binary."""
import argparse,csv,datetime,hashlib,json,os,re,shlex,shutil,subprocess,time
from pathlib import Path
BASE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dimensions(p):
    with p.open() as f:
        header=f.readline()
        if not header.startswith('%%MatrixMarket matrix coordinate'):raise ValueError('Unsupported matrix format')
        for line in f:
            if line.strip() and not line.startswith('%'):return tuple(map(int,line.split()))
    raise ValueError('No dimensions')
def parse_profile(text):
    return {int(w):int(v) for w,v in re.findall(r'#\s*w=(\d+)\s+min non-zero syndrome weight\s+(\d+)',text)}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--binary',default=str(Path.home()/'distm4ri_tools/dist-m4ri/src/dist_m4ri'))
    ap.add_argument('--threads',type=int,default=4)
    ap.add_argument('--seconds',type=int,default=900,help='Timeout per code sector, in dist-m4ri')
    ap.add_argument('--session-seconds',type=int,default=25200)
    ap.add_argument('--ids',nargs='+');ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args();assert args.threads>0 and args.seconds>0 and args.session_seconds>60
    binary=Path(args.binary).expanduser().resolve()
    manifest=json.loads((BASE/'manifest.json').read_text());entries=manifest['instances']
    if args.ids:
        assert set(args.ids)<=set(e['id'] for e in entries),'Unknown ID'
        entries=[e for e in entries if e['id'] in args.ids]
    for e in entries:
        for axis in ['x','z']:
            p=BASE/e['h'+axis];assert sha(p)==e['h'+axis+'_sha256'],p
            assert dimensions(p)[1]==e['n']
    if args.dry_run:
        for e in entries:
            print(f"VALID {e['id']}: HX/HZ hashes match, n={e['n']}, requested weights 1..{e['max_weight']}")
        print(f'{2*len(entries)} dist-m4ri calls planned. No searches launched. Binary: {binary}');return
    if not binary.is_file() or not os.access(binary,os.X_OK):raise SystemExit(f'Executable not found: {binary}')
    run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=BASE/f'distm4ri_results_{run_id}';out.mkdir()
    shutil.copy2(BASE/'manifest.json',out/'manifest.json');shutil.copy2(__file__,out/'run_distm4ri.py')
    # Preserve the actual executable used, not a rebuilt or substituted implementation.
    shutil.copy2(binary,out/'dist_m4ri_used')
    info={'started_utc':now(),'arguments':vars(args),'binary_path':str(binary),'binary_sha256':sha(binary),'wrapper_sha256':sha(__file__),'repo_commit':manifest['repo_commit'],'hostname':os.uname().nodename}
    (out/'campaign.json').write_text(json.dumps(info,indent=2)+'\n')
    for flag,name in [('--version','version.txt'),('--help','help.txt'),('--morehelp','morehelp.txt')]:
        p=subprocess.run([str(binary),flag],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        (out/name).write_text(p.stdout)
    help_text=(out/'help.txt').read_text()+(out/'morehelp.txt').read_text()
    if 'smax' not in help_text:raise SystemExit('Binary does not advertise smax; inspect saved help.')
    deadline=time.monotonic()+args.session_seconds;records=[]
    print(f'OUTPUT: {out}',flush=True)
    def write_summary():
        fields=['id','error_sector','check_matrix','weight','observed_minimum_nonzero_syndrome','profile_status','process_status','exit_code','matrix_sha256','log_directory']
        with (out/'observed_profiles.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    for e in entries:
        for sector,axis,other in [('z','x','z'),('x','z','x')]:
            remaining=int(deadline-time.monotonic())-45
            if remaining<=0:write_summary();print('Session budget exhausted; remaining sectors NOT RUN.',flush=True);return
            budget=min(args.seconds,remaining);dest=out/e['id']/sector;dest.mkdir(parents=True)
            h=BASE/e['h'+axis];g=BASE/e['h'+other]
            shutil.copy2(h,dest/'H_check.mtx');shutil.copy2(g,dest/'H_stabilizer.mtx')
            m,n,_=dimensions(h)
            cmd=[str(binary),'method=2',f'finH={dest / "H_check.mtx"}',f'finG={dest / "H_stabilizer.mtx"}',
                 f'wmax={e["max_weight"]}',f'smax={m}','dmin=1','noscan=0','wmin=0',
                 f'threads={args.threads}',f'timeout={budget}','debug=3',f'outC={dest / "logical_codewords.nz"}']
            # smax=m covers all possible positive syndrome weights; no profile value is supplied to the search.
            (dest/'command.sh').write_text(shlex.join(cmd)+'\n')
            meta={'id':e['id'],'error_sector':sector,'check_matrix':'H'+axis.upper(),'check_sha256':sha(h),'stabilizer_sha256':sha(g),'started_utc':now(),'command':cmd,'requested_wmax':e['max_weight'],'smax':m,'budget_seconds':budget}
            print(f"RUN {e['id']} {sector.upper()} errors via H{axis.upper()}: dist-m4ri, {budget}s, {args.threads} threads",flush=True)
            status='PROCESS_EXIT';begin=time.monotonic()
            with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr)
                try:p.wait(timeout=budget+30)
                except subprocess.TimeoutExpired:
                    status='EXTERNAL_TIMEOUT';p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
                except KeyboardInterrupt:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
                    (dest/'interrupted.txt').write_text(now()+'\n');raise
            meta.update(finished_utc=now(),wall_seconds=time.monotonic()-begin,exit_code=p.returncode,process_status=status)
            profile=parse_profile((dest/'stderr.log').read_text())
            meta['observed_profile']=profile
            (dest/'run_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
            for w in range(1,e['max_weight']+1):
                records.append({'id':e['id'],'error_sector':sector,'check_matrix':'H'+axis.upper(),'weight':w,
                    'observed_minimum_nonzero_syndrome':profile.get(w,''),'profile_status':'OBSERVED_ONLY' if w in profile else 'NOT_REPORTED',
                    'process_status':status,'exit_code':p.returncode,'matrix_sha256':sha(h),'log_directory':str(dest.relative_to(out))})
            write_summary()
            print(f"FINISHED {e['id']} {sector.upper()}: exit={p.returncode}, observed profile={profile}",flush=True)
    print(f'SAVED: {out}\nThese are observed CC profiles, not certified minima over all connected supports.',flush=True)
if __name__=='__main__':main()

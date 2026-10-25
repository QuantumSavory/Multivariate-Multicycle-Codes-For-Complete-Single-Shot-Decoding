#!/usr/bin/env python3
"""Save, audit and simulate the SAME circuits for replacement Figures 4,5,7,8."""
import argparse, hashlib, importlib.metadata, inspect, json, os, random, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
from resource_helpers import CODES, load, describe, save, sha

DECODER = dict(det_beam=8, beam_climbing=True, no_revisit_dets=True, merge_errors=True,
               pqlimit=10000, num_det_orders=10, det_order_method='DetIndex', seed=2384753)
FIGURES = {'phenomenological_X':4,'phenomenological_Z':5,'circuit_X':7,'circuit_Z':8}

def versions():
    out={}
    for name in ['numpy','scipy','h5py','stim','sinter','ldpc','tesseract-decoder','networkx','matplotlib']:
        try: out[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: out[name]='not found'
    return out

def prepare(args):
    import numpy as np
    import stim
    from scipy import sparse
    import ldpc.ckt_noise.css_code_memory_circuit as gen
    import sinter
    # Fail on input or decoder incompatibility before producing an experiment directory.
    decoder_object()
    data={name:load(args.data_path/f,n,k) for name,(f,n,k,r) in CODES.items()}
    args.output.mkdir(parents=True,exist_ok=False)
    out=args.output
    for name in ['rerun_figures.py','resource_helpers.py','redraw.py']:
        shutil.copy2(Path(__file__).with_name(name),out/name)
    source=Path(inspect.getfile(gen));shutil.copy2(source,out/'generator_source.py')
    ps=np.logspace(-4,-1,9) if not args.smoke else np.array([0.01])
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'kind':'NEW_SIMULATION_RUN',
        'smoke_only':args.smoke,'python':sys.version,'packages':versions(),'decoder':DECODER,
        'generator_source_sha256':sha(source),'generation_seed':args.seed,
        'sampling_seed':'Sinter/Stim sampling RNG not fixed; archived counts are the experimental record',
        'failure_definition':'Sinter default: any predicted observable differs from the sampled observable',
        'normalization':'Installed sinter.plot_error_rate with failure_units_per_shot_func=metadata r; plotting source archived',
        'interval':'Sinter likelihood region with highlight_max_likelihood_factor=1000',
        'tasks':[]}
    for name,(filename,n,k,r) in CODES.items():
      hx,hz,lx,lz=data[name]
      inp=out/'inputs'/filename;inp.parent.mkdir(exist_ok=True);shutil.copy2(args.data_path/filename,inp)
      for model in ['phenomenological','circuit']:
       full=model=='circuit'
       for basis in ['X','Z']:
        for j,p in enumerate(ps):
         random.seed(args.seed);np.random.seed(args.seed)
         kw=dict(num_rounds=r,basis=basis,after_clifford_depolarization=float(p) if full else 0,
             before_round_data_depolarization=float(p),before_measure_flip_probability=float(p),
             after_reset_flip_probability=float(p) if full else 0,
             idle_during_clifford_depolarization=float(p) if full else 0,
             idle_inactive_measure_qubits_during_clifford_depolarization=float(p) if full else 0,
             include_opposite_basis_detectors=False)
         c=gen.make_css_code_memory_circuit(x_stabilizers=sparse.csr_matrix(hx),z_stabilizers=sparse.csr_matrix(hz),
               x_logicals=sparse.csr_matrix(lx),z_logicals=sparse.csr_matrix(lz),**kw)
         dest=out/'tasks'/f'{model}_{basis}'/name/f'p{j:02d}';dest.mkdir(parents=True)
         c.to_file(str(dest/'circuit.stim'))
         # Both DEM and resource counts are obtained from the saved circuit bytes.
         c=stim.Circuit.from_file(str(dest/'circuit.stim'))
         dem=c.detector_error_model(decompose_errors=False)
         dem.to_file(str(dest/'detector_error_model.dem'))
         resources=describe(c,n)
         resources['repeat_blocks']=[{'index':i,'repetitions':v.repeat_count,'body':describe(v.body_copy(),n)}
                                    for i,v in enumerate(c) if isinstance(v,stim.CircuitRepeatBlock)]
         resources['x_check_weights']=sorted(set(map(int,hx.sum(axis=1))))
         resources['z_check_weights']=sorted(set(map(int,hz.sum(axis=1))))
         save(dest/'resources.json',resources)
         metadata=dict(code_key=name,n=n,k=k,r=r,p=float(p),basis=basis,model=model,
                       circuit_sha256=sha(dest/'circuit.stim'),run_type='new_revision_run')
         task=sinter.Task(circuit=c,detector_error_model=dem,decoder='tesseract-custom',json_metadata=metadata)
         manifest['tasks'].append(dict(directory=str(dest.relative_to(out)),metadata=metadata,
             settings=kw,strong_id=task.strong_id(),input_sha256=sha(inp),
             dem_sha256=sha(dest/'detector_error_model.dem'),resources_sha256=sha(dest/'resources.json'),
             max_shots=200 if args.smoke else (100000 if not full else 200000),
             max_errors=20 if args.smoke else (1000 if not full else 5000)))
         print(f'PREPARED {model} {basis} {name} p={p:.6g}',flush=True)
    save(out/'manifest.json',manifest)
    return manifest

def decoder_object():
    import tesseract_decoder
    from tesseract_decoder import TesseractSinterDecoder
    kw=dict(DECODER);kw['det_order_method']=tesseract_decoder.utils.DetOrder.DetIndex
    return TesseractSinterDecoder(**kw)

def load_tasks(out,manifest,group):
    import sinter,stim
    tasks=[]; records=[]
    for rec in manifest['tasks']:
        meta=rec['metadata']
        if f'{meta["model"]}_{meta["basis"]}'!=group: continue
        dest=out/rec['directory']
        for fn,expected in [('circuit.stim',meta['circuit_sha256']),('detector_error_model.dem',rec['dem_sha256']),('resources.json',rec['resources_sha256'])]:
            if sha(dest/fn)!=expected: raise ValueError(f'Changed archived input: {dest/fn}')
        task=sinter.Task(circuit=stim.Circuit.from_file(str(dest/'circuit.stim')),
            detector_error_model=stim.DetectorErrorModel.from_file(str(dest/'detector_error_model.dem')),
            decoder='tesseract-custom',json_metadata=meta)
        if task.strong_id()!=rec['strong_id']: raise ValueError('Task identity mismatch; refusing to resume')
        tasks.append(task);records.append(rec)
    return tasks,records

def make_plot(stats, records, out, group):
    import subprocess
    expected={r['strong_id']:r for r in records}
    found={s.strong_id:s for s in stats if s.strong_id in expected}
    complete=len(found)==len(expected) and all(
        st.shots>=expected[sid]['max_shots'] or st.errors>=expected[sid]['max_errors']
        for sid,st in found.items())
    save(out/'results'/f'{group}_completion.json', {
        'complete':complete,'tasks_found':len(found),'tasks_expected':len(expected),
        'records':[dict(strong_id=sid,shots=st.shots,errors=st.errors,discards=st.discards,seconds=st.seconds)
                   for sid,st in found.items()]})
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    plot_dir=out/'plot_records'/f'{group}_{stamp}'
    command=[sys.executable,str(Path(__file__).with_name('redraw.py')),
             '--run-dir',str(out),'--group',group,'--output',str(plot_dir),'--allow-smoke']
    subprocess.run(command,check=True)
    # Also expose the newest plots at a simple stable location.
    for image in plot_dir.glob('*.pdf'):
        shutil.copy2(image,out/'figures'/image.name)
    for image in plot_dir.glob('*.png'):
        shutil.copy2(image,out/'figures'/image.name)
    return complete


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-path',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=20261024)
    ap.add_argument('--prepare-only',action='store_true')
    ap.add_argument('--resume',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='Separate short test campaign; NOT publication results')
    ap.add_argument('--group',choices=list(FIGURES),help='Run just one figure; default all four')
    args=ap.parse_args()
    if hasattr(os, 'sched_getaffinity') and args.workers>len(os.sched_getaffinity(0)):
        ap.error('--workers exceeds the CPU affinity available to this process')
    if args.workers<1:ap.error('--workers must be positive')
    if args.resume:
        manifest=json.loads((args.output/'manifest.json').read_text())
        if manifest['packages']!=versions(): raise ValueError('Package versions changed; restore the saved environment before resuming')
        if manifest['decoder']!=DECODER: raise ValueError('Decoder options changed')
    else:
        if args.data_path is None:ap.error('--data-path is required for a new run')
        manifest=prepare(args)
    if args.prepare_only:
        print('PREPARATION COMPLETE; no sampling performed.',flush=True);return
    import sinter
    out=args.output
    (out/'results').mkdir(exist_ok=True);(out/'figures').mkdir(exist_ok=True)
    decoder=decoder_object()
    groups=[args.group] if args.group else list(FIGURES)
    status={}
    for group in groups:
        tasks,records=load_tasks(out,manifest,group)
        print(f'RUN {group}: {len(tasks)} tasks, {args.workers} workers',flush=True)
        stats=sinter.collect(num_workers=args.workers,tasks=tasks,
            max_shots=records[0]['max_shots'],max_errors=records[0]['max_errors'],
            custom_decoders={'tesseract-custom':decoder},print_progress=True,start_batch_size=100,
            save_resume_filepath=str(out/'results'/f'{group}.csv'))
        status[group]=make_plot(stats,records,out,group)
        save(out/'completion_this_invocation.json',status)
        print(f'SAVED Figure {FIGURES[group]}: all stopping targets met={status[group]}',flush=True)
    print(f'DONE {out.resolve()} (smoke-only={manifest["smoke_only"]})',flush=True)
if __name__=='__main__':main()

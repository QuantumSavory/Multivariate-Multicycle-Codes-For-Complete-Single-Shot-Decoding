#!/usr/bin/env python3
"""Plot existing revision-run CSVs with the original Figures 4/5/7/8 style. No simulation."""
import argparse, hashlib, inspect, json
from pathlib import Path
from datetime import datetime, timezone

SPECS={
 'phenomenological_X':(4,'X','phenomenological'),
 'phenomenological_Z':(5,'Z','phenomenological'),
 'circuit_X':(7,'X','circuit-level'),
 'circuit_Z':(8,'Z','circuit-level'),
}
STYLE={
 'AMC_180_6_12_W6':('AMC [[180,6,12]]','#1f77b4','o'),
 'BB_144_12_12':('BB [[144,12,12]]','#ff7f0e','v'),
 'MM_144_12_12_W9':('MM [[144,12,12]]','#2ca02c','*'),
 'TT_135_12_6':('TT [[135,12,6]]','#d62728','s'),
}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--run-dir',type=Path,default=Path('revision_run'))
 ap.add_argument('--output',type=Path)
 ap.add_argument('--group',choices=SPECS,help='Optional: redraw only one completed figure')
 ap.add_argument('--allow-smoke',action='store_true',help=argparse.SUPPRESS)
 args=ap.parse_args()
 import numpy as np
 import sinter
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 manifest=json.loads((args.run_dir/'manifest.json').read_text())
 if manifest.get('smoke_only') and not args.allow_smoke:raise ValueError('This is a smoke-test run; choose revision_run instead.')
 out=args.output or args.run_dir/('figures_sinter_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 out.mkdir(parents=True,exist_ok=False)
 # Keep the exact installed plotting implementation as part of this plotting record.
 (out/'sinter_plot_error_rate_source.txt').write_text(inspect.getsource(sinter.plot_error_rate))
 import importlib.metadata
 record={'sinter_version':importlib.metadata.version('sinter'),
         'matplotlib_version':matplotlib.__version__,
         'plotting':'sinter.plot_error_rate; failure_units_per_shot_func = metadata r; highlight_max_likelihood_factor=1000',
         'warning':'This restores the original Sinter plotting convention, not the rerun script\'s Wilson plotting convention. Raw counts are unchanged.',
         'figures':[]}
 for group in ([args.group] if args.group else SPECS):
  number,basis,model=SPECS[group]
  src=args.run_dir/'results'/f'{group}.csv'
  if not src.exists():print(f'SKIP Figure {number}: {src} not yet present');continue
  # Plot a fixed local snapshot, never edit or replace the live simulation CSV.
  raw=src.read_bytes();snapshot=out/f'{group}_counts.csv';snapshot.write_bytes(raw)
  stats=list(sinter.read_stats_from_csv_files(str(snapshot)))
  expected={r['strong_id']:r for r in manifest['tasks'] if r['metadata']['model']+'_'+r['metadata']['basis']==group}
  actual={s.strong_id:s for s in stats}
  unexpected=set(actual)-set(expected)
  if unexpected:raise ValueError(f'{group}: unexpected task IDs; refusing to mix experiments')
  for s in stats:
   if s.json_metadata!=expected[s.strong_id]['metadata']:raise ValueError('Task metadata mismatch')
   if s.discards:raise ValueError('Unexpected discarded shots; review denominator before plotting')
   if s.json_metadata['code_key'] not in STYLE:raise ValueError('Unknown code identifier')
  complete=len(actual)==len(expected) and all(s.shots>=expected[s.strong_id]['max_shots'] or s.errors>=expected[s.strong_id]['max_errors'] for s in stats)
  if not stats:print(f'SKIP Figure {number}: no completed batches');continue
  fig,ax=plt.subplots(figsize=(10,8),dpi=150)
  def label(s):return STYLE[s.json_metadata['code_key']][0]
  bylabel={v[0]:v for v in STYLE.values()}
  def plot_args(index,group_key,group_stats):
   _,color,marker=bylabel[group_key]
   return dict(color=color,marker=marker,linestyle='-')
  sinter.plot_error_rate(ax=ax,stats=stats,x_func=lambda s:s.json_metadata['p'],
      group_func=label,failure_units_per_shot_func=lambda s:s.json_metadata['r'],
      highlight_max_likelihood_factor=1000,plot_args_func=plot_args)
  xs=np.logspace(-4,-1,100)
  ax.plot(xs,xs,'k--',alpha=.5,linewidth=1.5,label='$p_L = p$')
  ax.set_xscale('log');ax.set_yscale('log')
  ax.set_xlim(1e-4,1e-1);ax.set_ylim(1e-4,1e-1)
  ax.set_xlabel('Physical Error Rate $p$',fontsize=14)
  ax.set_ylabel('Logical Error Rate per Round $p_L$',fontsize=14)
  ax.set_title(f'Tesseract: {basis} Memory Experiment\n({model} noise model)',fontsize=15)
  ax.grid(True,which='both',alpha=.3)
  ax.legend(loc='upper left',fontsize=11)
  fig.tight_layout()
  prefix='SMOKE_' if manifest.get('smoke_only') else ('' if complete else 'PARTIAL_')
  for ext in ['png','pdf']:fig.savefig(out/f'{prefix}figure{number:02d}.{ext}',dpi=600,bbox_inches='tight')
  plt.close(fig)
  record['figures'].append({'figure':number,'source':str(src.resolve()),'csv_sha256':hashlib.sha256(raw).hexdigest(),
      'complete':complete,'tasks_found':len(actual),'tasks_expected':len(expected),
      'total_shots':sum(s.shots for s in stats),'total_errors':sum(s.errors for s in stats)})
  print(f'SAVED {prefix}figure{number:02d}.pdf and .png; complete={complete}',flush=True)
 (out/'plot_record.json').write_text(json.dumps(record,indent=2)+'\n')
 print(f'OUTPUT: {out.resolve()}')
if __name__=='__main__':main()

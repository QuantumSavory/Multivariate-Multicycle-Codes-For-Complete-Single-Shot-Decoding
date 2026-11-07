"""Redraw Figs. 13–14 from the archived Sinter counts; no sampling."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sinter

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    a=parser.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    codes={'BB_144_12_12':('BB [[144,12,12]]','#ff8000',24),
           'MM_144_6_8_W6':('MM [[144,6,8]]','#005aa6',16),
           'MM_216_6_12_W6':('MM [[216,6,6]]','#2ca02c',24)}
    schedules={'lr':'LRC','LDPC':'default'}
    for basis in 'XZ':
        stats=sinter.read_stats_from_csv_files(a.data_dir/f'results_{basis}_tesseract-custom_both_threshold.csv')
        fig,ax=plt.subplots(figsize=(6.4,5.1),layout='constrained')
        for key,(label,color,rounds) in codes.items():
            for sched,tag in schedules.items():
                ss=[s for s in stats if (s.json_metadata['code_key'],s.json_metadata['circuit_type'])==(key,sched)]
                assert len(ss)==len({s.json_metadata['p'] for s in ss})==11
                assert all(s.json_metadata['basis']==basis and s.json_metadata['r']==rounds and s.decoder=='tesseract-custom' for s in ss)
                solid=sched=='lr'
                style=dict(label=label+' '+tag,color=color,linestyle='-' if solid else ':',marker='s' if solid else 'o',markersize=4.2,
                           markerfacecolor=color if solid else 'none',markeredgecolor='white' if solid else color,markeredgewidth=.65 if solid else 1.15,linewidth=1.6)
                sinter.plot_error_rate(ax=ax,stats=ss,x_func=lambda s:s.json_metadata['p'],
                    failure_units_per_shot_func=lambda s:s.json_metadata['r'],highlight_max_likelihood_factor=1000,
                    plot_args_func=lambda i,g,items:style.copy())
        assert len(stats)==66
        ax.plot([1e-4,1e-1],[1e-4,1e-1],'--',color='0.55',lw=1,label=r'$p_L=p$')
        ax.set(xscale='log',yscale='log',xlim=(1e-4,1e-1),ylim=(1e-4,1e-1),xlabel=r'Physical Error Rate $p$',ylabel=r'Logical Error Rate per Round $p_L$',title=f'Tesseract: {basis} Memory Experiment\n(circuit-level noise model)')
        ax.set_axisbelow(True); ax.grid(which='major',color='0.80',lw=.65);ax.grid(which='minor',color='0.91',lw=.4)
        ax.legend(loc='upper left',fontsize=8,framealpha=.98,edgecolor='0.35')
        fname=a.output_dir/f'LRC{basis}Basisweight6circuitlevel'
        fig.savefig(fname.with_suffix('.pdf'));fig.savefig(fname.with_suffix('.png'),dpi=220);plt.close(fig)
if __name__=='__main__': main()

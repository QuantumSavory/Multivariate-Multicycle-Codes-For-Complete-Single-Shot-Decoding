"""Independent standard-library GF(2) structural audit. No distance-search claims.
Canonical basis: lexicographic subsets; last group coordinate varies fastest.
Run: python independent_audit.py
"""
import json,csv,itertools,math,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def basis(rows):
 b={}
 for v in rows:
  while v:
   p=v.bit_length()-1
   if p in b:v^=b[p]
   else:b[p]=v;break
 return b

def residual(v,b):
 while v:
  p=v.bit_length()-1
  if p not in b:return v
  v^=b[p]
 return 0

def bits(v):
 while v:
  low=v&-v;yield low.bit_length()-1;v^=low

def columns(rows,n):
 c=[0]*n
 for i,row in enumerate(rows):
  for j in bits(row):c[j]|=1<<i
 return c

def annihilates(A,B):
 # A * B, B rows encoded as bitsets
 for a in A:
  s=0
  for i in bits(a):s^=B[i]
  if s:return False
 return True

def matrices(e):
 dims=e['orders'];N=math.prod(dims);t=len(e['supports']);q=t//2
 coords=list(itertools.product(*[range(d) for d in dims]));index={g:i for i,g in enumerate(coords)}
 blocks={k:list(itertools.combinations(range(t),k)) for k in range(t+1)}
 # boundary D_k, rows (k-1)-subsets, columns k-subsets, shift + exponent in column
 def boundary(k):
  rowblocks=blocks[k-1];colblocks=blocks[k];ri={s:i for i,s in enumerate(rowblocks)}
  rows=[0]*(len(rowblocks)*N)
  for j,J in enumerate(colblocks):
   for a in J:
    i=ri[tuple(x for x in J if x!=a)]
    for g in coords:
     for p in e['supports'][a]:
      h=tuple((x+y)%d for x,y,d in zip(g,p,dims))
      rows[i*N+index[g]]^=1<<(j*N+index[h])
  return rows,len(colblocks)*N
 dx,n=boundary(q);dz,nz=boundary(q+1);hz=columns(dz,nz)
 mx=boundary(q-1)[0] if q>=2 else []
 mz0,nmz=boundary(q+2) if q+2<=t else ([],0)
 mz=columns(mz0,nmz) if nmz else []
 return dx,hz,mx,mz,n

def audit(e):
 hx,hz,mx,mz,n=matrices(e);bx=basis(hx);bz=basis(hz)
 r={k:e[k] for k in ['id','source','source_line','reported_n','reported_k','reported_dx','reported_dz','duplicate_of']}
 r.update(n=n,k=n-len(bx)-len(bz),rank_x=len(bx),rank_z=len(bz),css_ok=annihilates(hx,columns(hz,n)),mx_ok=annihilates(mx,hx),mz_ok=annihilates(mz,hz))
 flags=[]
 for key in ['n','k']:
  if r[key]!=e['reported_'+key]:flags.append(key.upper()+'_MISMATCH')
 for side,H in [('x',hx),('z',hz)]:
  rw=[v.bit_count() for v in H];cw=[v.bit_count() for v in columns(H,n)]
  for kind,weights in [('row',rw),('col',cw)]:
   for stat,f in [('min',min),('median',statistics.median),('max',max)]:r[f'{kind}_{stat}_{side}']=f(weights)
  for stat in ['median','max']:
   key=f'reported_row_{stat}_{side}'
   if key in e and r[f'row_{stat}_{side}']!=e[key]:flags.append(key.upper()+'_MISMATCH')
  key='reported_row_constant_'+side
  if key in e and (min(rw)!=e[key] or max(rw)!=e[key]):flags.append(key.upper()+'_MISMATCH')
 if e.get('reviewer_z_support_zero_based'):
  v=sum(1<<i for i in e['reviewer_z_support_zero_based'])
  r['reviewer_z_valid']=all((h&v).bit_count()%2==0 for h in hx) and bool(residual(v,bz))
  r['reviewer_z_upper']=v.bit_count()
  assert r['reviewer_z_valid'],e['id']
  if v.bit_count()<e['reported_dz']:flags.append('REPORTED_DZ_REFUTED_BY_WITNESS')
 if e['duplicate_of']:flags.append('DUPLICATE_INPUT')
 assert r['css_ok'] and r['mx_ok'] and r['mz_ok'],e['id']
 r['flags']=';'.join(flags);return r

def main():
 es=json.loads((ROOT/'instances.json').read_text());rows=[]
 for i,e in enumerate(es,1):
  r=audit(e);rows.append(r)
  if i%50==0 or r['flags']:print(i,e['id'],r['flags'],flush=True)
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with (ROOT/'independent_structural_audit.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
 print('Audited',len(rows),'rows;',sum(bool(r['flags']) for r in rows),'flagged.')
if __name__=='__main__':main()

"""Strict evidence preflight followed by the archived paper comparison code."""
from pathlib import Path
import json,math,sys,os,runpy,gzip,lzma
ROOT=Path(__file__).resolve().parents[1]
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('Duplicate JSON key: '+k)
  d[k]=v
 return d
def stored(p):
 p=Path(p)
 return p.with_suffix(p.suffix+'.xz') if p.suffix=='.json' and p.with_suffix(p.suffix+'.xz').exists() else p.with_suffix(p.suffix+'.gz') if p.suffix=='.json' and p.with_suffix(p.suffix+'.gz').exists() else p

def read(p):
 p=stored(p)
 raw=lzma.decompress(p.read_bytes()) if p.suffix=='.xz' else gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def finite(x):return type(x) in (int,float) and math.isfinite(x)
def validate(corpus,index,refdir,variant):
 assert len(corpus)==222 and len({x['id'] for x in corpus})==222,'Corpus cardinality/unique keys'
 ids={c['id']:c for c in corpus};items=index['index'];assert len(items)==444
 keys={c['id']+'::'+m for c in corpus for m in ['FE','DL']}
 assert len({x['key'] for x in items})==444 and {x['key'] for x in items}==keys,'Index coverage'
 wanted={Path(x['file']).name for x in items}
 assert {p.name.removesuffix('.gz').removesuffix('.xz') for p in refdir.glob('*.json*')}==wanted,'Reference file coverage'
 assert {p.name.removesuffix('.gz').removesuffix('.xz') for p in (ROOT/'results'/('app-'+variant)).glob('*.json*')}==wanted,'App file coverage'
 assert not index['errors'],'Browser errors'
 for c in corpus:
  k=c['k'];assert type(k) is int and k>=3
  for q in ['te','se','source_rows']:assert len(c[q])==k and all(finite(v) for v in c[q])
  assert all(v>0 for v in c['se']) and len(set(c['source_rows']))==k and all(type(v)is int and v>0 for v in c['source_rows'])
 for it in items:
  p=Path(it['file']);assert p.parts[0]=='app-'+variant and len(p.parts)==2 and p.suffix=='.json','Unsafe app path'
  a=read(ROOT/'results'/p);r=read(refdir/p.name);c=ids[a['id']];k=c['k'];model=a['model']
  assert model in ['FE','DL'] and a['key']==r['key']==it['key']==a['id']+'::'+model
  if k>100:
   assert a['summary'] is None and r['refused'] is True and r['points']==[];continue
  assert r['refused'] is False and a['summary'] is not None
  assert a['summary']['model']==model and a['summary']['k']==k and type(a['summary']['sampled']) is bool and a['summary']['sampled']==(k>15),'Invalid summary metadata'
  for rec,isref in [(a,False),(r,True)]:
   points=rec['points'];want=5000 if k>15 else 2**k-1-(k if variant=='original' and not isref else 0)
   assert len(points)==want,'Point cardinality'
   assert type(rec['summary']['n_subsets']) is int and rec['summary']['n_subsets']==want,'Summary count cardinality'
   seen=set()
   for p in points:
    m=p['members'] if isinstance(p['members'],list) else [p['members']]
    assert m and len(set(m))==len(m) and all(type(v)is int and 1<=v<=k for v in m)
    if k<=15:assert tuple(sorted(m)) not in seen;seen.add(tuple(sorted(m)))
    quantities=['mu','I2','Q','k']+(['tau2'] if model=='DL' and len(m)>1 else [])+(['se'] if k>15 else [])
    assert all(q in p and finite(p[q]) for q in quantities),'Invalid/missing quantity'
    assert p['k']==len(m)
   for q in ['n_subsets','median_est','median_i2','min_est','max_est','q25_est','q75_est']:assert finite(rec['summary'][q]),'Invalid summary'
 return True
def execute(variant,fresh=False,preflight=False):
 os.chdir(ROOT);refdir=ROOT/('.validate-work/reference' if fresh else 'results/reference')
 validate(read(ROOT/'data/corpus.json.xz'),read(ROOT/f'results/app-{variant}.json'),refdir,variant)
 if preflight:print('INPUT PREFLIGHT PASS: 222 effect / 444 model configurations, exact fields and cardinality');return
 code=(ROOT/'bench/compare.py').read_text(encoding='utf-8')
 code=code.replace("def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))", "def read(p):return archive_read(Path('data')/p if p=='corpus.json' else Path('results')/p)")
 code=code.replace("rp=Path('reference')/Path(it['file']).name",f"rp=archive_stored(Path({str(refdir)!r})/Path(it['file']).name)")
 code=code.replace('r=read(rp)','r=archive_read(rp)')
 outname='results-fresh.json' if fresh else f'results-{variant}.json'
 code=code.replace("Path(f'results-{variant}.json')", repr(str(ROOT/'outputs'/outname)))
 code=code.replace(repr(str(ROOT/'outputs'/outname))+'.write_text', 'Path('+repr(str(ROOT/'outputs'/outname))+').write_text')
 old=sys.argv;sys.argv=['compare.py',variant]
 try:exec(compile(code,'bench/compare.py','exec'),{'__name__':'__main__','archive_read':read,'archive_stored':stored})
 finally:sys.argv=old
 result=read(ROOT/'outputs'/outname);expected=read(ROOT/'expected/paper_values.json')
 assert (result['passing'],result['total'])==((expected['passed'],expected['checks']) if variant=='patched' else (expected['before_passed'],expected['before_checks'])),'Comparison count/verdict mismatch'
 if fresh:
  import csv,hashlib
  with (ROOT/'outputs/validate_R_table.csv').open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['quantity','checks','passing','max_difference','tolerance']);w.writeheader();w.writerows(dict(quantity=q,**v) for q,v in result['quantities'].items())
  print(f"{result['passing']}/{result['total']} checks pass (fresh full R refit; browser geometry from archived capture)")
if __name__=='__main__':execute(sys.argv[1], '--fresh' in sys.argv,'--preflight' in sys.argv)

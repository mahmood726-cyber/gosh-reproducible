"""Regenerate tables and figures from full archived numerical comparisons."""
from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from compare_archive import ROOT,read,execute
from compare_ui import run as compare_ui
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def table(p,rows):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def build(out,recompute=True):
 out.mkdir(parents=True,exist_ok=True)
 if recompute:
  execute('original');execute('patched')
 compare_ui()
 before=read(ROOT/'outputs/results-original.json');after=read(ROOT/'outputs/results-patched.json');corpus=read(ROOT/'data/corpus.json.xz');expected=read(ROOT/'expected/paper_values.json')
 assert set(before['quantities'])==set(after['quantities'])
 n=dict(before_passed=before['passing'],before_checks=before['total'],passed=after['passing'],checks=after['total'],datasets=len({c['dataset'] for c in corpus}),effect_configurations=len(corpus),model_configurations=len(after['coverage'])+len(after['refusals']),enumerated=sum(c['k']<=15 for c in corpus),sampled=sum(15<c['k']<=100 for c in corpus),over_cap=sum(c['k']>100 for c in corpus),ui_passed=read(ROOT/'results/ui-results-patched.json.xz')['passing'],ui_checks=read(ROOT/'results/ui-results-patched.json.xz')['total'])
 assert n==expected,(n,expected)
 rows=[]
 for q,a in after['quantities'].items():
  b=before['quantities'][q];rows.append(dict(quantity=q,checks_before=b['checks'],passed_before=b['passing'],checks_after=a['checks'],passed_after=a['passing'],max_difference_before=b['max_difference'],max_difference_after=a['max_difference'],tolerance=a['tolerance']))
 rows.append(dict(quantity='TOTAL',checks_before=n['before_checks'],passed_before=n['before_passed'],checks_after=n['checks'],passed_after=n['passed'],max_difference_before='',max_difference_after='',tolerance=''))
 table(out/'table1_by_quantity.csv',rows)
 table(out/'table2_datasets.csv',[dict(configuration=c['id'],dataset=c['dataset'],definition=c['definition'],k=c['k'],source_rows=';'.join(map(str,c['source_rows'])),mode='cap refusal' if c['k']>100 else 'enumerated' if c['k']<=15 else 'sampled') for c in corpus])
 dump(out/'numbers.json',{k:dict(value=v,source='data/corpus.json.xz; outputs/results-{original,patched}.json; results/ui-results-patched.json.xz',transformation='Full strict preflight and primary comparison; corpus aggregation',validation='expected/paper_values.json') for k,v in n.items()})
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8})
 numeric=[(q,x) for q,x in after['quantities'].items() if x['tolerance']>0]
 fig,ax=plt.subplots(figsize=(170/25.4,6))
 ax.scatter([max(x['max_difference'],1e-16) for q,x in numeric],range(len(numeric)),label='After: maximum difference',s=22)
 ax.scatter([max(before['quantities'][q]['max_difference'],1e-16) for q,x in numeric],range(len(numeric)),label='Before: maximum difference',s=22,marker='x')
 ax.set_xscale('log');ax.axvline(1e-9,color='black',ls='--',lw=1,label='Tolerance 1e-9');ax.set_yticks(range(len(numeric)),[q for q,x in numeric]);ax.invert_yaxis();ax.set_xlabel('Maximum normalized difference (zeros plotted at 1e-16)');ax.set_title('GOSH browser / metafor agreement',fontsize=11);ax.legend(loc='lower right');ax.grid(axis='x',alpha=.2)
 fig.tight_layout();save(fig,out,'figure2_agreement')
 fig=plt.figure(figsize=(170/25.4,3.8));fig.patch.set_facecolor('#f7f9fb')
 fig.text(.5,.86,'GOSH plots in the browser',ha='center',fontsize=15,weight='bold')
 fig.text(.5,.71,'FE / DL against metafor 5.2-1',ha='center',fontsize=11)
 fig.text(.5,.54,f"{n['datasets']} datasets | {n['effect_configurations']} effect configurations",ha='center',fontsize=10)
 fig.text(.5,.36,f"{n['passed']:,} / {n['checks']:,} checks pass",ha='center',fontsize=14,weight='bold',color='#24658a')
 fig.text(.5,.17,'Full enumeration and captured seeded draws. Page-cap checks included.\nNumerical software validation; dependent rows do not establish clinical independence.',ha='center',fontsize=8)
 save(fig,out,'visual_abstract');sizes={}
 for name in ['figure2_agreement','visual_abstract']:
  for ext in ['png','tif']:
   with Image.open(out/f'{name}.{ext}') as im:sizes[f'{name}.{ext}']=dict(width_pixels=im.width,height_pixels=im.height,dpi=list(map(float,im.info['dpi'])))
 dump(out/'sizes.json',sizes)
 (out/'reproduction_report.md').write_text(f"Full archived comparison: {n['passed']}/{n['checks']}; historical before {n['before_passed']}/{n['before_checks']}. UI: {n['ui_passed']}/{n['ui_checks']}. Figures show per-quantity maxima, not a distribution. I² differences are normalized by 100, other statistical quantities by max(1, |R|). Plot coordinates use their archived absolute tolerance. Images: 300 dpi, 170 mm, minimum 8 pt. Native R validation fits every accepted configuration, checks all page-cap refusals and uses archived browser geometry; it does not launch a browser.\n",encoding='utf-8')
 print(f"OUTPUTS: {n['passed']}/{n['checks']} after; {n['before_passed']}/{n['before_checks']} before")
 return n
def save(fig,out,name):
 for ext in ['png','tif']:
  options={'pil_kwargs':{'compression':'tiff_deflate'}} if ext=='tif' else {}
  fig.savefig(out/f'{name}.{ext}',dpi=300,**options)
 plt.close(fig)
if __name__=='__main__':
 import sys
 build(ROOT/'outputs',recompute='--reuse-comparisons' not in sys.argv)

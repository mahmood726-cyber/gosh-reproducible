import json, math, sys, collections
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
def fixed(v,d):
    if v==0:v=0.0
    return format(Decimal.from_float(float(v)).quantize(Decimal(1).scaleb(-d),rounding=ROUND_HALF_UP),f".{d}f")
def tick_labels(ticks):
    magnitude=max(map(abs,ticks))
    scientific=magnitude != 0 and (magnitude < 1e-4 or magnitude >= 1e7)
    for digits in range(2,18):
        values=[format(t,f'.{digits}e') if scientific else fixed(t,digits) for t in ticks]
        if all(ticks[i]==ticks[i-1] or values[i]!=values[i-1] for i in range(1,len(ticks))):
            return [__import__('re').sub(r'e([+-])0+(\d+)',r'e\1\2',v) for v in values]
    return list(map(str,ticks))

variant=sys.argv[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def arr(x):return x if isinstance(x,list) else [x]
index=read(f'app-{variant}.json'); corpus={d['id']:d for d in read('corpus.json')}
stats={}; failures=[];coverage=[];refusals=[]
def check(q,a,b,key,scale=1,exact=False):
    z=stats.setdefault(q,dict(checks=0,passing=0,max_difference=0,tolerance=0 if exact else 1e-9))
    z['checks']+=1
    if exact: diff=abs(a-b) if type(a) in (int,float) and type(b) in (int,float) else (0 if a==b else 1); ok=a==b
    else:
        ok=isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isfinite(a) and math.isfinite(b)
        diff=abs(a-b)/scale if ok else float('inf');ok=ok and diff<=1e-9
    if math.isfinite(diff):z['max_difference']=max(z['max_difference'],diff)
    else:z['nonfinite']=z.get('nonfinite',0)+1
    z['passing']+=int(ok)
    if not ok and len(failures)<200:failures.append(dict(quantity=q,key=key,app=a,reference=b,difference=diff if math.isfinite(diff) else None))
for it in index['index']:
    a=read(it['file']); key=a['key']; d=corpus[a['id']]
    rp=Path('reference')/Path(it['file']).name
    check('reference_present',rp.exists(),True,key,exact=True)
    if not rp.exists():continue
    r=read(rp)
    check('configuration_key',a.get('key'),it['key'],key,exact=True)
    check('reference_key',r.get('key'),it['key'],key,exact=True)
    if d['k']>100:
        check('app_cap_refusal',a['summary'] is None,True,key,exact=True)
        refusals.append(dict(key=key,reason='k > 100 page limit; R fit not attempted',k=d['k']))
        check('refusal_clears_chart',len(a['ui']['circles']),0,key,exact=True)
        continue
    check('app_evidence',a['summary'] is not None,True,key,exact=True)
    check('reference_success',r['refused'],False,key,exact=True)
    if a['summary'] is None or r['refused']:
        refusals.append(dict(key=key,app=a['summary'],reference_reason=r.get('reason')));continue
    ap=a['points'];rr=r['points']
    check('summary_model',a['summary'].get('model'),a['model'],key,exact=True)
    check('summary_input_k',a['summary'].get('k'),d['k'],key,exact=True)
    check('sampling_mode',a['summary'].get('sampled'),d['k']>15,key,exact=True)
    check('sampling_control_visibility',a['ui']['sampleVisible'],'block' if d['k']>15 else 'none',key,exact=True)
    def keyed(points):
        out={};seen=collections.Counter()
        for p in points:
            m=tuple(sorted(arr(p['members'])));occ=seen[m];seen[m]+=1
            out[(m,occ)]=p
        return out
    aa=keyed(ap);bb=keyed(rr)
    check('coverage',set(aa)==set(bb),True,key,exact=True)
    missing=set(bb)-set(aa);extra=set(aa)-set(bb)
    coverage.append(dict(key=key,app=len(ap),reference=len(rr),missing=len(missing),extra=len(extra),missing_singletons=sum(len(x[0])==1 for x in missing),unique_app_memberships=len({x[0] for x in aa})))
    if d['k']<=15:check('unique_enumeration',len({x[0] for x in aa}),len(ap),key,exact=True)
    for m in aa.keys()&bb.keys():
        p,t=aa[m],bb[m];pk=key+'::'+','.join(map(str,m[0]))+'#'+str(m[1])
        for q in ['mu','I2','Q','tau2','k','se']:
            if q not in p or q not in t:continue
            scale=100 if q=='I2' else max(1,abs(t[q])) if isinstance(t[q],(int,float)) else 1
            check('subset_'+q,p[q],t[q],pk,scale,exact=q=='k')
    for q,t in r['summary'].items():
        check('summary_'+q,a['summary'].get(q),t,key,100 if q=='median_i2' else max(1,abs(t)),exact=q=='n_subsets')
    check('plotted_count',len(a['ui']['circles']),len(ap),key,exact=True)
    check('display_count',int(a['ui']['count'].replace(',','').replace(' ','').replace('\u00a0','')),len(ap),key,exact=True)
    # UI rounded strings are checked against the actual exported statistics.
    check('display_median_est',float(a['ui']['estimate']),float(fixed(a['summary']['median_est'],3)),key,exact=True)
    check('display_median_i2',float(a['ui']['i2'].rstrip('%')),float(fixed(a['summary']['median_i2'],1)),key,exact=True)
    lo=min(p['mu'] for p in ap);hi=max(p['mu'] for p in ap);pad=(hi-lo)*.1 or .1
    if variant == 'patched':
        scale=max(abs(lo),abs(hi))
        pad=max((hi/scale-lo/scale)*.1,8*sys.float_info.epsilon)*scale if scale else .1
    for j,(p,c) in enumerate(zip(ap,a['ui']['circles'])):
        if variant == 'patched':
            def fraction(v,low,high):
                eps=8*sys.float_info.epsilon*max(1,abs(low),abs(high))
                dl,dh=abs(v-low),abs(v-high)
                if min(dl,dh)<=eps:v=low if dl<=dh else high
                scale=max(abs(low),abs(high))
                return (v/scale-low/scale)/(high/scale-low/scale)
            x=60+fraction(p['mu'],lo-pad,hi+pad)*520
            y=20+(1-fraction(p['I2'],0,100))*350
        else:
            x=60+(p['mu']-(lo-pad))/(hi-lo+2*pad)*520
            y=20+(1-p['I2']/100)*350
        check('plot_x',c[0],x,key)
        check('plot_y',c[1],y,key)
    ticks = [lo-pad, (lo-pad)*.5+(hi+pad)*.5, hi+pad] if variant == 'patched' else [lo+pad,(lo+hi)/2,hi]
    expected=[f'{v}%' for v in [0,25,50,75,100]]+(tick_labels(ticks) if variant == 'patched' else [fixed(t,2) for t in ticks])+['Pooled effect','I\xb2']
    check('axis_labels',a['ui']['ticks'],expected,key,exact=True)
total=sum(v['checks'] for v in stats.values());passing=sum(v['passing'] for v in stats.values())
result=dict(variant=variant,configurations=len(index['index']),quantities=stats,total=total,passing=passing,failures=failures,coverage=coverage,refusals=refusals,page_errors=index['errors'])
Path(f'results-{variant}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for q,v in stats.items():print(f"{q}: {v['passing']}/{v['checks']} pass; max difference {v['max_difference']:.17g}; tolerance {v['tolerance']}")
print(f'{passing}/{total} checks pass')

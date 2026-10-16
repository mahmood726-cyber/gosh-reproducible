import json, math, statistics, re
from pathlib import Path
from collections import Counter
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
from axis_oracle import coordinates
checks=[];failures=[]
def test(q,ok,key):
 checks.append((q,bool(ok)))
 if not ok:failures.append(dict(quantity=q,key=key))
def message_terms(text, kind):
    """Semantic contract: case insensitive, without freezing exact copy."""
    flags = re.I
    has = lambda pattern: bool(re.search(pattern, text, flags))
    # Remove explicit negated display statements before rejecting success claims.
    positive = re.sub(r"\b(?:cannot|can['’]t|not|never)\s+(?:be\s+)?(?:displayed|shown)\b", '', text, flags=flags)
    no_success = not re.search(r"\b(?:plot|subsets?|points?)\b[^.!?]*\b(?:displayed|shown)\b", positive, flags)
    if kind == 'axis':
        return dict(axis=has(r'\b(?:axis|range|limits)\b'),
                    recovery=has(r'\b(?:widen|reset)\b'),
                    retained=has(r'\bcomputed\s+results?\b[^.!?]*\b(?:retained|available|preserved)\b'),
                    no_success=no_success)
    if kind == 'omission':
        return dict(subsets=has(r'\bsubset\s+points\b'),
                    outside=has(r'\boutside\b[^.!?]*\baxis\s+range\b'), no_success=no_success)
    return dict(draws=has(r'\b(?:draws?|count)\b'),
                integer=has(r'\b(?:whole\s+number|integer)\b'),
                recovery=has(r'\b(?:enter|adjust|reset|choose)\b'),
                bounds=has(r'\b1\s+to\s+100,?000\b'), no_success=no_success)


def notice_checks(note, points, expected, key):
 omitted=len(points)-len(expected)
 note=note.strip()
 test('omission_notice_presence',bool(note)==bool(omitted),key)
 if omitted:
  for term,ok in message_terms(note,'omission').items():test('omission_message_'+term,ok,key)
  match=re.match(r'^(\d+)\s+subset points\b',note,re.I)
  test('omission_notice_count',bool(match) and int(match[1])==omitted,key)

def close(a,b,scale=1):return isinstance(a,(int,float)) and isinstance(b,(int,float)) and abs(a-b)/scale<=1e-9
import sys
variant=sys.argv[1];e=read('options-'+variant+'.json')
for d in e['records']:
 key=d['id']+'::'+d['model'];name=key.replace(':','_')+'.json'
 full=read(Path('app-'+variant)/name)
 test('seed_replay',d['repeat'],key)
 test('sample_count',len(d['points'])==1000,key)
 test('sample_prefix',d['points']==full['points'][:1000],key)
 r=read(Path('reference')/name)
 rp=r['points'][:1000]
 for a,b in zip(d['points'],rp):
  test('option_subset_membership',a['members']==b['members'],key)
  for q in ['mu','I2','Q','tau2','k']:
   if q in a and q in b:test('option_'+q,close(a[q],b[q],100 if q=='I2' else max(1,abs(b[q]))),key)
 mus=[x['mu'] for x in rp];i2=[x['I2'] for x in rp]
 quartiles=statistics.quantiles(mus,n=4,method='inclusive')
 expected=dict(n_subsets=1000,median_est=statistics.median(mus),median_i2=statistics.median(i2),min_est=min(mus),max_est=max(mus),q25_est=quartiles[0],q75_est=quartiles[2])
 for q,b in expected.items():test('option_summary_'+q,close(d['summary'][q],b,100 if q=='median_i2' else max(1,abs(b))),key)
 for prefix, observed, limits, oracle in [('axis_override',d['circles'],d['bounds'],d['overrideOracle']),('axis_automatic',d['automatic'],{},d['automaticOracle'])]:
  expected=coordinates(d['points'],limits)
  assert expected == oracle['coordinates'], 'Independent oracle evidence mismatch'
  assert len(oracle['native']) == len(expected)
  test(prefix+'_count',len(observed)==len(expected),key)
  notice_checks(d['overrideNote' if prefix=='axis_override' else 'automaticNote'],d['points'],expected,key+'::'+prefix)
  for c,wanted in zip(observed,oracle['native']):
   test(prefix+'_x',close(c[0],wanted[0],max(1,abs(wanted[0]))),key)
   test(prefix+'_y',close(c[1],wanted[1],max(1,abs(wanted[1]))),key)
 test('axis_exports_unchanged',d['unchanged'],key)
for i,d in enumerate(e['axisCases']):
 key=f"fixture::{d['model']}::{i}"
 expected=coordinates(d['points'],d['limits'])
 assert expected == d['oracle']['coordinates'], 'Independent oracle evidence mismatch'
 assert len(d['oracle']['native']) == len(expected)
 test('axis_override_count',len(d['circles'])==len(expected) and bool(expected),key)
 notice_checks(d['plotNote'],d['points'],expected,key)
 test('axis_exports_unchanged',d['unchanged'],key)
 for c,wanted in zip(d['circles'],d['oracle']['native']):
  test('axis_override_x',close(c[0],wanted[0],max(1,abs(wanted[0]))),key)
  test('axis_override_y',close(c[1],wanted[1],max(1,abs(wanted[1]))),key)
for d in e['invalidAxes']:
 key=d['model']+'::'+d['name']
 for term,ok in message_terms(d['error'],'axis').items():test('axis_error_'+term,ok,key)
 test('axis_error_visible',d['visible'],key)
 test('axis_error_empty_svg',d['empty'],key)
 test('axis_error_retained',d['retained'],key)
 test('axis_error_recovery',d['recovered'],key)
for d in e['drawCases']:
 key=d['model']+'::'+d['value']
 for term,ok in message_terms(d['error'],'draw').items():test('draw_error_'+term,ok,key)
 test('draw_error_visible',d['visible'],key)
 test('draw_error_cleared_results',d['cleared'],key)
 test('draw_error_recovery',d['recovered'],key)
assert not e['errors'], e['errors']
for d in e['uninstrumented']:
 key=d['id']+'::'+d['model'];a=read(Path('app-'+variant)/(key.replace(':','_')+'.json'))
 test('uninstrumented_summary',a['summary']==d['summary'],key)
 test('uninstrumented_point_count',len(a['points'])==d['circles'],key)
from numeric_oracle import expected as numeric_expected, observed as numeric_observed, matches as numeric_matches
assert len(e['numericMatrix']) == 76
for case in e['numericMatrix']:
 actual=numeric_observed(case)
 for field,value in numeric_expected(case).items():
  test('numeric_matrix_'+field,numeric_matches(actual[field],value),case['model']+'::'+case['name'])

table={q:dict(checks=sum(1 for x,y in checks if x==q),passing=sum(y for x,y in checks if x==q)) for q in sorted({q for q,ok in checks})}
result=dict(variant=variant,total=len(checks),passing=sum(ok for q,ok in checks),quantities=table,failures=failures[:20])
Path('ui-results-'+variant+'.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for q,v in table.items():print(q+': '+str(v['passing'])+'/'+str(v['checks'])+' pass')
print(str(result['passing'])+'/'+str(result['total'])+' UI checks pass')

if failures: sys.exit(1)

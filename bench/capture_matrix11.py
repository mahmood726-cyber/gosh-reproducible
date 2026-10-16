from pathlib import Path
import subprocess,json,sys
r=Path.cwd();t=r/'allmeta/gosh/tests';sys.path.insert(0,str(t));from numeric_oracle import expected,observed,matches
p=subprocess.run(['node',str(t/'numeric-probe.cjs'),str(r/'allmeta/gosh/index.html')],capture_output=True,text=True,encoding='utf-8',check=True)
cases=json.loads(p.stdout)
evidence=[]
for c in cases:
 wanted=expected(c);actual=observed(c)
 assert all(matches(actual[k],v) for k,v in wanted.items()), (c['model'],c['name'],[k for k,v in wanted.items() if not matches(actual[k],v)])
 evidence.append(dict(model=c['model'],state=c['name'],expected=wanted,observed=actual))
(r/'round11-matrix.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(len(cases),len(expected(cases[0])),len(cases)*len(expected(cases[0])))

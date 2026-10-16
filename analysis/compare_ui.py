"""Replay the final UI comparison over the archived actual browser captures."""
from pathlib import Path
import sys,json
from compare_archive import read
ROOT=Path(__file__).resolve().parents[1]
def run():
 code=(ROOT/'bench/compare_options.py').read_text(encoding='utf-8')
 code=code.replace("def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))","def read(p):return archive_read(ROOT/'results'/p)")
 code=code.replace("Path('ui-results-'+variant+'.json')","(ROOT/'outputs'/('ui-results-'+variant+'.json'))")
 old=sys.argv;sys.argv=['compare_options.py','patched'];sys.path.insert(0,str(ROOT/'bench'))
 try:exec(compile(code,'bench/compare_options.py','exec'),{'__name__':'__main__','ROOT':ROOT,'archive_read':read})
 finally:sys.argv=old;sys.path.pop(0)
 got=json.loads((ROOT/'outputs/ui-results-patched.json').read_text(encoding='utf-8'));source=read(ROOT/'results/ui-results-patched.json.xz')
 assert got==source and got['total']==got['passing']==21586 and not got['failures'],'UI comparison differs from final audited evidence'
 return got
if __name__=='__main__':run()

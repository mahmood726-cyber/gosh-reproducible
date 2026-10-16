"""Verify complete inventory, source pins, outputs and actual R ledger."""
from pathlib import Path
import hashlib,json,re,csv,tempfile,gzip,lzma
from PIL import Image
from compare_archive import ROOT,read
from make_outputs import build
EXCLUDE={'.git','__pycache__','.pytest_cache','outputs','.validate-work','.slim-work'}
def source_files():return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in EXCLUDE or x.startswith('.verify-') for x in p.relative_to(ROOT).parts) and p.name not in {'SOURCE_SHA256.json','PROGRESS.md'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(paths,base,pins):
 assert {p.relative_to(base).as_posix():sha(p) for p in paths}==pins,'Inventory/hash mismatch'
def check_table(rows):
 assert rows and rows[-1]['quantity']=='TOTAL' and len({x['quantity'] for x in rows})==len(rows)
 for q,n in [('checks_before',12804532),('passed_before',12803218),('checks_after',12813556),('passed_after',12813556)]:assert int(rows[-1][q])==sum(int(x[q]) for x in rows[:-1])==n,'Table total mismatch'
def images(a,b):
 with Image.open(a) as x,Image.open(b) as y:
  assert x.convert('RGB').tobytes()==y.convert('RGB').tobytes(),'Image content mismatch'
  assert abs(x.width/300*25.4-170)<.1,'Image width'
  assert all(abs(float(v)-300)<.001 for v in x.info['dpi']+y.info['dpi']),'Image DPI'

COMMIT='e749e98871dd2665b71e99cc998ac1ff8c50effe'
BUTTON_COMMIT='5e20358918c9366eb10c1a368f2ca1b0480faa84'
RELEASE='v1.5.0'
RELEASE_DOI='10.5281/zenodo.23414184'
ALLOWED=set()

def provenance():
 for name in ['README.md','CITATION.cff','.zenodo.json']:
  text=(ROOT/name).read_text(encoding='utf-8')
  assert COMMIT in text,'Missing merged GOSH commit: '+name
  assert BUTTON_COMMIT in text,'Missing merged Validate-panel commit: '+name
  assert '<'+'ALLMETA_COMMIT_BUTTON'+'>' not in text,'Unfilled Validate-panel placeholder: '+name
  assert 'v1.4.0' not in text and 'version: 1.4.0' not in text,'Incorrect release provenance'
  assert 'the next allmeta release (pending)' not in text,'Stale pending-release wording: '+name
  assert RELEASE in text,'Missing allmeta release version: '+name
  assert set(re.findall(r'\bv\d+\.\d+\.\d+\b',text))=={RELEASE},'Wrong allmeta release version: '+name
  assert RELEASE_DOI in text,'Missing allmeta release DOI: '+name
  assert set(re.findall(r'10\.5281/zenodo\.\d+',text))=={RELEASE_DOI},'Wrong allmeta release DOI: '+name
  placeholders=set(re.findall(r'<[^<>\s]+>',text))
  assert placeholders<=ALLOWED,'Provenance placeholder remains: '+name+' '+repr(sorted(placeholders))

def compression():
 proof=read(ROOT/'analysis/compression_proof.json')
 assert {r['stored'] for r in proof}=={p.relative_to(ROOT).as_posix() for p in (ROOT/'results').rglob('*.json.xz')}
 assert not list((ROOT/'results').rglob('*.json')),'Uncompressed results remain'
 for r in proof:
  p=ROOT/r['stored'];raw=p.read_bytes()
  assert raw.startswith(b'\xfd7zXZ\x00'),'Invalid xz header'
  assert sha(p)==r['stored_sha256']
  decoded=lzma.decompress(raw)
  assert hashlib.sha256(decoded).hexdigest()==r['original_sha256']==r['decompressed_sha256']
  canonical=json.dumps(read(p),sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
  assert hashlib.sha256(canonical).hexdigest()==r['canonical_original_sha256']==r['canonical_decompressed_sha256']

def membership_compression():
 proof=read(ROOT/'analysis/membership_compression_proof.json')
 assert len(proof)==888 and len({r['file'] for r in proof})==888
 assert not list((ROOT/'results').rglob('*.txt*')),'Derived membership scratch must not ship'
 for r in proof:
  record=read(ROOT/r['source'])
  raw='\n'.join(','.join(map(str,point['members'])) for point in record['points']).encode('utf-8')
  assert type(r['trailing_newline']) is bool
  if r['trailing_newline']:raw+=b'\n'
  assert hashlib.sha256(raw).hexdigest()==r['original_sha256']==r['regenerated_sha256']


def data_compression():
 proof=read(ROOT/'analysis/data_compression_proof.json.xz')
 assert {r['stored'] for r in proof}=={p.relative_to(ROOT).as_posix() for p in (ROOT/'data').glob('*.json.xz')}
 assert not list((ROOT/'data').glob('*.json'))
 for r in proof:
  packed=(ROOT/r['stored']).read_bytes();raw=lzma.decompress(packed)
  assert hashlib.sha256(packed).hexdigest()==r['stored_sha256']
  assert hashlib.sha256(raw).hexdigest()==r['original_sha256']==r['decompressed_sha256']
  canonical=json.dumps(read(ROOT/r['stored']),sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
  assert hashlib.sha256(canonical).hexdigest()==r['canonical_sha256']

def verify():
 inventory(source_files(),ROOT,read(ROOT/'SOURCE_SHA256.json'))
 provenance()
 compression()
 membership_compression()
 data_compression()
 app=ROOT/'app';inventory([p for p in app.rglob('*') if p.is_file() and p.name!='app-sha256.json'],app,read(app/'app-sha256.json'))
 archive=source_files()+[ROOT/'SOURCE_SHA256.json']+[p for p in (ROOT/'outputs').rglob('*') if p.is_file()]
 assert sum(p.stat().st_size for p in archive)<500_000_000,'Archive exceeds 500 MB'
 for p in archive:
  assert p.stat().st_size<90_000_000,'File exceeds 90 MB: '+str(p)
  if p.suffix.lower() in {'.py','.r','.js','.json','.md','.html','.txt','.csv','.cff','.css','.patch'}:
   raw=p.read_bytes();assert not raw.startswith(b'\xef\xbb\xbf'),'UTF-8 BOM'
   assert not re.search(r'\b[A-Za-z]:[\\/](?:Users|Projects|claude-temp|Program Files)[\\/]',raw.decode('utf-8')),'Machine path: '+str(p)
 for f in read(app/'gosh/validate/MANIFEST.json')['files']:
  p=app/'gosh'/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes'] and b'\r' not in p.read_bytes()
 with (ROOT/'outputs/table1_by_quantity.csv').open(encoding='utf-8') as f:check_table(list(csv.DictReader(f)))
 with (ROOT/'outputs/table2_datasets.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 assert len(rows)==222 and len({x['configuration'] for x in rows})==222
 for name in ['figure2_agreement','visual_abstract']:images(ROOT/f'outputs/{name}.png',ROOT/f'outputs/{name}.tif')
 with tempfile.TemporaryDirectory(prefix='.verify-',dir=ROOT) as tmp:
  build(Path(tmp),recompute=False)
  for p in Path(tmp).iterdir():assert p.read_bytes()==(ROOT/'outputs'/p.name).read_bytes(),'Output differs: '+p.name
 with (ROOT/'outputs/validate_R_table.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 ledger=read(ROOT/'outputs/results-fresh.json')['quantities']
 assert len(rows)==len(ledger) and {r['quantity'] for r in rows}==set(ledger),'R quantity coverage'
 for r in rows:
  expected=ledger[r['quantity']]
  for q in ['checks','passing','max_difference','tolerance']:assert float(r[q])==expected[q],'R ledger mismatch'
 assert sum(int(r['checks']) for r in rows)==sum(int(r['passing']) for r in rows)==12813556
 z=read(ROOT/'.zenodo.json');assert z['title']=='GOSH plots in the browser: validation against the R package metafor' and z['creators']==[{'name':'Ahmad, Mahmood'}] and z['license']=='MIT' and z['version']=='1.0.0'
 assert len(z['related_identifiers'])==2 and all(x['relation']=='isDerivedFrom' for x in z['related_identifiers'])
 base=app/'r-shiny/shinylive/webr';manifest=read(base/'repo/manifest.json')
 for f in manifest['packages']:
  p=base/f.get('path','repo/'+manifest['layout']+f['file']);assert p.is_file() and sha(p)==f['sha256'] and p.stat().st_size==f['bytes'],'Missing/altered webR package'
 print('ARCHIVE VERIFIED: exact source/app inventories, full tables, deterministic 300-dpi figures and full fresh R ledger')
if __name__=='__main__':verify()

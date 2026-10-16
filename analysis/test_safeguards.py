"""Clean evidence passes; missing, duplicated and altered evidence fails."""
from pathlib import Path
import copy,json,unittest,tempfile,csv,subprocess,os,shutil,ast,math
from unittest.mock import patch
import compare_archive as c
from verify_archive import inventory,sha,check_table,images,source_files,provenance,membership_compression
class Safeguards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.corpus=c.read(c.ROOT/'data/corpus.json.xz');cls.index=c.read(c.ROOT/'results/app-patched.json');cls.ref=c.ROOT/'results/reference'
 def test_full_clean_and_bad_coverage(self):
  self.assertTrue(c.validate(self.corpus,self.index,self.ref,'patched'))
  for mutate in [lambda x:x.pop(),lambda x:x.__setitem__(1,x[0])]:
   bad=copy.deepcopy(self.corpus);mutate(bad)
   with self.assertRaises(AssertionError):c.validate(bad,self.index,self.ref,'patched')
  for mutate in [lambda x:x['te'].pop(),lambda x:x['te'].__setitem__(0,None),lambda x:x['se'].__setitem__(0,0),lambda x:x['source_rows'].__setitem__(0,-1),lambda x:x['source_rows'].__setitem__(1,x['source_rows'][0])]:
   bad=copy.deepcopy(self.corpus);mutate(bad[0])
   with self.assertRaises(AssertionError):c.validate(bad,self.index,self.ref,'patched')
  for mutate in [lambda x:x['index'].pop(),lambda x:x['index'][1].update(key=x['index'][0]['key']),lambda x:x['index'][0].update(file='../escape.json')]:
   bad=copy.deepcopy(self.index);mutate(bad)
   with self.assertRaises(AssertionError):c.validate(self.corpus,bad,self.ref,'patched')
 def test_missing_invalid_and_duplicate_reference(self):
  original=c.read;first=self.ref/Path(self.index['index'][0]['file']).name
  mutations=[lambda r:r['points'].pop(),lambda r:r['points'][0].pop('mu'),lambda r:r['points'][0].update(mu=None),lambda r:r['points'][0].update(mu=float('nan')),lambda r:r['points'][0].update(mu='0'),lambda r:r['points'][0].update(members=[0]),lambda r:r['points'].__setitem__(1,r['points'][0]),lambda r:r['summary'].pop('median_est')]
  for mutate in mutations:
   bad=original(first);mutate(bad)
   with patch.object(c,'read',side_effect=lambda p:bad if Path(p)==first else original(p)):
    with self.assertRaises((AssertionError,KeyError)):c.validate(self.corpus,self.index,self.ref,'patched')
  original_glob=Path.glob
  def extra(path,pattern):
   values=list(original_glob(path,pattern))
   return iter(values+[path/'unexpected.json']) if path==self.ref and pattern=='*.json*' else iter(values)
  with patch.object(Path,'glob',extra):
   with self.assertRaises(AssertionError):c.validate(self.corpus,self.index,self.ref,'patched')
  appfile=c.ROOT/'results'/self.index['index'][0]['file']
  for change in [{'sampled':0},{'k':999},{'model':'other'},{'n_subsets':0}]:
   bad=original(appfile);bad['summary'].update(change)
   with patch.object(c,'read',side_effect=lambda p:bad if Path(p)==appfile else original(p)):
    with self.assertRaises(AssertionError):c.validate(self.corpus,self.index,self.ref,'patched')
 def test_json_and_source_hash_gates(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.json';p.write_text('{"a":1}');self.assertEqual(c.read(p),{'a':1});pins={'x.json':sha(p)};inventory([p],Path(tmp),pins)
   p.write_text('{"a":2}')
   with self.assertRaises(AssertionError):inventory([p],Path(tmp),pins)
   for text in ['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}']:
    p.write_text(text)
    with self.assertRaises(ValueError):c.read(p)
  extra=c.ROOT/'negative-test-extra-source.txt'
  try:
   extra.write_text('negative inventory test',encoding='utf-8');self.assertIn(extra,source_files())
  finally:extra.unlink(missing_ok=True)
 def test_actual_paper_numeric_comparator(self):
  tree=ast.parse((c.ROOT/'bench/compare.py').read_text(encoding='utf-8'))
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check')
  scope={'math':math,'stats':{},'failures':[]};exec(compile(ast.Module(body=[fn],type_ignores=[]),'paper check','exec'),scope)
  for app,ref,passed in [(1,1,True),(1+5e-10,1,True),(1+2e-9,1,False),(None,None,False),(float('nan'),1,False),(float('inf'),1,False),('1',1,False)]:
   scope['stats'].clear();scope['failures'].clear();scope['check']('value',app,ref,'fixture');self.assertEqual(scope['stats']['value']['passing'],int(passed))
  for app,ref,passed in [('FE','FE',True),('FE','DL',False),(2,3,False)]:
   scope['stats'].clear();scope['check']('exact',app,ref,'fixture',exact=True);self.assertEqual(scope['stats']['exact']['passing'],int(passed))
 def test_output_tables_and_images(self):
  with (c.ROOT/'outputs/table1_by_quantity.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
  check_table(rows)
  for mutate in [lambda r:r.pop(),lambda r:r[0].update(checks_after='0'),lambda r:r.append(r[0])]:
   bad=copy.deepcopy(rows);mutate(bad)
   with self.assertRaises(AssertionError):check_table(bad)
  images(c.ROOT/'outputs/figure2_agreement.png',c.ROOT/'outputs/figure2_agreement.tif')
  with self.assertRaises(AssertionError):images(c.ROOT/'outputs/figure2_agreement.png',c.ROOT/'outputs/visual_abstract.tif')
 def test_compressed_reader_and_provenance(self):
  import gzip,lzma
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.json.gz'
   p.write_bytes(gzip.compress(b'{"a":1}',mtime=0))
   self.assertEqual(c.read(p),{'a':1})
   self.assertEqual(c.read(p.with_suffix('')),{'a':1})
   for raw in [b'{"a":1,"a":2}',b'{"a":NaN}']:
    p.write_bytes(gzip.compress(raw,mtime=0))
    with self.assertRaises(ValueError):c.read(p)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.json.xz';p.write_bytes(lzma.compress(b'{"a":1}'))
   self.assertEqual(c.read(p),{'a':1})
   self.assertEqual(c.read(p.with_suffix('')),{'a':1})
  provenance()
  original=Path.read_text
  for replacement in ['<'+'ALLMETA_COMMIT'+'>','badcommit']:
   with patch.object(Path,'read_text',lambda p,**kw:original(p,**kw).replace('e749e98871dd2665b71e99cc998ac1ff8c50effe',replacement)):
    with self.assertRaises(AssertionError):provenance()
  for replacement in ['<'+'ALLMETA_COMMIT_BUTTON'+'>','badcommit']:
   with patch.object(Path,'read_text',lambda p,**kw:original(p,**kw).replace('5e20358918c9366eb10c1a368f2ca1b0480faa84',replacement)):
    with self.assertRaises(AssertionError):provenance()
  # The released files hold no placeholders, so inject them into the read text.
  for token in ['ALLMETA_UNKNOWN','ALLMETA_RELEASE','ALLMETA_RELEASE_DOI','allmeta_release']:
   injected='<'+token+'>'
   with patch.object(Path,'read_text',lambda p,**kw:original(p,**kw)+' '+injected):
    with self.assertRaises(AssertionError,msg=injected):provenance()
 def test_wrong_release_version_refused(self):
  provenance();original=Path.read_text
  for change in [lambda t:t.replace('v1.5.0','v1.4.9'),lambda t:t+' v1.5.1',lambda t:t.replace('v1.5.0','')]:
   with patch.object(Path,'read_text',lambda p,**kw:change(original(p,**kw))):
    with self.assertRaises(AssertionError):provenance()
 def test_wrong_release_doi_refused(self):
  provenance();original=Path.read_text
  for change in [lambda t:t.replace('10.5281/zenodo.23414184','10.5281/zenodo.23414183'),lambda t:t+' 10.5281/zenodo.99999999',lambda t:t.replace('10.5281/zenodo.23414184','')]:
   with patch.object(Path,'read_text',lambda p,**kw:change(original(p,**kw))):
    with self.assertRaises(AssertionError):provenance()
 def test_membership_derivation_gate(self):
  import verify_archive as v
  proof=v.read(c.ROOT/'analysis/membership_compression_proof.json')
  original=v.read
  altered=copy.deepcopy(proof);altered[0]['original_sha256']='0'*64
  newline=copy.deepcopy(proof);newline[0]['trailing_newline']=not newline[0]['trailing_newline']
  for changed in [proof[:-1],altered,newline]:
   with patch.object(v,'read',side_effect=lambda p:changed if Path(p).name=='membership_compression_proof.json' else original(p)):
    with self.assertRaises(AssertionError):membership_compression()
 def test_source_json_preservation_gate(self):
  import verify_archive as v
  proof=v.read(c.ROOT/'analysis/data_compression_proof.json.xz');original=v.read
  altered=copy.deepcopy(proof);altered[0]['original_sha256']='0'*64
  for changed in [proof[:-1],altered]:
   with patch.object(v,'read',side_effect=lambda p:changed if Path(p).name=='data_compression_proof.json.xz' else original(p)):
    with self.assertRaises(AssertionError):v.data_compression()
 def test_native_r_version_and_hash_gates(self):
  # Exercise the actual entrypoint gates, replacing ONLY downstream execution.
  # This is a gate test, not a numerical refit or an N/N scientific verdict.
  pins=c.read(c.ROOT/'INPUT_SHA256.json')
  with tempfile.TemporaryDirectory(prefix='.verify-',dir=c.ROOT) as tmp:
   base=Path(tmp)
   for rel in pins:
    dest=base/rel;dest.parent.mkdir(parents=True,exist_ok=True);os.link(c.ROOT/rel,dest)
   shutil.copyfile(c.ROOT/'validate.R',base/'validate.R')
   def run(p,wrong_version=False):
    (base/'INPUT_SHA256.json').write_text(json.dumps(p),encoding='utf-8')
    code='system2<-function(...)0L;'
    if wrong_version:code+='packageVersion<-function(p){if(p=="metafor") package_version("0.0.0") else utils::packageVersion(p)};'
    code+='source("validate.R")'
    return subprocess.run(['Rscript','-e',code],cwd=base,capture_output=True,text=True)
   result=run(pins);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertNotEqual(run(pins,True).returncode,0)
   missing=dict(pins);missing.pop(next(iter(missing)));self.assertNotEqual(run(missing).returncode,0)
   altered=dict(pins);altered['data/corpus.json.xz']='0'*64;self.assertNotEqual(run(altered).returncode,0)
if __name__=='__main__':unittest.main(verbosity=2)

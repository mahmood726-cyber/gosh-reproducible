"""Full fresh reference refit using four independent R processes, no subsetting."""
from pathlib import Path
import os,sys,subprocess,time,concurrent.futures,shutil
from compare_archive import read
ROOT=Path(__file__).resolve().parents[1]
def run(shard):
 with (ROOT/f'.validate-work/worker-{shard}.log').open('wb') as log:
  p=subprocess.run([os.environ.get('GOSH_RSCRIPT',shutil.which('Rscript')),'analysis/refit_worker.R',str(shard),'4'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(f'R shard {shard} failed: see worker log')
 return shard
if __name__=='__main__':
 os.chdir(ROOT);work=ROOT/'.validate-work';work.mkdir(exist_ok=True)
 if (work/'reference').exists():raise RuntimeError('Existing refit output; move .validate-work/reference aside before a fresh run')
 members=work/'memberships';members.mkdir(exist_ok=False)
 proof={r['source']:r for r in read(ROOT/'analysis/membership_compression_proof.json.xz')}
 for p in sorted((ROOT/'results/app-patched').glob('*.json.xz')):
  record=read(p)
  raw='\n'.join(','.join(map(str,point['members'])) for point in record['points']).encode('utf-8')
  if proof[p.relative_to(ROOT).as_posix()]['trailing_newline']:raw+=b'\n'
  (members/(p.name.removesuffix('.json.xz')+'.txt')).write_bytes(raw)
 start=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for shard in pool.map(run,range(4)):print('Finished full refit shard',shard,flush=True)
 print(f'Fresh R refit wall time: {time.monotonic()-start:.3f} seconds',flush=True)
 subprocess.run([sys.executable,'analysis/compare_archive.py','patched','--fresh'],cwd=ROOT,check=True)

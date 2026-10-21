"""Versioned inventories and a disposable, byte-identical v1.0 view."""
from pathlib import Path
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
LAYER = ROOT / 'v1_1'
METADATA = {'README.md', 'CHANGELOG.md', 'CITATION.cff', '.zenodo.json'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def legacy_source(rel):
    return LAYER/'legacy-metadata'/rel if rel in METADATA else ROOT/rel

def check_legacy_pins():
    pins = read(ROOT/'SOURCE_SHA256.json')
    for rel, expected in pins.items():
        assert sha(legacy_source(rel)) == expected, 'V1.0 hash mismatch: '+rel
    print(f'V1.0 SOURCE PINS {len(pins)}/{len(pins)}', flush=True)
    return pins

def layer_files():
    return [p for p in LAYER.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.name != 'SOURCE_SHA256.json'] + [
                ROOT/name for name in sorted(METADATA | {'validate.py', 'verify.py', 'RELEASE_EQUIVALENCE.md'})]

def check_layer():
    pins = read(LAYER/'SOURCE_SHA256.json')
    actual = {p.relative_to(ROOT).as_posix():sha(p) for p in layer_files()}
    assert actual == pins, 'V1.1 inventory/hash mismatch'
    old = read(ROOT/'SOURCE_SHA256.json')
    allowed = set(old) | set(pins) | {'SOURCE_SHA256.json','v1_1/SOURCE_SHA256.json'}
    excluded = {'.git','__pycache__','.pytest_cache','outputs','.validate-work','.slim-work'}
    actual_paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
        and not any(x in excluded or x.startswith('.verify-') for x in p.relative_to(ROOT).parts)}
    assert actual_paths == allowed, 'Archive file coverage mismatch: '+repr(actual_paths ^ allowed)
    prov = read(LAYER/'PROVENANCE.json')
    for item in prov['files']:
        p = LAYER/item['path']
        assert sha(p) == item['sha256'] and p.stat().st_size == item['bytes']
        if item['adaptation'] is None:
            raw = p.read_bytes()
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == item['git_blob']
            assert sha(p) == item['source_sha256']
    assert prov['allmeta_commit'] == '1e3ef389cdfbce7c735c32e2794e67d3cbefb622'
    assert prov['allmeta_release'] == 'v1.8.0' and prov['allmeta_release_doi'] == '10.5281/zenodo.23515177'
    z = read(ROOT/'.zenodo.json')
    assert z['version'] == '1.1.0'
    for name in ['README.md', 'CITATION.cff', '.zenodo.json']:
        text = (ROOT/name).read_text(encoding='utf8')
        assert '<ALLMETA_RELEASE' not in text, 'Unfilled release token: '+name
        assert 'v1.8.0' in text and '10.5281/zenodo.23515177' in text, 'allmeta v1.8.0 tag/DOI missing: '+name
    eq = (ROOT/'RELEASE_EQUIVALENCE.md').read_text(encoding='utf8')
    assert '1cb3f8409c7af75ed41f7e1811f9c502f900fc79' in eq and 'byte-identical' in eq, 'Release equivalence record missing'
    assert 'EXACT R 345842/345842' in eq and 'EXACT METAFOR 182826/182826' in eq, 'Release equivalence counts missing'
    print(f'V1.1 SOURCE PINS {len(pins)}/{len(pins)}', flush=True)

@contextlib.contextmanager
def legacy_view():
    pins = check_legacy_pins()
    # Temp root is fixed inside the archive. Inputs are hard links; derived outputs
    # are copies so the unmodified legacy replay cannot overwrite archived output.
    base = (ROOT / ('.verify-v1-'+uuid.uuid4().hex)).resolve()
    base.mkdir()
    try:
        assert base.parent == ROOT.resolve()
        for rel in list(pins)+['SOURCE_SHA256.json']:
            dest=base/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            os.link(legacy_source(rel),dest)
        shutil.copytree(ROOT/'outputs',base/'outputs',ignore=shutil.ignore_patterns('v1_1'))
        yield base
    finally:
        assert base.parent == ROOT.resolve() and base.name.startswith('.verify-v1-')
        shutil.rmtree(base)

def legacy_checks(actions):
    commands = {
        'verify': [sys.executable,'analysis/verify_archive.py'],
        'safeguards': [sys.executable,'analysis/test_safeguards.py'],
        'replay': [sys.executable,'analysis/compare_archive.py','patched'],
    }
    with legacy_view() as base:
        for action in actions:
            print('V1.0 '+action.upper()+' (unchanged scripts and pinned bytes)',flush=True)
            # Python 3.13 Windows creates mode-0700 temp directories with a
            # restrictive ACL that this host cannot subsequently access.
            # Use normal inherited permissions for temporary directories only;
            # the original verifier/test/replay source and assertions are unchanged.
            bootstrap = (
                "import os,runpy,sys;"
                "original_mkdir=os.mkdir;"
                "os.mkdir=lambda p,mode=0o777,*,dir_fd=None:"
                "original_mkdir(p,0o777 if os.name=='nt' and mode==0o700 else mode,dir_fd=dir_fd);"
                "sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
            )
            script = commands[action][1]
            env = os.environ.copy()
            env['PYTHONPATH'] = str(base/'analysis')+os.pathsep+env.get('PYTHONPATH','')
            subprocess.run([sys.executable,'-c',bootstrap,*commands[action][1:]],cwd=base,env=env,check=True)

if __name__ == '__main__':
    legacy_checks(sys.argv[1:] or ['verify','safeguards','replay'])

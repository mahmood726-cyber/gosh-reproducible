"""One-time lossless migration; retain canonical and byte proofs before unlinking."""
from pathlib import Path
import lzma, gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(raw):
    return json.dumps(json.loads(raw), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')

def migrate():
    records = []
    originals = sorted((ROOT / 'results').rglob('*.json'))
    assert originals, 'No originals to migrate'
    for p in originals:
        raw = p.read_bytes()
        dest = p.with_suffix('.json.xz')
        assert not dest.exists(), dest
        dest.write_bytes(lzma.compress(raw, format=lzma.FORMAT_XZ, preset=6))
        restored = lzma.decompress(dest.read_bytes())
        before, after = digest(canonical(raw)), digest(canonical(restored))
        assert raw == restored and before == after, p
        records.append(dict(file=p.relative_to(ROOT).as_posix(), stored=dest.relative_to(ROOT).as_posix(),
                            original_bytes=len(raw), compressed_bytes=dest.stat().st_size,
                            original_sha256=digest(raw), decompressed_sha256=digest(restored),
                            canonical_original_sha256=before, canonical_decompressed_sha256=after,
                            stored_sha256=digest(dest.read_bytes())))
    proof = ROOT / 'analysis/compression_proof.json'
    proof.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    # The complete proof is durably written before any original is removed.
    assert len(json.loads(proof.read_text(encoding='utf-8'))) == len(originals)
    for p in originals:
        p.unlink()
    print(f'LOSSLESS COMPRESSION: {len(records)} files; every canonical and byte hash identical', flush=True)

def migrate_memberships():
    from compare_archive import read
    records = []
    originals = sorted((ROOT / 'results').rglob('*.txt'))
    assert originals, 'No membership originals to migrate'
    for p in originals:
        raw = p.read_bytes()
        source = p.with_suffix('.json.xz')
        record = read(source)
        regenerated = '\n'.join(','.join(map(str,point['members'])) for point in record['points']).encode('utf-8')
        trailing_newline = raw == regenerated + b'\n'
        if trailing_newline:
            regenerated += b'\n'
        assert raw == regenerated, p
        records.append(dict(file=p.relative_to(ROOT).as_posix(), source=source.relative_to(ROOT).as_posix(),
                            original_bytes=len(raw), trailing_newline=trailing_newline, original_sha256=digest(raw), regenerated_sha256=digest(regenerated)))
    proof = ROOT / 'analysis/membership_compression_proof.json'
    proof.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert len(json.loads(proof.read_text(encoding='utf-8'))) == len(originals)
    for p in originals:
        p.unlink()
    print(f'LOSSLESS MEMBERSHIP DERIVATION: {len(records)} files', flush=True)

if __name__ == '__main__':
    migrate()
    migrate_memberships()
    for name in ['compression_proof.json', 'membership_compression_proof.json']:
        proof = ROOT / 'analysis' / name
        raw = proof.read_bytes()
        dest = proof.with_suffix('.json.xz')
        dest.write_bytes(lzma.compress(raw, preset=6))
        assert lzma.decompress(dest.read_bytes()) == raw
        proof.unlink()

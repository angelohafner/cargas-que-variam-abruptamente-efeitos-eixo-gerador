"""Restore the byte-identical raw video archive from its GitHub transport parts."""
from pathlib import Path
import hashlib
import json
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def restore():
    folder = ROOT / 'data_archives/raw_selected'
    record = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    target = ROOT / 'video/BESS_Load_Smoothing/data/raw_selected.npz'
    if target.exists():
        if target.stat().st_size == record['bytes'] and digest(target) == record['sha256']:
            print('PASS: raw_selected.npz already matches the original archive.')
            return
        raise RuntimeError('Existing raw_selected.npz differs; preserved without replacement.')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='raw_selected_', suffix='.tmp',
                                         dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            whole = hashlib.sha256()
            total = 0
            for part in record['parts']:
                source = folder / part['name']
                if source.resolve().parent != folder.resolve():
                    raise ValueError('Archive part path is outside the expected folder.')
                part_hash = hashlib.sha256()
                part_bytes = 0
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                        output.write(block)
                        whole.update(block)
                        part_hash.update(block)
                        part_bytes += len(block)
                        total += len(block)
                if part_bytes != part['bytes'] or part_hash.hexdigest() != part['sha256']:
                    raise ValueError('Archive part integrity failed: ' + part['name'])
        if total != record['bytes'] or whole.hexdigest() != record['sha256']:
            raise ValueError('Reassembled archive does not match the original SHA-256.')
        os.rename(temporary, target)
        temporary = None
        print(f'PASS: restored {target.relative_to(ROOT).as_posix()} ({total} bytes).')
        print('SHA-256: ' + record['sha256'])
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


if __name__ == '__main__':
    restore()

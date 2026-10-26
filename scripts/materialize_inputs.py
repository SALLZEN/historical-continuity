"""Restore the largest input table byte-for-byte from its transport parts."""
from pathlib import Path
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def materialize(data_dir=None):
    data = Path(data_dir) if data_dir is not None else ROOT/'inputs'
    spec = json.loads((ROOT/'INPUT-STORAGE.json').read_text())
    target = data/spec['table']
    if target.is_file():
        if sha256(target) != spec['sha256']:
            raise ValueError('Existing input table has a different checksum.')
        return target
    missing = [p['file'] for p in spec['parts'] if not (data/p['file']).is_file()]
    if missing:
        raise FileNotFoundError('Full input package required; missing transport parts: '+', '.join(missing))
    temporary = target.with_suffix('.assembling')
    try:
        with temporary.open('wb') as output:
            for part in spec['parts']:
                path = data/part['file']
                if path.stat().st_size != part['bytes'] or sha256(path) != part['sha256']:
                    raise ValueError('Transport-part checksum differs: '+part['file'])
                with path.open('rb') as source:
                    shutil.copyfileobj(source, output)
        if temporary.stat().st_size != spec['bytes'] or sha256(temporary) != spec['sha256']:
            raise ValueError('Assembled input checksum differs.')
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target

if __name__ == '__main__':
    print('Verified input:', materialize().name)

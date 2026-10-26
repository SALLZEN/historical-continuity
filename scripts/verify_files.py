"""Verify the supplied review snapshot against its SHA-256 manifest."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/'MANIFEST.json').read_text())
missing = []
for name, entry in manifest['files'].items():
    path = ROOT/name
    if not path.is_file():
        missing.append(name)
        continue
    if path.stat().st_size != entry['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        sys.exit('Integrity check failed: '+name)
intentional = {name for name in manifest['files'] if name.startswith('inputs/')}
compact = bool(missing) and set(missing) == intentional
if missing and not compact:
    sys.exit('Unexpected missing files: '+', '.join(missing))
print(json.dumps({'passed': True, 'package': 'compact' if compact else 'full',
                  'files_verified': len(manifest['files'])-len(missing),
                  'intentionally_omitted': missing}, indent=2))

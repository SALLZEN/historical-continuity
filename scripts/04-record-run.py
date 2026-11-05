#!/usr/bin/env python3
"""Record the checked reconstruction without recording personal destinations."""
from pathlib import Path
import json
from modules import analysis
root=Path(__file__).resolve().parents[1]
report=json.loads((root/'verification/results.json').read_text())
assert report['passed'] and len(report['rebuilt_tables_compared'])==8
analysis.write_run_record(analysis.initialize(root),verification=report)
print('Checked run recorded')

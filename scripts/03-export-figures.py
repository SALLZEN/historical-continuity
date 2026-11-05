#!/usr/bin/env python3
"""Export the three registered manuscript plots after reconstruction and verification."""
from pathlib import Path
from modules import plotting
root=Path(__file__).resolve().parents[1]
(root/'verification').mkdir(exist_ok=True)
if not (root/'reproduced/analysis/stratum-differences.csv').is_file():
    raise SystemExit('Run ./run.sh --analysis-only before standalone figure export')
for record in plotting.export_all(root):print(record['pdf'],record['width_mm'],record['height_mm'],flush=True)

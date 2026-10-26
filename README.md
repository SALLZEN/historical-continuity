# Computational materials for the EJPS revision

Manuscript: **Historical Continuity as Justification for Dark Matter: How History Becomes an Epistemic Strategy**.

These materials support Sections 3.1 and 3.3 and Appendix A. They contain the retained ADS inputs, analysis code, comparison tables, complete model coefficients, and the manuscript figures. No live ADS query is needed. The original retrieval date is not embedded in the retained input files and has not been reconstructed.

## Two review packages

- **Full package:** includes all five retained input tables. It supports reconstruction from those inputs.
- **Compact package:** includes the complete model dataset and output tables, code, figures, and checks. It supports independent refitting of both reported models, but does not include the raw retained input tables. Use the full package to reconstruct the corpus and citation rates.

## Setup

Use Python 3.11 and the supplied dependency versions. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The requirements contain only the analysis dependencies. R, Quarto, API credentials, Git LFS, and the original research directory are not needed for the revision workflow.

## Inspect and verify

```sh
.venv/bin/python scripts/verify_files.py
.venv/bin/python scripts/check_results.py
```

The first command verifies the supplied files against `MANIFEST.json`. In the compact package it reports the intentionally omitted input files. The second refits both logistic models from `analysis/co-citation-analysis.csv`, compares their coefficients and intervals with the supplied tables, verifies the cohort sizes and comparator rates, and independently checks the reported citation-rate calculations from the verification table.

## Reconstruct from the retained inputs (full package)

```sh
.venv/bin/python scripts/reproduce.py
.venv/bin/python scripts/check_results.py --reproduced reproduced
```

The reconstruction verifies input checksums, writes to `reproduced/analysis/` and `reproduced/figures/`, and leaves the supplied analysis tables and manuscript figures untouched. Alternative locations can be selected with `--data-dir` and `--output-dir`.

## Input storage

The GitHub source archive includes the actual data, without Git LFS pointers. To keep each stored file within GitHub's ordinary file-size limit, `papers.parquet` is transported as `papers.parquet.part01` and `papers.parquet.part02`. `scripts/reproduce.py` automatically restores the original table and verifies its hash. You can also run `python3 scripts/materialize_inputs.py` separately. This changes file transport only; no rows, columns, or values have been removed or altered.

## Contents

- `inputs/`: five retained Parquet tables, unchanged at the byte level. The largest table is stored as two lossless transport parts and is restored automatically before reconstruction. The other four tables are supplied directly.
- `INPUT-STORAGE.json`: part sizes and checksums for restoring the largest table.
- `scripts/materialize_inputs.py`: restoration of that table, verified against its original SHA-256 hash.
- `analysis/`: supplied results, including the complete model sample, two coefficient tables, stratum predictions, historical comparators, field counts, seven linked early references, citation-rate verification, and numerical summary.
- `checks/expected-results.json`: numerical targets and input hashes corresponding to this revision.
- `scripts/reproduce.py`: reconstruction from retained inputs.
- `scripts/check_results.py`: independent refitting and comparison of numerical results.
- `scripts/verify_files.py`: package integrity check using SHA-256.
- `manuscript-figures/`: the exact four image/PDF files used in the current manuscript.
- `MANIFEST.json`: sizes and SHA-256 hashes for the package files.
- `REVIEWER-GUIDE.md`: correspondence between evidence and manuscript claims.

## Figure provenance

The three computational figures in `manuscript-figures/` are the author-edited files actually included by the manuscript. The fourth is the historical Lundmark table image. The co-citation figure's title and horizontal-axis wording have been updated to describe the association; its plotted graphics are unchanged. The reconstruction generates alternative numerical displays (`fig-impact.pdf`, `fig-stratum.pdf`) and copies the supplied field display (`fig-arxiv.pdf`) after verifying its counts. Those rebuilt displays support checking the calculations; they do not reproduce the typography and layout of the author-edited manuscript figures. No newly generated figure is represented as the exact manuscript graphic.

## Interpretation and limits

The complete retrieval corpus, citation-rate cohort, classified citing papers, and model sample have different denominators. The historical comparators are named examples spanning different genres. The seven early sources are recovered citation-graph links, not a complete transcription of the review's bibliography. Reference-list length means linked, date-eligible references. The models estimate associations; they do not establish causal influence, interpretive agreement, reference stabilization, or funding effects. The second model does not test a difference between the two citation-indicator coefficients.

The inherited license designation is retained in `LICENSE`; this preparation assigns no new license. Bibliographic content and historical source material remain part of the evidence and have not been altered for anonymization.

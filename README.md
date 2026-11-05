# Historical Continuity: EJPS computational companion

Manuscript: **Historical Continuity as Justification for Dark Matter: How History Becomes an Epistemic Strategy**.

This private repository supports the retained EJPS evidence with five local input tables, two logistic models, independent checks, a shared-function notebook and approved STIX PDF exports. No ADS credentials or live retrieval are required.

The deposited scientific baseline is [Zenodo 23675367](https://doi.org/10.5281/zenodo.23675367). This is an **unreleased normalized companion update**, based on that unchanged evidence and DAMADI archive v0.1.1. See NORMALIZATION.md and PROVENANCE.json.

## Set up Python

Use Python 3.11. From the repository root:

    ./setup-environment.sh

This creates .runtime/venv and installs requirements.lock.txt, the complete tested Python environment. requirements.txt lists the direct dependency pins. If necessary:

    PYTHON_BIN=/absolute/path/to/python3.11 ./setup-environment.sh

Select an existing compatible environment with DAMADI_PYTHON=/absolute/path/to/python when running the commands below.

## Reconstruct and check the numerical analysis

    ./run.sh --analysis-only

This restores papers.parquet from its transport parts, verifies all five input hashes, reconstructs the 55,140-paper sample, fits both models, independently checks 158,367 annual citation rates and percentiles, compares all eight CSV tables and the numerical summary, and records the checked run.

For the same stages in a fresh private notebook kernel:

    ./run.sh --notebook --analysis-only

The clean source is notebooks/01-reproduce-ejps-analysis.ipynb. It uses the same numbered functions as scripts/reproduce.py. The executed copy goes to executed-notebooks/. No global kernel is installed.

## Export the approved figures

The approved graphics route is verified on macOS and uses R, Quartz, command-line C compiler tools and rsvg-convert. Required/tested R packages are listed in config/r-environment.json. Install these separately; setup-environment.sh installs Python packages only.

    ./run.sh

Or run the full analysis and figure notebook:

    ./run.sh --notebook

After a numerical run, regenerate figures alone with:

    .runtime/venv/bin/python scripts/03-export-figures.py

The readable R constructions are scripts/02-export-waffle.R and scripts/02b-export-stratum.R. When running them manually from an IDE, set the repository root as the working directory and run the waffle stage before the stratum stage; the latter uses its category palette. Bundled STIX Two Text uses Medium for logical bold, with no global font installation.

## Retained and generated material

- inputs/: unchanged source tables. The largest travels as two lossless parts and is restored automatically. No Git LFS or new data download is needed.
- analysis/ and checks/: supplied reference results and numerical targets.
- manuscript-figures/: exact submitted/deposited artwork, retained as evidence.
- figures/: exact approved normalized PDF references and their registry. config/normalized-figures.json pins identities, dimensions and exceptions.
- scripts/modules/: shared analysis and plotting functions; scripts/ contains the readable entry points and retained independent checks.
- notebooks/: clean source notebook.
- reproduced/: newly calculated analysis tables, PDF exports, figure registry and run record.
- verification/ and executed-notebooks/: generated checks and executed notebook, ignored by Git.
- resources/fonts/: bundled static STIX faces, OFL license and attribution.
- MANIFEST.json: checked-in package integrity, excluding the manifest itself and runtime files.

Run in a writable checkout. Reproduction does not overwrite supplied analysis, submitted artwork or approved figure references.

## Existing checking commands

    .runtime/venv/bin/python scripts/verify_files.py
    .runtime/venv/bin/python scripts/check_results.py
    .runtime/venv/bin/python scripts/reproduce.py
    .runtime/venv/bin/python scripts/check_results.py --reproduced reproduced

The direct reproduce.py command now reconstructs numbers only; ./run.sh also performs the independent check, optional approved figure stage and checked-run recording. Its --data-dir and --output-dir options remain available. To restore just the largest table:

    .runtime/venv/bin/python scripts/materialize_inputs.py

## Interpretation and limits

The full corpus, rate cohort, classified review citers and fitted-model sample have different denominators. The seven linked early sources are a recoverable citation-graph subset, not the review's complete bibliography. Reference-list length means linked, date-eligible references. The models establish associations rather than causal influence or interpretive agreement. The second model does not test a difference between coefficients.

The original ADS retrieval timestamp is not embedded in the retained tables. Historical comparators are named examples, not an exhaustive genre population. These runs reproduce the retained calculation without adding an independent validation sample. Submitted graphics remain distinguishable from normalized PDF exports.

The inherited LICENSE designation is unchanged. Font licensing is supplied under resources/fonts/OFL.txt. REVIEWER-GUIDE.md retains the deposited evidence-to-claim correspondence.

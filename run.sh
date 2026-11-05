#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
WORKSPACE_DIR=$(pwd)
PYTHON_EXECUTABLE=$(printenv DAMADI_PYTHON || true)
[ -n "$PYTHON_EXECUTABLE" ] || PYTHON_EXECUTABLE="$WORKSPACE_DIR/.runtime/venv/bin/python"
[ -x "$PYTHON_EXECUTABLE" ] || { printf '%s\n' 'Run ./setup-environment.sh first, or set DAMADI_PYTHON to a prepared Python 3.11 interpreter.' >&2; exit 1; }
MODE=full
NOTEBOOK=0
for option in "$@"; do
  case "$option" in
    --analysis-only) MODE=analysis ;;
    --notebook) NOTEBOOK=1 ;;
    *) printf '%s\n' 'Usage: ./run.sh [--notebook] [--analysis-only]' >&2; exit 2 ;;
  esac
done
if [ "$MODE" = full ]; then
  [ "$(uname -s)" = Darwin ] || { printf '%s\n' 'Approved figures require macOS Quartz; use --analysis-only for numerical reconstruction.' >&2; exit 1; }
  for program in Rscript rsvg-convert; do
    command -v "$program" >/dev/null 2>&1 || { printf '%s\n' "Missing $program. See README.md, or use --analysis-only." >&2; exit 1; }
  done
fi
mkdir -p .runtime/matplotlib verification
export MPLCONFIGDIR="$WORKSPACE_DIR/.runtime/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
if [ "$MODE" = analysis ]; then export DAMADI_ANALYSIS_ONLY=1; else export DAMADI_ANALYSIS_ONLY=0; fi
if [ "$NOTEBOOK" = 1 ]; then exec "$PYTHON_EXECUTABLE" scripts/execute-notebook.py; fi
"$PYTHON_EXECUTABLE" scripts/reproduce.py
"$PYTHON_EXECUTABLE" scripts/check_results.py --reproduced reproduced --report verification/results.json
if [ "$MODE" = full ]; then "$PYTHON_EXECUTABLE" scripts/03-export-figures.py; fi
"$PYTHON_EXECUTABLE" scripts/04-record-run.py

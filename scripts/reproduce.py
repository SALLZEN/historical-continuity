"""Reconstruct the EJPS evidence through shared, numbered analysis stages."""
from pathlib import Path
import argparse
from modules import analysis

def reconstruct(root, data_dir=None, output_dir=None):
    state = analysis.initialize(root, data_dir=data_dir, output_dir=output_dir)
    print('1. Five input hashes verified', flush=True)
    analysis.build_model_sample(state)
    print('2. Model sample:', len(state['cohort']), flush=True)
    analysis.fit_models_and_strata(state)
    print('3. Both logistic models fitted', flush=True)
    analysis.verify_citation_rates(state)
    print('4. Annual rates verified:', len(state['rates']), flush=True)
    analysis.write_counts_and_summary(state)
    analysis.write_run_record(state)
    print('5. Reconstructed tables:', state['analysis_dir'], flush=True)
    return state

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    reconstruct(Path(__file__).resolve().parents[1], args.data_dir, args.output_dir)

"""Refit both reported models and verify the numerical evidence for the revision."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reproduced', type=Path, help='Also compare tables rebuilt from retained inputs.')
parser.add_argument('--report', type=Path, help='Write a JSON verification report.')
args = parser.parse_args()
expected = json.loads((ROOT/'checks/expected-results.json').read_text())
a = ROOT/'analysis'
c = pd.read_csv(a/'co-citation-analysis.csv')
assert c.bibcode.is_unique and len(c) == expected['analysis_n']
assert int(c.cites_bh.sum()) == expected['analysis_bh_citers']
assert c.year.between(2018, 2025).all() and (c.n_linked_refs >= 1).all()
assert set(c.cites_bh.unique()) == {0, 1}
c['log_refs'] = np.log1p(c.n_linked_refs)
models = {}
for outcome in ['bh_early', 'other_early']:
    c[outcome] = c[outcome].astype(int)
    fit = smf.glm(outcome+' ~ cites_bh + log_refs + C(stratum)', data=c,
                  family=sm.families.Binomial()).fit(maxiter=100)
    assert fit.converged
    saved = pd.read_csv(a/(outcome+'-coefficients.csv'), index_col=0)
    assert list(saved.index) == list(fit.params.index)
    np.testing.assert_allclose(fit.params, saved['Coef.'], rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(fit.bse, saved['Std.Err.'], rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(fit.conf_int(), saved[['[0.025', '0.975]']], rtol=1e-9, atol=1e-10)
    estimate = float(np.exp(fit.params['cites_bh']))
    interval = np.exp(fit.conf_int().loc['cites_bh']).tolist()
    delta = float((fit.predict(c.assign(cites_bh=1)) - fit.predict(c.assign(cites_bh=0))).mean())
    target = expected['results'][outcome]
    np.testing.assert_allclose(estimate, target['odds_ratio'], rtol=1e-9)
    np.testing.assert_allclose(interval, target['wald_ci95'], rtol=1e-9)
    np.testing.assert_allclose(delta, target['mean_standardized_difference'], rtol=1e-9)
    models[outcome] = {'odds_ratio': estimate, 'wald_ci95': interval,
                       'mean_standardized_difference': delta, 'converged': True}
    if outcome == 'bh_early':
        strata = pd.read_csv(a/'stratum-differences.csv')
        counts = c.groupby('stratum').agg(mean_log_refs=('log_refs', 'mean'),
                     n_bh=('cites_bh', 'sum'), n_total=('bibcode', 'size'))
        for row in strata.itertuples():
            values = counts.loc[row.stratum]
            np.testing.assert_allclose(row.mean_log_refs, values.mean_log_refs)
            assert row.n_bh == values.n_bh and row.n_total == values.n_total
            assert row.n_nonbh == row.n_total - row.n_bh and row.n_bh >= 10 and row.n_nonbh >= 100
        differences = (fit.predict(strata.assign(cites_bh=1, log_refs=strata.mean_log_refs))
                     - fit.predict(strata.assign(cites_bh=0, log_refs=strata.mean_log_refs)))
        np.testing.assert_allclose(differences, strata.difference, rtol=1e-9)

rates = pd.read_csv(a/'citation-rate-verification.csv')
assert rates.bibcode.is_unique and len(rates) == expected['rate_records']
assert (rates.years_exposed == rates.latest_metric_year-rates.publication_year+1).all()
np.testing.assert_allclose(rates.total_citations/rates.years_exposed, rates.avg_citations_per_year, rtol=1e-9)
np.testing.assert_allclose(rates.recomputed_rate, rates.avg_citations_per_year, rtol=1e-9)
rates['independent_percentile'] = rankdata(rates.avg_citations_per_year, method='average')/len(rates)*100
bh = rates.set_index('bibcode').loc['2018RvMP...90d5002B']
np.testing.assert_allclose(bh.avg_citations_per_year, expected['bh_rate'])
np.testing.assert_allclose(bh.independent_percentile, expected['bh_percentile'])
comparators = pd.read_csv(a/'historical-comparators.csv')
for row in comparators.itertuples():
    matching = rates.set_index('bibcode').loc[row.bibcode]
    np.testing.assert_allclose(row.avg_citations_per_year, matching.avg_citations_per_year)
    np.testing.assert_allclose(row.percentile, matching.independent_percentile)
fields = pd.read_csv(a/'bh-citers-by-field.csv').set_index('arxiv_category').papers
assert fields.sum() == expected['classified_bh_citers'] == 551
assert fields.loc[['high-energy physics','astrophysics','general relativity and quantum cosmology','physics']].tolist() == [233,180,76,48]
assert len(pd.read_csv(a/'bh-linked-early-references.csv')) == expected['linked_early_reference_count'] == 7

compared = []
if args.reproduced:
    for p in sorted(a.glob('*.csv')):
        rebuilt = args.reproduced/'analysis'/p.name
        pd.testing.assert_frame_equal(pd.read_csv(p), pd.read_csv(rebuilt), check_exact=False,
                                      rtol=1e-9, atol=1e-10)
        compared.append(p.name)
    summary = json.loads((args.reproduced/'analysis/bibliometric-summary.json').read_text())
    assert summary == expected, 'Rebuilt numerical summary differs from the revision targets.'
report = {'passed': True, 'model_records': len(c), 'bh_model_citers': int(c.cites_bh.sum()),
          'rate_records_verified': len(rates), 'bh_rate': float(bh.avg_citations_per_year),
          'bh_percentile': float(bh.independent_percentile), 'models': models,
          'rebuilt_tables_compared': compared}
if args.report:
    args.report.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))

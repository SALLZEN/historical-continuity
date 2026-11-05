"""EJPS revision reconstruction in readable stages; numerical statements retained from reproduce.py."""
from pathlib import Path
import hashlib,json,warnings,sys,importlib.metadata as metadata
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import rankdata
BH='2018RvMP...90d5002B'

def find_workspace(start):
    start=Path(start).resolve()
    for candidate in [start,*start.parents]:
        marker=candidate/'config/workspace.json'
        if marker.is_file() and json.loads(marker.read_text()).get('entry_code')=='E.03--MS-DA-CR':return candidate
    raise FileNotFoundError('No E.03 computational workspace marker above this location')

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()

def initialize(root,output_dir=None,data_dir=None):
    root=Path(root).resolve()
    expected=json.loads((root/'checks/expected-results.json').read_text())
    out=Path(output_dir).resolve() if output_dir else root/'reproduced'
    data=Path(data_dir).resolve() if data_dir else root/'inputs'
    protected=[root/name for name in ['analysis','inputs','checks','scripts','config','resources','figures','manuscript-figures','.git']]
    if out==root or any(out==p or p in out.parents for p in protected) or out==data or data in out.parents:
        raise ValueError('Choose a separate reconstruction directory; supplied evidence is protected')
    from materialize_inputs import materialize
    materialize(data)
    checked={}
    for name,entry in expected['inputs'].items():
        path=data/(name+'.parquet');actual=sha256(path)
        if actual!=entry['sha256']:raise ValueError('Input checksum differs: '+path.name)
        checked[name]=actual
    (out/'analysis').mkdir(parents=True,exist_ok=True)
    (out/'figures').mkdir(exist_ok=True)
    return {'root':root,'data':data,'output_root':out,'analysis_dir':out/'analysis','figure_dir':out/'figures','expected':expected,'checked_inputs':checked}


def build_model_sample(ctx):
    OUT=ctx['analysis_dir'];DATA=ctx['data']
    def read(name,**kwargs):return pd.read_parquet(DATA/(name+'.parquet'),**kwargs)
    papers=read('papers',columns=['bibcode','year','doctype','title'])
    classes=read('paper_arxiv_classes').sort_values(['bibcode','class_pos']).drop_duplicates('bibcode')
    meta=papers.merge(classes[['bibcode','arxiv_class','arxiv_category']],on='bibcode',how='left',validate='one_to_one')
    cites=read('paper_citations',columns=['bibcode','citing_bibcode']).drop_duplicates()
    citers=set(cites.loc[cites.bibcode.eq(BH),'citing_bibcode'])
    refyears=pd.to_numeric(cites.loc[cites.citing_bibcode.eq(BH),'bibcode'].str[:4],errors='coerce')
    bh_refs=cites.loc[cites.citing_bibcode.eq(BH)].copy()
    bh_refs['ref_year']=pd.to_numeric(bh_refs.bibcode.str[:4],errors='coerce')
    early=set(bh_refs.loc[bh_refs.ref_year.between(1800,1959),'bibcode'])
    pd.DataFrame({'bibcode':sorted(early)}).merge(papers[['bibcode','title']],how='left').to_csv(OUT/'bh-linked-early-references.csv',index=False)
    cohort=meta.loc[meta.year.between(2018,2025)&meta.doctype.isin(['article','eprint'])&meta.arxiv_category.notna()].copy()
    cohort['cites_bh']=cohort.bibcode.isin(citers).astype(int)
    refs=cites[cites.citing_bibcode.isin(cohort.bibcode)].copy()
    refs['ref_year']=pd.to_numeric(refs.bibcode.str[:4],errors='coerce')
    refs=refs.loc[refs.ref_year.between(1800,2025)]
    refs['in_early']=refs.bibcode.isin(early)
    refs['other_early']=refs.ref_year.lt(1960)&~refs.in_early
    signals=refs.groupby('citing_bibcode').agg(n_linked_refs=('bibcode','size'),bh_early=('in_early','max'),other_early=('other_early','max')).reset_index()
    cohort=cohort.merge(signals,left_on='bibcode',right_on='citing_bibcode',how='inner',validate='one_to_one')
    keep=['astrophysics','high-energy physics','general relativity and quantum cosmology','physics','nuclear physics','quantum physics']
    cohort=cohort[cohort.arxiv_category.isin(keep)].copy()
    cohort['year_bin']=pd.cut(cohort.year,[2018,2020,2022,2024,2026],right=False,labels=['2018–2019','2020–2021','2022–2023','2024–2025']).astype(str)
    cohort['stratum']=cohort.year_bin+' / '+cohort.arxiv_category
    cohort['log_refs']=np.log1p(cohort.n_linked_refs)
    cohort[['bibcode','year','arxiv_category','cites_bh','n_linked_refs','bh_early','other_early','stratum']].to_csv(OUT/'co-citation-analysis.csv',index=False)
    ctx['papers']=papers
    ctx['meta']=meta
    ctx['cites']=cites
    ctx['citers']=citers
    ctx['early']=early
    ctx['cohort']=cohort
    ctx['keep']=keep
    return ctx


def fit_models_and_strata(ctx):
    OUT=ctx['analysis_dir'];DATA=ctx['data']
    def read(name,**kwargs):return pd.read_parquet(DATA/(name+'.parquet'),**kwargs)
    cohort=ctx['cohort']
    results={};models={}
    for outcome in ['bh_early','other_early']:
     cohort[outcome]=cohort[outcome].astype(int)
     with warnings.catch_warnings(record=True) as caught:
      model=smf.glm(outcome+' ~ cites_bh + log_refs + C(stratum)',data=cohort,family=sm.families.Binomial()).fit(maxiter=100)
     models[outcome]=model
     beta=float(model.params['cites_bh']);ci=model.conf_int().loc['cites_bh']
     a=cohort.assign(cites_bh=1);b=cohort.assign(cites_bh=0)
     diff=model.predict(a)-model.predict(b)
     results[outcome]={'odds_ratio':float(np.exp(beta)),'wald_ci95':[float(np.exp(ci.iloc[0])),float(np.exp(ci.iloc[1]))],'mean_standardized_difference':float(diff.mean()),'median_standardized_difference':float(diff.median()),'converged':bool(model.converged),'warnings':sorted(set(str(x.message) for x in caught))}
     model.summary2().tables[1].to_csv(OUT/(outcome+'-coefficients.csv'))
    strata=cohort.groupby(['year_bin','arxiv_category','stratum']).agg(mean_log_refs=('log_refs','mean'),n_bh=('cites_bh','sum'),n_total=('cites_bh','size')).reset_index()
    strata['n_nonbh']=strata.n_total-strata.n_bh
    strata=strata[(strata.n_bh>=10)&(strata.n_nonbh>=100)].copy()
    strata['difference']=models['bh_early'].predict(strata.assign(cites_bh=1,log_refs=strata.mean_log_refs))-models['bh_early'].predict(strata.assign(cites_bh=0,log_refs=strata.mean_log_refs))
    strata.to_csv(OUT/'stratum-differences.csv',index=False)
    ctx['cohort']=cohort
    ctx['results']=results
    ctx['models']=models
    ctx['strata']=strata
    return ctx


def verify_citation_rates(ctx):
    OUT=ctx['analysis_dir'];DATA=ctx['data']
    def read(name,**kwargs):return pd.read_parquet(DATA/(name+'.parquet'),**kwargs)
    papers=ctx['papers']
    rates=read('avg_citations_result');assert rates.bibcode.is_unique
    # Independently verify the stored rates against annual citation metrics, using
    # the original notebook's inclusive publication-to-latest-metric convention.
    annual=pd.read_parquet(DATA/'paper_metrics_long.parquet',filters=[('metric','==','citations')])
    annual=annual.merge(papers[['bibcode','year']],on='bibcode',how='left',validate='many_to_one')
    annual=annual[annual.metric_year.ge(annual.year)]
    rate_check=annual.groupby('bibcode').agg(publication_year=('year','first'),latest_metric_year=('metric_year','max'),total_citations=('value','sum'))
    rate_check['years_exposed']=rate_check.latest_metric_year-rate_check.publication_year+1
    rate_check['recomputed_rate']=rate_check.total_citations/rate_check.years_exposed
    assert set(rate_check.index)==set(rates.bibcode)
    rate_check=rate_check.join(rates.set_index('bibcode')[['avg_citations_per_year']],validate='one_to_one')
    assert np.allclose(rate_check.recomputed_rate,rate_check.avg_citations_per_year)
    rate_check.to_csv(OUT/'citation-rate-verification.csv')
    del annual
    expected=rankdata(rates.avg_citations_per_year.to_numpy(),method='average')/len(rates)*100
    assert np.allclose(expected,rates.percentile)
    target=rates.loc[rates.bibcode.eq(BH)].iloc[0]
    pos=rates[rates.avg_citations_per_year.gt(0)].sort_values('avg_citations_per_year')
    ctx['rates']=rates
    ctx['rate_check']=rate_check
    ctx['target']=target
    ctx['pos']=pos
    return ctx


def write_counts_and_summary(ctx):
    OUT=ctx['analysis_dir'];DATA=ctx['data']
    def read(name,**kwargs):return pd.read_parquet(DATA/(name+'.parquet'),**kwargs)
    papers=ctx['papers']
    meta=ctx['meta']
    citers=ctx['citers']
    early=ctx['early']
    cohort=ctx['cohort']
    results=ctx['results']
    rate_check=ctx['rate_check']
    rates=ctx['rates']
    target=ctx['target']
    pos=ctx['pos']
    circulation=meta[meta.bibcode.isin(citers)&meta.arxiv_category.notna()].groupby('arxiv_category').size().sort_values(ascending=False)
    circulation.to_csv(OUT/'bh-citers-by-field.csv',header=['papers'])
    assert circulation.loc[['high-energy physics','astrophysics','general relativity and quantum cosmology','physics']].tolist()==[233,180,76,48]
    # Comparators are named historical treatments, not an exhaustive genre population.
    comparator_ids=[BH,'2017NatAs...1E..59D','2010dmp..book.....S','1999PASP..111..657V']
    comparators=meta[meta.bibcode.isin(comparator_ids)].merge(rates,on='bibcode',how='left')
    comparators[['bibcode','title','year','avg_citations_per_year','percentile']].to_csv(OUT/'historical-comparators.csv',index=False)
    inputs={n:{'path':'inputs/'+n+'.parquet','sha256':hashlib.sha256((DATA/(n+'.parquet')).read_bytes()).hexdigest()} for n in ['papers','paper_citations','paper_arxiv_classes','paper_metrics_long','avg_citations_result']}
    summary={'full_corpus':len(papers),'year_range':[int(papers.year.min()),int(papers.year.max())],'rate_records':len(rates),'rate_records_verified_from_annual_metrics':len(rate_check),'rate_max_absolute_error':float((rate_check.recomputed_rate-rate_check.avg_citations_per_year).abs().max()),'positive_rate_records':len(pos),'bh_rate':float(target.avg_citations_per_year),'bh_percentile':float(target.percentile),'bh_graph_citers':len(citers),'classified_bh_citers':int(circulation.sum()),'linked_early_reference_count':len(early),'analysis_n':len(cohort),'analysis_bh_citers':int(cohort.cites_bh.sum()),'analysis_outcome_counts':cohort.groupby('cites_bh')[['bh_early','other_early']].agg(['sum','mean']).to_json(),'results':results,'inputs':inputs,'limits':['Retained linked references are incomplete relative to the full bibliographies.','Reference-list length means linked, date-eligible references, not the full reference list.','Citation overlap is an association, not interpretive adherence or causal impact.','No original ADS retrieval timestamp is embedded in these parquet inputs.']}
    (OUT/'bibliometric-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    ctx['circulation']=circulation
    ctx['comparators']=comparators
    ctx['summary']=summary
    return ctx


def write_run_record(ctx,verification=None):
    record={'entry_code':'E.03--MS-DA-CR','edition':'0.1.0','companion_status':'unreleased normalized update','inputs':ctx['checked_inputs'],'software':{n:metadata.version(n) for n in ['numpy','pandas','pyarrow','scipy','statsmodels','matplotlib']},'summary_file':'analysis/bibliometric-summary.json','verification':verification,'scope':'Reconstruction from retained revision inputs; no live retrieval or new analytical choices'}
    path=ctx['output_root']/'run-record.json';path.write_text(json.dumps(record,indent=2)+'\n');return record

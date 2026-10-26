"""Reconcile the EJPS citation evidence against the retained author data.

Reads the bundled retained tables without modifying them. Writes to a separate
output directory, leaving the checked-in evidence and manuscript figures intact. The seven-source set is the recoverable citation-graph subset, not
an exhaustive transcription of the review's early bibliography.
"""
from pathlib import Path
import hashlib,json,warnings,os,argparse,tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'ejps-matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME',str(Path(tempfile.gettempdir())/'ejps-font-cache'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import rankdata
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Reproduce the EJPS revision evidence from the retained inputs.')
parser.add_argument('--data-dir',type=Path,default=ROOT/'inputs')
parser.add_argument('--output-dir',type=Path,default=ROOT/'reproduced')
args=parser.parse_args()
DATA=args.data_dir.resolve()
from materialize_inputs import materialize
materialize(DATA)
OUT=args.output_dir.resolve()/'analysis';FIG=args.output_dir.resolve()/'figures'
if OUT==ROOT/'analysis' or FIG==ROOT/'manuscript-figures':
 parser.error('Choose a separate output directory to preserve the supplied evidence.')
OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
expected_inputs=json.loads((ROOT/'checks/expected-results.json').read_text())['inputs']
for name,entry in expected_inputs.items():
 path=DATA/(name+'.parquet')
 if not path.is_file():
  parser.error('Missing '+name+'.parquet; use the full review archive for reconstruction from retained inputs.')
 if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
  parser.error('Input checksum differs for '+name+'.parquet')
BH='2018RvMP...90d5002B'
def read(n,**kw):return pd.read_parquet(DATA/(n+'.parquet'),**kw)
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
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42})
colors={'astrophysics':'#a33773','high-energy physics':'#237f85','general relativity and quantum cosmology':'#6266b7','physics':'#ed8e36','nuclear physics':'#777777','quantum physics':'#999999'}
fig,axes=plt.subplots(1,4,figsize=(7.5,3.5),sharex=True,sharey=True)
years=['2018–2019','2020–2021','2022–2023','2024–2025'];shown=keep[:4]
for ax,year in zip(axes,years):
 for yi,category in enumerate(shown):
  row=strata[(strata.year_bin==year)&(strata.arxiv_category==category)]
  if len(row):ax.scatter(row.difference*100,[yi],s=row.n_bh*5,color=colors[category],edgecolor='white',linewidth=.5,zorder=3)
 ax.axvline(0,ls='--',lw=.7,color='#888888');ax.set_title(year,fontsize=10);ax.grid(axis='x',color='#e6e6e6');ax.set_axisbelow(True)
 ax.set_xlim(-.5,max(10,float(strata.difference.max()*100)+1));ax.set_xticks([0,5,10]);ax.spines[['top','right','left']].set_visible(False)
axes[0].set_yticks(range(4),['Astrophysics','High-energy\nphysics','General relativity\nand quantum cosmology','Physics']);axes[0].invert_yaxis()
fig.supxlabel('Adjusted probability difference (percentage points)',fontsize=11,y=.03)
fig.suptitle('Co-citation association within year and field strata',fontsize=11)
fig.text(.6,.14,'Circle area: number of papers citing the review',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.18,1,.94));fig.savefig(FIG/'fig-stratum.pdf');plt.close(fig)
# Retain the original rate definition and cohort, while removing plotting jitter.
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
fig,ax=plt.subplots(figsize=(7.2,3.6));ax.plot(pos.avg_citations_per_year,pos.percentile,color='#e39b43',lw=1.5)
ax.scatter([target.avg_citations_per_year],[target.percentile],s=40,color='#ac582c',zorder=4)
ax.axvline(pos.avg_citations_per_year.mean(),ls='--',color='#39876b',lw=1,label='Mean among positive-rate records')
ax.axvline(pos.avg_citations_per_year.median(),ls='--',color='#555555',lw=1,label='Median among positive-rate records')
ax.annotate('Bertone and Hooper (2018)\n'+f'{target.avg_citations_per_year:.2f} citations/year; percentile {target.percentile:.2f}',xy=(target.avg_citations_per_year,target.percentile),xytext=(3,59),arrowprops={'arrowstyle':'->','color':'#666666'},bbox={'facecolor':'white','edgecolor':'#aaaaaa','boxstyle':'round,pad=.4'},fontsize=10)
ax.set_xscale('log');ax.set_xlim(max(.01,float(pos.avg_citations_per_year.min())),max(550,float(pos.avg_citations_per_year.max())));ax.set_ylim(0,102)
ax.set_xlabel('Average citations per year (logarithmic scale)',fontsize=11);ax.set_ylabel('Percentile within citation-metric records',fontsize=11);ax.tick_params(labelsize=10);ax.grid(alpha=.2);ax.legend(fontsize=9,loc='lower right');fig.tight_layout();fig.savefig(FIG/'fig-impact.pdf');plt.close(fig)
# Broad-field circulation: preserve the primary-class convention, report all fields.
circulation=meta[meta.bibcode.isin(citers)&meta.arxiv_category.notna()].groupby('arxiv_category').size().sort_values(ascending=False)
circulation.to_csv(OUT/'bh-citers-by-field.csv',header=['papers'])
# Preserve the author-designed four-field display after checking its counts.
import shutil
assert circulation.loc[['high-energy physics','astrophysics','general relativity and quantum cosmology','physics']].tolist()==[233,180,76,48]
shutil.copy2(ROOT/'manuscript-figures/arxiv-waffle-plot.pdf',FIG/'fig-arxiv.pdf')
# Comparators are named historical treatments, not an exhaustive genre population.
comparator_ids=[BH,'2017NatAs...1E..59D','2010dmp..book.....S','1999PASP..111..657V']
comparators=meta[meta.bibcode.isin(comparator_ids)].merge(rates,on='bibcode',how='left')
comparators[['bibcode','title','year','avg_citations_per_year','percentile']].to_csv(OUT/'historical-comparators.csv',index=False)
inputs={n:{'path':'inputs/'+n+'.parquet','sha256':hashlib.sha256((DATA/(n+'.parquet')).read_bytes()).hexdigest()} for n in ['papers','paper_citations','paper_arxiv_classes','paper_metrics_long','avg_citations_result']}
summary={'full_corpus':len(papers),'year_range':[int(papers.year.min()),int(papers.year.max())],'rate_records':len(rates),'rate_records_verified_from_annual_metrics':len(rate_check),'rate_max_absolute_error':float((rate_check.recomputed_rate-rate_check.avg_citations_per_year).abs().max()),'positive_rate_records':len(pos),'bh_rate':float(target.avg_citations_per_year),'bh_percentile':float(target.percentile),'bh_graph_citers':len(citers),'classified_bh_citers':int(circulation.sum()),'linked_early_reference_count':len(early),'analysis_n':len(cohort),'analysis_bh_citers':int(cohort.cites_bh.sum()),'analysis_outcome_counts':cohort.groupby('cites_bh')[['bh_early','other_early']].agg(['sum','mean']).to_json(),'results':results,'inputs':inputs,'limits':['Retained linked references are incomplete relative to the full bibliographies.','Reference-list length means linked, date-eligible references, not the full reference list.','Citation overlap is an association, not interpretive adherence or causal impact.','No original ADS retrieval timestamp is embedded in these parquet inputs.']}
(OUT/'bibliometric-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['inputs','analysis_outcome_counts']},indent=2))
print(comparators[['bibcode','title','avg_citations_per_year']].to_string(index=False))

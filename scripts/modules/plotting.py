"""STIX presentation exports from verified revision values; no model changes."""
from pathlib import Path
import json,subprocess,os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from . import analysis
from .damadi_plotting import configure_fonts,save_pdf

PROFILES={'fig-citation-impact':{'width_mm':156,'height_mm':90},'fig-cocitation-strata':{'width_mm':177.8,'height_mm':101.6},'fig-arxiv-citing-patterns':{'width_mm':156,'height_mm':156*5.68/7.25}}

def export_impact(root,out):
    rates=pd.read_parquet(root/'inputs/avg_citations_result.parquet')
    positive=rates[rates.avg_citations_per_year.gt(0)].copy()
    target=positive.loc[positive.bibcode.eq(analysis.BH)].iloc[0]
    rng=np.random.default_rng(42)
    y_jitter=rng.uniform(-1.5,1.5,len(positive));x_jitter=rng.uniform(-1.5,1.5,len(positive))
    fig,ax=plt.subplots(figsize=(156/25.4,90/25.4))
    ax.scatter(positive.avg_citations_per_year+x_jitter,positive.percentile+y_jitter,alpha=.15,color='#FFA239',marker='2',linewidths=.2,edgecolors='black',s=10)
    ax.scatter([target.avg_citations_per_year],[target.percentile],color='#E37434',s=50,marker='o',edgecolors='black',linewidths=.5,label=analysis.BH,zorder=5)
    ax.axvline(positive.avg_citations_per_year.mean(),color='#2cb869',linestyle='--',linewidth=1,label='Overall mean')
    ax.axvline(positive.avg_citations_per_year.median(),color='#333333',linestyle='--',linewidth=1,label='Overall median')
    ax.annotate(f'Bibcode: {analysis.BH}\nAvg cit/year: {target.avg_citations_per_year:.2f}\nPercentile: {target.percentile:.1f}',xy=(target.avg_citations_per_year,target.percentile),xytext=(.51,.57),textcoords='axes fraction',fontsize=9,color='#333333',bbox={'boxstyle':'round','facecolor':'white','edgecolor':'#777777','linewidth':.6},arrowprops={'color':'#777777','arrowstyle':'->','linewidth':.6})
    ax.set_xscale('symlog');ax.set_xlim(1,550)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v,p:f'{int(v):,}' if v>=1 else ''))
    ax.set_xticks([1,2,5,10,25,50,100,200,500]);ax.tick_params(labelsize=9)
    ax.grid(True,linestyle='--',alpha=.3)
    ax.set_title('Percentile vs. average citations per year',fontsize=11)
    ax.set_xlabel('Average citations per year (symlog)',fontsize=10);ax.set_ylabel('Percentile',fontsize=10)
    ax.legend(fontsize=9,loc='lower right',framealpha=.95)
    fig.tight_layout(pad=.7);path=save_pdf(fig,out/'fig-citation-impact.pdf',156,90);plt.close(fig)
    return {'figure':'fig-citation-impact','pdf':path.name,'source':'Retained annual-rate table; original notebook scatter construction','seed':42,'jitter_order':'y followed by x, uniform -1.5 to 1.5; unchanged from retained notebook','positive_rate_records':len(positive),'percentile_denominator':len(rates),'target_rate':float(target.avg_citations_per_year),'target_percentile':float(target.percentile),**PROFILES['fig-citation-impact']}

def export_strata(root,out):
    # Use the author's R/ggplot specification and Quartz export directly.
    result=subprocess.run(['Rscript','--vanilla',str(root/'scripts/02b-export-stratum.R'),str(root)],cwd=root,capture_output=True,text=True)
    (root/'verification/stratum-export.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('Author-specified stratum export failed; see verification/stratum-export.log')
    data=pd.read_csv(root/'reproduced/analysis/stratum-differences.csv')
    return {'figure':'fig-cocitation-strata','pdf':'fig-cocitation-strata.pdf','source':'Author-supplied ggplot specification; verified revision predictions, no refit','displayed_strata':len(data),'model_recalculation_for_presentation':False,'export_backend':'Quartz PDF','size_scale':{'ggplot_range_mm':[5,15],'legend_title':'Review-citing papers:'},'minimum_normal_text_pt':8.5,'manuscript_inclusion_width_mm':156,**PROFILES['fig-cocitation-strata']}

def validate_waffle_pdf(root):
    from pypdf import PdfReader
    root=Path(root)
    path=root/'reproduced/figures/fig-arxiv-citing-patterns.pdf'
    reader=PdfReader(path);assert len(reader.pages)==1
    page=reader.pages[0];text=page.extract_text() or ''
    lines={line.strip() for line in text.splitlines()}
    forbidden=lines.intersection({'x','y','5','10','15'})
    assert not forbidden, f'Upper waffle coordinate axes returned: {sorted(forbidden)}'
    joined=' '.join(text.split())
    for label in ['Category totals','Subclass composition','Citations','48','76','180','233']:
        assert label in joined,label
    actual=[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72]
    expected=[156,156*5.68/7.25]
    assert np.allclose(actual,expected,atol=.02)
    report={'passed':True,'upper_panel_axes_absent':True,'lower_panel_axes_retained':True,'counts':[48,76,180,233],'dimensions_mm':actual,'baseline_aspect_inches':[7.25,5.68]}
    (root/'verification/waffle-display-check.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def export_all(root):
    root=Path(root).resolve();analysis.initialize(root)  # Verify input identities before any export.
    out=root/'reproduced/figures';out.mkdir(parents=True,exist_ok=True)
    configure_fonts(root/'resources/fonts')
    records=[export_impact(root,out)]
    result=subprocess.run(['Rscript','--vanilla',str(root/'scripts/02-export-waffle.R'),str(root)],cwd=root,capture_output=True,text=True)
    (root/'verification/waffle-export.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('R field-display export failed; see verification/waffle-export.log')
    validate_waffle_pdf(root)
    records.append(export_strata(root,out))
    records.append({'figure':'fig-arxiv-citing-patterns','pdf':'fig-arxiv-citing-patterns.pdf','source':'Author stepwise R waffle/bar construction, using the verified frozen primary-class counts','displayed_counts':{'high-energy physics':233,'astrophysics':180,'general relativity and quantum cosmology':76,'physics':48},'classified_records':551,'outside_display':14,**PROFILES['fig-arxiv-citing-patterns']})
    for row in records:
        row.update(presentation_revision='0.1.6',text_font='Bundled STIX Two Text',emphasis='Medium',background='white')
        row.setdefault('minimum_normal_text_pt',9)
    (root/'reproduced/figure-registry.json').write_text(json.dumps(records,indent=2)+'\n')
    return records

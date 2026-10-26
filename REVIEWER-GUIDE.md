# Evidence guide

| Manuscript location | Claim or calculation | Inspect |
| --- | --- | --- |
| Section 3.1; Appendix A | 201,272 retrieved records; 158,367 eligible rate records | `analysis/bibliometric-summary.json`; `analysis/citation-rate-verification.csv` |
| Section 3.1 | B&H: 122.33 citations per year; percentile 99.87 | `analysis/bibliometric-summary.json`; rate table |
| Section 3.1; Appendix A | Named historical comparisons using the same rate convention | `analysis/historical-comparators.csv` |
| Section 3.3 | 729 distinct B&H citers; 551 classified; four displayed fields total 537 | summary; `analysis/bh-citers-by-field.csv` |
| Section 3.3; Appendix A | Seven recoverable early reference links | `analysis/bh-linked-early-references.csv` |
| Section 3.3 | 55,140 model records, including 513 B&H citers | `analysis/co-citation-analysis.csv` |
| Section 3.3 | Linked-early-source odds ratio 6.91, 95% Wald interval 5.17–9.22 | `analysis/bh_early-coefficients.csv`; summary |
| Section 3.3 | Mean standardized difference 5.52 percentage points | summary; `scripts/check_results.py` |
| Section 3.3 | Other-early-source odds ratio 3.40, interval 1.47–7.90 | `analysis/other_early-coefficients.csv`; summary |
| Figure 3 | Stratum predictions, with minimum citer/non-citer counts | `analysis/stratum-differences.csv` |
| Appendix A | Exact input identities | `checks/expected-results.json`; `MANIFEST.json` |

## Specifications carried into the revision workflow

- Citing papers: articles and eprints from 2018–2025 in the six specified primary fields, with at least one retained date-eligible outgoing link.
- Early means before 1960 (through 1959).
- Reference-count covariate: log(1 + linked reference count), with reference years 1800–2025.
- Fixed effects: interaction of four two-year bins with primary field.
- First outcome: citation of any of the seven linked early references.
- Second outcome: citation of any pre-1960 source outside that subset.
- The rate denominator uses the inclusive interval from publication through the last recorded metric year for each paper, not a common end date.
- No coefficient-difference test or reception study is claimed.

The additional comparison model, numerical verification, historical comparator export, and explicit denominators are included here alongside the revised manuscript's limits on interpretation.

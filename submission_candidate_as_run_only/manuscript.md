# Where does machine-learning equity alpha go? Costs, capacity and capital-gains tax in Germany, India and Japan

**Manuscript candidate, as-run evidence only. Not submission-ready.** Draft of 2026-10-14 on branch `feat/completion-sprint-2026-10-14`. Authors, affiliations and acknowledgements are not filled in (author decision). This candidate is a narrower paper than the project's original framing and is **not** a replication or update of any analysis it did not perform. Its scope and what it omits are explained in `docs/FINAL_PUBLICATION_PATH.md`; every quoted number is traced in `TRACEABILITY.csv` and re-derived by `tools/check_submission_candidate.py`.

## Abstract

We measure how much of a machine-learning equity signal survives three implementation frictions (AUM-indexed trading costs, an ADV participation constraint and statutory capital-gains tax) in Germany, India and Japan over 2009-2019, on identical signals and a common investable universe, using a dated lot-level tax engine. Four statements are supported by the traceable as-run evidence. (1) The gross decile signals are real, but the executable participation-capped decile book has a negative net Sharpe ratio in all three markets at a $1bn mandate. Where a net Sharpe ratio of the optimised book is traceable (India, Japan), it is not distinguishable from zero. (2) The effect of the participation constraint, measured as an annualised net-return difference B(A) against an uncapped plan, increases monotonically with mandate size on the 35 rungs where the comparator is solvent; at large rungs the comparator is near-ruined and B(A) is an accounting difference against an infeasible plan, not a gain. (3) The statute decides whether a holding-period tax channel can exist: the long-term share of gains is exactly zero under the German and Japanese flat regimes; on the executable decile book the tax channel is eight to nineteen times larger in the flat regimes than in India, which is itself borderline significant. (4) No machine-learning design axis (representation, conditioning, uncertainty) is detectable at the available power on the capped decile book in Germany and India. We also document a cost-input coverage asymmetry that manufactured a highly significant but spurious cross-country result. All numbers were produced under the project's original exit treatment (`as_run`); a revised analysis under the later exit ruling is blocked by missing data and was not run, so sensitivity to the exit treatment is unknown.

## 1. Introduction

Machine learning extracts economically large predictability from the cross-section of equity returns [@GKX2020], and a second literature asks how much of it is implementable. Capacity under price impact is studied for the US in [@KS2004; @NMV2016], with dynamic trading under transaction costs in [@GP2013]; [@ACM2023] report that machine-learning return predictability weakens under realistic economic restrictions, and [@AHV2023] report net returns for machine-learning strategies priced with effective spreads and no AUM term. International machine-learning predictability is documented across 46 markets in [@CFMZ2023]. A cost-aware, AUM-dependent machine-learning portfolio method is the subject of [@JKMP2026]; we do not propose a method.

An allocator faces a specific mandate size in a specific market under a specific tax code. We therefore index every quantity to AUM, use three jurisdictions whose capital-gains statutes differ in whether a long-term category exists, and apply a lot-level tax engine rather than a flat haircut. We make no claim to be first on capacity, on fragility to frictions, on non-US machine learning or on tax-aware construction, and we do not adjudicate between [@NMV2016] and [@AHV2023]. Our contribution is a measurement, to our knowledge not previously assembled on one book across these three regimes (the literature search was not exhaustive), together with a methods caution.

**Scope of the evidence.** All results below were produced under the project's `as_run` exit treatment. A later ruling replaced it with a carry-forward policy, and the revised analysis (the project's "Phase C") **has not been run**: its inputs do not support it (Section 7). Pre-registration amendments are committed but **not countersigned** (Section 7). No claim here depends on either.

## 2. Related work

*Capacity and price impact.* [@KS2004] estimate break-even fund sizes for momentum under price impact; their results vary by a large factor across weighting schemes. [@NMV2016] compute capacities for 23 anomalies from effective spreads and a Kyle-linear impact model and find buy/hold rules the most effective cost mitigation; [@NMV2019] compare cost-mitigation techniques. Our cost model is square-root (concave per unit) in the sense of Section 4.1. *Machine learning net of costs.* [@ACM2023], [@AHV2023], [@CV2023] and [@JKMP2026] study returns net of costs; [@ACM2023] has been read at abstract level only in this project, and its full text must be read before submission. *International and design dispersion.* [@CFMZ2023]; design choices are studied in [@CHK2024], [@LAL2025] and uncertainty in [@LMNS2025]. *Tax.* Tax-aware portfolio construction and lot-level methods have a single-jurisdiction literature [CITATION PENDING: the project's tax-literature records, keys SS2018, IM2012, BY2003, KS2024, HUANG2019, PISH2026 and CBLO2020 in the full-account paper, and the Dai-Lei-Liu-Yang (Management Science 2026) and Moehle-Kochenderfer-Boyd-Ang (JOTA 2021) rows of the prior-art tracker, have no entry in `research/08_References/references.bib`; full records must be verified and added before submission]. None of the sources above prices capacity under a statutory tax engine to our knowledge.

## 3. Data and institutional detail

Panels for Germany, India and Japan were supplied and certified by a separate data workstream (contracts C1 universe, C2 signals, C4 targets, C6 cost inputs, C14 tax regimes); we did not independently audit survivorship or listing conventions. The evaluation window is 2009-01 to 2019-12 (132 months; India's tax panel has 131). The cost-input coverage that makes a security-month tradeable (a certified spread, daily volatility and USD ADV) is 0.652 in Germany, 0.989 in India and 0.998 in Japan (mean over months of certified C6 names divided by in-universe names; `results/phase_c_census_v3_2026-10-14/input_coverage_by_country_month.csv`). An uncertified security-month is non-tradeable and imputation is prohibited, so Germany's investable universe is smaller than its signal-bearing one. Statutory short-term rates as configured in the tax engine are 26.375% (Germany, flat) and 20.315% (Japan, flat); India has a short-term rate with a long-term category (the section 112A reform of 2018-04-01 is spanned by a dated engine). Breadth is capped at 600 names (verified bit-identical for Germany and India; binding only in Japan).

## 4. Framework

### 4.1 Cost model, constraints and books

Per name, in return units, `cost_i = (spread_i/2 + commission) |dw_i| + k sigma_d,i sqrt(AUM/ADV_i) |dw_i|^1.5` with commission 1 bp, k = 1.0 and borrow a modelled flat 1% per year (certified borrow-fee data do not exist). The participation constraint is `|w_i| <= 0.05 ADV_i / AUM`. The frozen contract has gross exposure 2.0, a 1% per-name cap and a 10% volatility target. We use three books: the **uncapped decile spread** (long top decile, short bottom, gross 2.0; not executable), the **capped decile spread** (the same with weights clipped to the participation cap; the first executable object), and the **optimised book** (full constraint set). Headline results use the 8 prediction cells of a 2x2x2x2 factorial (representation, conditioning, loss, uncertainty); the economic-loss arm is excluded because it is not a competent implementation. The capacity effect cannot be measured on the optimised book because an uncapped optimisation cannot be constructed, so it is measured on the decile books.

### 4.2 Solvency, the matched-book accounting and the unit B(A)

The same saved decile weights are passed through one lot-level backtest engine under the zero-tax control and the statutory regime on identical dates and universe. Capacity is reported as **B(A)**, the annualised mean net-return difference between the capped and uncapped decile composites (an equal-weighted summary of 8 independently simulated full-AUM variants, not an investable fund), in points of NAV per year. A rung is solvent only if no cell-month of either book has a net return at or below -100%; insolvent rungs get no B(A). Solvency is a minimal criterion: at many solvent rungs the uncapped comparator's compounded terminal wealth is far below one (Table 2).

### 4.3 Inference

Differences use a paired studentised stationary bootstrap (4,000 replications, block 6, seed 0 for B(A)), Holm adjustment within country over valid rungs, with unadjusted intervals shown separately. Sharpe-ratio t-statistics use Newey-West standard errors. The inference library was corrected on 2026-10-13; the corrections do not touch the tools that produced the results below, and residual limitations (approximate interval coverage, HAC over-rejection at high autocorrelation) are listed in the project's internal inference audit. This is an internal validation, not external statistical review.

## 5. Results

### 5.1 From signal to executable portfolio

The composite gross decile Sharpe ratio is +2.305 (Germany), +1.197 (India) and +1.278 (Japan) on the compliant universe, before value-weighting (which, on a superseded universe, cut gross Sharpe by about 80%; not re-run). At $1bn the executable capped decile book has a negative net Sharpe ratio in all three markets (Table 1). That book attains only a few percent of its target gross, so its Sharpe ratio is a ratio of small numbers dominated by fixed spread costs; the sign, not the level, is the finding.

**Table 1. Capped decile composite at $1bn (matched-book accounting; zero-tax control and statutory regime).**

| Country | Net Sharpe | t vs zero | Tax channel (after-tax minus net) | t | p |
|---|---|---|---|---|---|
| Germany | -0.709 | -2.40 | -0.070 | -3.55 | 0.017 |
| India | -0.638 | -1.81 | -0.009 | -2.14 | 0.037 |
| Japan | -0.828 | -2.74 | -0.170 | -3.67 | 0.002 |

For the optimised book at $1bn, the net Sharpe ratio is not distinguishable from zero where a result is traceable: India +0.271 (t +0.82, p 0.413; after tax +0.265, t +0.80) and Japan +0.055 (t +0.18, p 0.861; after tax -0.082, t -0.27). The corresponding German figure is quoted in project documents but no artifact containing it exists in the repository, so it is not reported here.

### 5.2 Capacity: the effect of the participation constraint

B(A) is monotone increasing in AUM across all 35 solvent rungs (Germany 11, India 10, Japan 14), and 3 German and 4 Indian rungs have an insolvent comparator and no B(A) (Figure 1; Table 2). It is not distinguishable from zero at the smallest German rungs ($100k: -0.52 points per year; $300k: -0.01) and Holm-significant at 9 of 11 German, 8 of 10 Indian and 8 of 14 Japanese rungs. Where B(A) is large the comparator is near-ruined: the uncapped composite's terminal wealth is below 0.1 at 6 of 11 German, 7 of 10 Indian and 4 of 14 Japanese rungs (Figure 2). **B(A) is therefore an accounting difference against an infeasible plan, not realised performance, and it is not convertible to a Sharpe-point gain.** The effect is small where the cap is slack and grows with how hard it binds; we describe this as found, not imposed.

**Table 2. B(A), Tier B (pipeline accounting; primary), selected solvent rungs. Points of NAV per year; terminal wealth of the uncapped composite (start = 1).**

| Country | AUM | B(A) | Unadjusted 95% interval | Holm p | Uncapped terminal wealth |
|---|---|---|---|---|---|
| Germany | $100k | -0.52 | [-1.85, +0.55] | 0.862 | 2.9 |
| Germany | $1mn | +5.09 | [+1.22, +9.03] | 0.041 | 0.70 |
| Germany | $10mn | +41.44 | [+31.39, +53.21] | 0.000 | 0.0069 |
| Germany | $100mn | +171.72 | [+146.06, +199.88] | 0.000 | 7.7e-10 |
| India | $100k | +2.88 | [+0.94, +5.33] | 0.070 | 0.92 |
| India | $1mn | +12.48 | [+6.59, +20.04] | 0.047 | 0.19 |
| India | $30mn | +103.99 | [+80.96, +132.42] | 0.010 | 2.6e-06 |
| Japan | $100k | -0.01 | [-0.03, +0.00] | 0.380 | 0.95 |
| Japan | $1bn | +101.65 | [+86.90, +116.62] | 0.000 | 6.7e-06 |
| Japan | $10bn | +289.32 | [+216.88, +360.45] | 0.003 | 1.1e-17 |

**Figure 1.** B(A) by mandate size, solvent rungs only, Tier A (wedge tool) and Tier B (pipeline, primary). Hollow markers: near-ruined comparator. File: `results/figures/fig1_capacity_return_difference_B.png`.
**Figure 2.** Compounded terminal wealth of the uncapped comparator at solvent rungs. File: `results/figures/fig2_uncapped_terminal_wealth.png`.

Tier A and Tier B cost accounting differ by convention and the difference is only partly explained by the cost-parity diagnostic (12 rung-book pairs); we report Tier B as primary and Tier A beside it. Japan's positive capacity result at $1bn was a prediction committed to the repository, with its scoring code, before any Japanese portfolio existed. It is not an externally pre-registered confirmation (Section 7); of the five predictions scored, one passed vacuously on a reading of -0.0013 (p 0.370) and one failed, both reported. A sign-flip hypothesis built on the German small-mandate region was retracted (Section 6).

### 5.3 Tax: what the statute decides

The long-term share of realised gains, `lt_share_of_gains`, is exactly 0.0000 in every statutory-regime row for Germany and Japan that we checked (80 rows across five summaries), because neither flat regime creates a long-term category; it is 0.5928 in India (mean over the 8 prediction cells at $1bn; from an untracked local output pending a tracked snapshot). This is a statutory fact, not an estimate. On the executable decile book the tax channel is -0.070 (Germany), -0.170 (Japan) and -0.009 (India) Sharpe points (Table 1): the flat regimes are 8 to 19 times larger in magnitude than India's, and India is itself borderline significant, so the supported statement is an ordering of magnitudes by statute type, not a clean contrast between significant and insignificant. On the optimised book the Japanese tax channel is -0.1373 (t -4.99, 3 of 8 cells significant under Holm) and the Indian -0.0054 (t -1.93, 0 of 8); the German value is not traceable. We do not claim that taxes decide viability (no net Sharpe is significantly positive before tax), that the tax drag is ordered by turnover rather than rate (not traceable at $1bn), or any causal tax effect. With three jurisdictions that differ in rate and wedge at once, the design cannot separate the two.

### 5.4 Design axes are not detectable at this power

For each of 14 mandate sizes and 3 axes (representation, conditioning, uncertainty), the composite of the four cells at each level is compared with the paired bootstrap and Holm correction across axes. On the capped decile book, 0 of 42 axis-rungs is significant in each of Germany and India; on the uncapped decile book 5 of 42 (Germany) and 0 of 42 (India). Germany's five are within multiple-testing expectation. Paired standard errors on the optimised book at $1bn imply a minimum detectable effect (80% power, 132 months; 2.8 standard errors) of 0.25 to 0.81 Sharpe points depending on axis and market. The null excludes only effects of roughly a quarter of a Sharpe point or more; the design has 8 cells, against hundreds to thousands in the design-dispersion literature [@CHK2024; @LAL2025]. One observation is **exploratory, not pre-specified and unreplicated**: on the optimised book at $1bn, Japan's conditioning axis has effect +0.515 (t +2.84), the only one of nine contrasts significant at 5% unadjusted. It is disclosed, not claimed, and must not be cited as evidence that conditioning helps.

## 6. A cautionary case: a coverage asymmetry that manufactured a result

An early capacity ladder formed deciles on Germany's signal-bearing cross-section rather than its investable one. Cost-input coverage is 0.652 in Germany against 0.989 in India, and the ladder violated the non-tradeability rule in both directions in Germany only (uncovered names were charged zero cost in the uncapped book and given a zero cap in the capped book). It produced a monotone, theoretically coherent negative capacity effect at small mandates (t = -6.098 at $100k), which survived a value-weighting check and an impact-coefficient sweep because both varied parameters inside the mis-specified universe. Enforcing the project's own non-tradeability rule removed it (the compliant reading at $100k is +0.068, t +1.22). **That result is retracted and is not a finding.** The lesson is that robustness checks that vary parameters within a frame do not test the frame: the checks that caught it were reconciling the count of names against the capacity frontier's, and asking whether the effect appears in a panel where the mechanism cannot operate. The cost of ignoring it would have been a headline.

## 7. Limitations and the status of the evidence

1. **Exit treatment and the blocked revised analysis.** All numbers use the `as_run` exit treatment, which drops a -100% lot without realising the loss and treats a missing cost-input row as a closed position. A later ruling replaced it with a carry-forward policy. The revised analysis has **not been run** and cannot be run on the current data: every one of 560 weight series exceeds the 25% unresolved threshold because C4 supplies no usable return for held names that leave the universe in a minority of their months, and the vendor coverage that might fill those months is undocumented (status unknown). No revised number exists. How the as-run numbers would change is unknown.
2. **Pre-registration.** PLAN_001 and its amendments are committed to the repository but not countersigned by the designated statistical reviewer; a further amendment is an unsigned, non-binding draft. "Prediction committed before the data existed" is the most that is claimed.
3. **Power.** 8 prediction cells and 132 months; the design null is a bound.
4. **Comparator.** The capacity effect is measured against an infeasible plan (Section 5.2). The cost-calibration sensitivity was not run, so no statement is made about the sign of the effect at other impact calibrations, and none about whether the cap ever hurts.
5. **Two books.** Cost and capacity are measured on decile books and tax on the capped decile book (and, separately, the optimised book); magnitudes are compared by order only.
6. **Turnover is endogenous; n = 3 jurisdictions;** borrow is a modelled flat proxy; value-weighting robustness is not confirmed on the compliant universe; the economic-loss arm is excluded.
7. **Traceability.** Some figures rest on untracked local outputs or are missing artifacts (the German optimised-book Sharpe and tax-channel figures); these are marked or omitted. This is an internal validation by the research team; no external review has occurred.

## 8. Conclusion

Under the original exit treatment, a machine-learning equity signal that is real gross does not survive implementation at institutional scale in these three markets: the executable book is negative net of costs, the net Sharpe ratio of the optimised book is not distinguishable from zero where it is traceable, the participation constraint matters more the harder it binds (against an infeasible comparator), and the statute, not the rate, decides whether a holding-period tax channel exists. These are measurements that corroborate published work, not a new mechanism. Whether they survive the project's revised exit ruling is unknown and currently untestable.

## Appendix A. Claims deliberately not made (withdrawn or not supported)

All items below are **withdrawn** or unsupported and must not be restated as findings: Sharpe-point capacity gains presented as established performance improvements (the comparators are near-ruined); capacity gains at German and Indian $1bn and $10bn rungs; an asymptotic channel and a cross-market regularity built on it; a capacity sign flip, its crossover and its scaling law; that taxes are decisive for viability; that two flat-regime tax placebos agree exactly; frontiers below US estimates; cost-over-tax ratios averaged over a broken arm; that capacity overwrites ML design identifiability; and that the cap never hurts at any mandate size. Each is recorded with its reason in `docs/FINALIZATION_AUDIT_2026-10-09.md` section 1.2 and `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`.

## Appendix B. Reproducibility

See `README.md` in this directory and the repository README. The numbers in this manuscript are re-derived from the committed artifacts listed in `TRACEABILITY.csv` by `python tools/check_submission_candidate.py`. The raw vendor data, the C4/C6 staging files and the original SAS inputs are not in the repository (data-access restrictions); the figures and tables here do not require them.

## References

References are in `references.bib` (a subset of `research/08_References/references.bib`, entries copied verbatim; a pending list is in `README.md`).

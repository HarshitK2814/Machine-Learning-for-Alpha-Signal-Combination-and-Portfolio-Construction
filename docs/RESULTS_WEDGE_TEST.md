# The wedge test: which friction channel binds on a machine-learning design?

**Status:** Germany complete, India running, Japan not yet run.
**Reproduce:** `python tools/exp_wedge_test.py --inputs outputs/summary_after_tax_DEU_1e9.csv
outputs/summary_after_tax_IND_1e9.csv`

---

## 1. The claim being tested

From `research/05_Selected_Research_Design/REFRAMED_CLAIM.md`:

> Machine-learning portfolio research controls frictions by penalising turnover. For a taxable
> investor the binding friction is not turnover but **holding-period composition**. The friction
> penalty on a machine-learning design is ordered by each country's statutory **holding-period
> wedge**, not by its transaction tax, and is **identically zero** in jurisdictions whose law sets
> a flat capital-gains rate.

The contribution is the identification, not the machinery: *nobody has used cross-country variation
in tax architecture to identify which friction channel binds on a machine-learning design choice.*

## 2. Why this is a test and not an arithmetic identity

`alphacomb.theory.tax_model` gives, for a strategy at turnover `p` under a realisation-based tax
with boundary `H` and wedge `Delta = theta_S - theta_L`:

```
R(p) = g(1 - theta_L) - kappa*p - g * Delta * Phi(p, H)
```

so tax paid per unit of gross return decomposes as

```
tax_drag / gross  ~  theta_L   +   Delta * Phi(p, H)
                     level         holding-period channel, PROPORTIONAL TO THE WEDGE
```

The empirical object is therefore the **slope of tax-per-unit-of-gain on turnover**, by country.
Zero where the wedge is zero; positive where it is not.

What stops this being a tautology is that the two candidate explanations are **opposed**, not
nested. Germany taxes capital gains at **26.375%**, harder than India's **15%** short-term rate.

* A *tax-level* account ("high taxes punish high-turnover strategies") predicts **Germany** shows
  the largest turnover penalty of the three.
* The *wedge* account predicts **Germany shows none at all**, because with no holding-period
  boundary there is nowhere for a gain to be moved to.

They cannot both be right, and the data chooses. The falsification condition was fixed in advance:
if the penalty tracks the transaction tax rather than the wedge, or if Germany shows the same slope
as India, the claim is wrong.

## 3. The statutory variation (frozen C14 schedule, not assumed)

Regimes are **derived** from `data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv`
by `alphacomb.tax.statutory`, so they cannot drift from the schedule the dated C14 engine resolves
against. Over the frozen 2009-2019 evaluation window:

| country | legal regime | cgt_short | cgt_long | **wedge** | boundary | STT |
|---|---|---|---|---|---|---|
| **DEU** | Abgeltungsteuer | 0.26375 | 0.26375 | **0.000** | none | 0 |
| **JPN** | reduced -> normal + reconstruction | 0.10 / 0.20315 | same | **0.000** | none | 0 |
| **IND** | STT100 / LTCG exempt | 0.15000 | 0.00000 | **0.150** | 12 months | 0.0010 |
| **IND** | Section 112A (from 2018-04-01) | 0.15000 | 0.10000 | **0.050** | 12 months | 0.0010 |

Germany and Japan are **placebos the tax code wrote**, not placebos we constructed. India's wedge
*falls inside the sample* when section 112A ends the LTCG exemption on 2018-04-01, which is a
within-country event study on top of the cross-country ordering - and the reason the frozen
mechanism subwindow stops at 2018-03-31, since across 2014-01..2018-03 every country sits on a
single constant rule.

## 4. Germany: the placebo holds

16 cells, 132 months, statutory Abgeltungsteuer, HIFO lot selection, `tax_exempt` as the zero-tax
control.

| quantity | value |
|---|---|
| slope of tax-per-gain on turnover | **-21.99** |
| robust t-statistic | **-1.44** |
| significant at 5% | **no** |
| mean tax drag | 5.2 bp p.a. |
| mean cost drag | 27.7 bp p.a. |
| `lt_share_of_gains` | **0.000 in every cell** |

Supporting correlations across the 16 cells:

| | |
|---|---|
| corr(tax drag, turnover) | **-0.544** |
| corr(tax drag, gross return) | +0.423 |
| partial corr(tax drag, turnover \| gross) | **-0.377** (n=16, p ~ 0.17) |

**Turnover does not raise the German tax bill.** The slope is statistically indistinguishable from
zero and its point estimate is *negative*. What the bill does track is gains, which is exactly what
a flat rate implies: every euro of gain is taxed once at 26.375% however often it is realised.

`lt_share_of_gains` is 0.000 in every cell because under Abgeltungsteuer **no holding-period
boundary exists for newly acquired listed shares** - there is no long-term category for a gain to
fall into. That is the placebo stated in the ledger's own output.

Note the magnitudes: tax drag averages 5.2 bp against cost drag of 27.7 bp. For a German investor
in this universe, costs dominate taxes more than five to one.

## 5. India: the treatment

*Running. India carries a 0.15 wedge and a 12-month boundary with full ADV coverage (99.98%),
against Germany's exactly-zero wedge. The prediction is a positive, significant slope.*

## 6. Japan: the second placebo, not yet run

Japan is the strongest available replication of the Germany result, because it is flat-rate at a
**different level** (20.315% against Germany's 26.375%). Two flat-rate countries at different
rates both showing a zero slope is far harder for a tax-level story to accommodate than one.

It has not been run: 247,412 investible months and ~2,400-name cross-sections put it at roughly a
day of compute on this machine. It is the single most valuable run left, and the ask is in
`docs/handoff/18_FOR_ABSAR_...`.

## 7. What this does and does not establish

Even with India, this is a **three-country** design with 16 cells per country, so the slope is
estimated on 16 points. The claim rests on an *ordering across jurisdictions* that the statute
fixes in advance, not on the precision of any single slope. That is the design's strength - the
treatment is assigned by tax law rather than by us - and also its limit: with three countries, the
cross-country degrees of freedom are three.

The honest framing is that the test can **falsify** the wedge account cleanly (a significant
positive slope in Germany would do it) while **confirming** it only as far as three jurisdictions
and one sample period allow.

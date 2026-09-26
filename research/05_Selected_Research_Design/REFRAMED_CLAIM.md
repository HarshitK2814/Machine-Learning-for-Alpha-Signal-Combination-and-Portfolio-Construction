# The reframed claim

**Supersedes the headline of `Selected_Research_Design.md`.** That document's design, contracts and
experiment list all stand. What changes is what the paper is *about*, and therefore what the first
five pages have to establish.

---

## 1. The claim

> Machine-learning portfolio research controls frictions by penalising turnover. For a taxable
> investor the binding friction is not turnover but **holding-period composition**. We identify this
> using cross-country variation in tax architecture: the friction penalty on a machine-learning
> design is ordered by each country's statutory holding-period wedge, not by its transaction tax,
> and it is **identically zero** in jurisdictions whose law sets a flat capital-gains rate.

## 2. Why this passes the desk

The binding desk-rejection criterion for an empirical finance paper is that a reader of the first
five pages can state, in one sentence, why the estimates can be read causally. Ours:

> **Germany and Japan tax capital gains at a flat rate, so no holding-period boundary exists for a
> strategy to be penalised by. They are placebos the tax code wrote, not placebos we constructed.**

Three further properties a referee looks for:

* **Dose-response.** The wedge is 17 points in the United States, 7.5 in India, zero in Germany,
  Japan, Singapore, Hong Kong, Taiwan and China. The prediction is an ordering, not a sign.
* **A confound that the design breaks.** The United Kingdom (50 bps stamp duty) and Taiwan (30 bps
  securities transaction tax) have *high* transaction taxes and therefore *low* optimal turnover -
  close to the United States, which has almost no transaction tax at all. **Turnover alone cannot
  distinguish them; the decomposition can.** Our calibrated model puts the holding-period channel at
  59.8% of the friction cost in the US, 20.9% in India, and exactly 0.0% in the UK and Taiwan
  despite their similar turnover.
* **A falsification condition fixed in advance.** If the penalty tracks the transaction tax instead
  of the wedge, or if Germany and Japan show the same penalty as the United States, the claim is
  wrong and we say so.

## 3. The theory, in one line

`alphacomb.theory.tax_model`. For a strategy at turnover `p` under a realisation-based tax with
boundary `H`:

```
R(p) = g(1 - theta_L)  -  kappa*p  -  g * Delta * Phi(p, H)
```

with `Delta = theta_S - theta_L` the wedge and `Phi(p,H) = 1 - H(1-p)^(H-1) + (H-1)(1-p)^H` the
share of gains realised at the short-term rate - which is exactly the `lt_share_of_gains` the
after-tax ledger already measures, so the model's central object is a quantity the pipeline reports.

Differentiating separates the channels:

```
-dR/dp = kappa                    turnover channel, identical across tax regimes
       + g * Delta * dPhi/dp      holding-period channel, PROPORTIONAL TO THE WEDGE
```

Two results worth stating because intuition gets them backwards:

1. **Under a flat rate the tax bill does not depend on turnover at all.** Every dollar of gain is
   taxed once at the same rate however often it is realised. "High turnover means a big tax bill" is
   true only where a wedge exists. A test pins this.
2. **The wedge converts turnover into a rate, not an amount.** That is first-order, and it is
   precisely what an objective penalising `|dw|` cannot reach.

33 tests, including the closed form checked against Monte Carlo across 18 parameter combinations.

## 4. What each existing piece becomes

| Piece | Was | Is now |
|---|---|---|
| Factorial attribution across 4 ingredients | The contribution | **The mechanism section** - shows the effect is holding-period composition, not turnover |
| After-tax lot-level ledger | The contribution | **The measurement instrument** |
| Nine-jurisdiction module | A realism detail | **The identification strategy** |
| `theory.tax_model` | Did not exist | **The comparative static the empirics test** |
| Adaptive combination | A contribution | **Appendix.** Scored -0.003 against fixed 1/N; Remlinger et al. (2023) own the method |
| Complexity x tax wedge | A hypothesis | **Rejected.** Spearman +1.000 against the prediction. Keep only the residue: complexity *lengthens* holding periods |
| Inference layer | Did not exist | **Reported on every table**, not an appendix |
| Pre-registration | Did not exist | **Frozen before the confirmatory run.** `prereg/PLAN_001`, 64 configurations, fingerprint `cae8140b7e2b7ee4` |

## 5. What is still missing, honestly

1. **Real data.** Still the only fatal blocker. Everything above is a plan until C1-C6 arrive.
2. **International panels.** The identification needs actual return and cost data for at least the
   US, India, Germany or Japan, and one high-transaction-tax flat-rate country. This is a
   substantially larger data ask than the original US-only design and must be raised with
   workstream A **now**, not after the US results are in.
3. **Tax rates verified against statute** for each jurisdiction and each sample period. Every rate
   currently carries `[verify]`.
4. **The remaining frontier rungs** - attention, conformal, robust optimisation - are built but
   never validated against a benchmark. The complexity ladder was silently inverted for weeks;
   assume these are broken until shown otherwise.

## 6. The honest sentence about novelty

Huang (2019) showed taxes matter more than costs for an ML strategy. Sialm & Sosner (2018) and
Krasner & Sosner (2024) analysed after-tax long/short factor portfolios. Pishehvar (2026) built
lot-level tax machinery into an ML portfolio system. Remlinger et al. (2023) aggregated ML models
online for long/short.

**Nobody has used cross-country variation in tax architecture to identify which friction channel
binds on a machine-learning design choice.** That sentence is the contribution, and it is the only
ground in this project that no one else currently occupies.

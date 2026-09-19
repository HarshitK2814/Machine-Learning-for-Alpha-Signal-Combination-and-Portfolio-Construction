# After-tax evaluation and self-adapting combination

Two capabilities added to workstream B, both aimed at one question: **what does the investor keep
out of sample, after everything?**

---

## 1. Why this is a contribution and not just plumbing

Every paper in our closest-prior-art tracker reports returns **gross of tax**. @GKX2020,
@JKMP2026, @SWZ2023, @DMNU2020, @DMU2024 and @FRLUX2025 all stop at net of trading costs. That is
not an oversight on their part: the implicit investor is a pension fund or an endowment, and for
that investor net-of-cost *is* net.

But the same papers motivate themselves with turnover. A strategy that turns over 150% a year and
realises its gains at short-term rates hands a top-bracket US investor a bill that, under the
default regime encoded here, is of the same order as the trading cost. Jeffrey and Arnott's 1993
question — *is your alpha big enough to cover its taxes?* — has never been asked of a machine-learning
signal-combination pipeline.

This gives us a claim that is **new, testable, and small enough to defend**:

> The ranking of machine-learning signal-combination designs is not invariant to the investor's tax
> status. Designs that win on net-of-cost Sharpe are not the designs that win after tax, and the
> reordering is driven by a measurable channel: holding-period composition, not turnover alone.

That claim is falsifiable. If the ranking turns out to be invariant, we report that, and it is still
a finding worth a table: it would tell the literature its gross-of-tax results generalise.

**Status: [proposal]. The numbers in section 5 are a synthetic-data rehearsal, not a result.**

---

## 2. What the tax layer models

`alphacomb.tax`, three modules.

### `regimes.py` — who is being taxed

| Regime | Short-term | Long-term | Structure |
|---|---|---|---|
| `tax_exempt` | 0 | 0 | The literature's implicit investor. Our control. |
| `taxable_us_top_bracket` | 40.8% | 23.8% | s1(h) + s1411 NIIT. Wash-sale rule on. |
| `trader_475f_mtm` | 40.8% | 40.8% | s475(f) election: unrealised gains taxed annually, no wash-sale rule, no holding-period benefit. |
| `offshore_fund` | 0 | 0 | No US tax on a non-resident's capital gains; 30% statutory withholding on dividends. |

Rates are **defaults, flagged `[verify]`**, not a legal position. They are overridable per run and
must be re-checked against the schedule in force before any number leaves the repository.

### `lots.py` — the rules that actually decide the bill

Portfolio-level `turnover × rate` is not good enough, because three lot-level things dominate:

* **s1222 / s1(h)** — the long-term boundary. Held *more than* twelve months, tested on the exact
  anniversary. Our first implementation used a month fraction and a leap year pushed a
  twelve-month hold over the line; the boundary is worth 17 points of tax, so it is now an exact
  `DateOffset` comparison and a test pins it.
* **s1233** — closing a short is *always* short-term, however long it was open. Half of a
  dollar-neutral book therefore has no access to the preferential rate at all.
* **s1091** — the wash sale. A monthly-rebalanced strategy re-buys names constantly, so the rule
  disallows a large share of exactly the losses a tax-aware strategy wants to harvest. It is
  implemented in both directions (repurchase within 30 days before *or* after the loss sale), with
  the disallowed loss added to the replacement lot's basis and the holding period tacked under
  s1223(3).

Lot selection is a first-class choice: `FIFO`, `LIFO`, `HIFO`, `TAX_OPTIMAL`.

### `backtest.py` — the ledger

Runs in dollars with a real NAV. Total return is split into price and dividend so the dividend tax
and the capital-gains tax are distinguished; shorts pay a substitute dividend which, for a taxable
individual, is not currently deductible. Gains net within character then across (s1222), losses
offset ordinary income only to the statutory cap (s1211(b)), and the excess carries forward
(s1212(b)). Because reporting only *realised* tax flatters any strategy that defers, the summary
also reports a **liquidation** figure where every open position is sold on the last day.

**Not modelled, stated rather than hidden:** state and local tax, AMT, s1256 and straddle rules,
constructive sales (s1259 — does not bind, the optimiser never holds both sides of one name), and
intra-month timing (trades settle at month end, so the wash window is evaluated on month-end dates;
adjacent month ends are 28–31 days apart, so a sale followed by a next-month repurchase is treated
as a wash — the conservative reading, and we report how much it disallows).

### Tax inside the optimiser

`alphacomb.portfolio.tax_terms` adds to the objective

```
tax(w) = Σ rate_i · max(g_i,0) · pos(w_prev_i − w_i)     (selling a gain costs tax)
       − Σ rate_i · |min(g_i,0)| · s_i                    (selling a loss earns a credit)
```

convex in `w`; the harvesting credit needs the bounded auxiliary variable `0 ≤ s_i ≤ w_prev_i`,
`s_i ≤ w_prev_i − w_i`, or the objective is not concave and the solver would manufacture unlimited
harvesting. `g_i` and `rate_i` come from **the same ledger that later scores the result**, so the
optimiser cannot be optimising against a tax model the accountant would not recognise.

**The wash-sale trap, which is itself a result.** An optimiser given a harvesting credit and no
further constraint sells a loser and buys it straight back next month — and s1091 disallows exactly
that loss. The strategy pays the trading cost and gets nothing. `--wash-block` forbids
re-establishing a name inside the window. We run both on purpose: the gap between them is the
measurement.

---

## 3. What the adaptive layer does

`alphacomb.adaptive`. The request was for models that change on their own. There are two ways to do
that and only one survives a referee.

**The version that does not survive:** each month, pick whichever model looked best recently. That
is a specification search run monthly. Our own falsification audit (`docs/FALSIFICATION_AUDIT.md`)
shows how much performance adaptive search manufactures under a no-predictability null.

**The version that does:** fix the aggregation rule *ex ante*, feed it only realised out-of-sample
outcomes, and inherit a regret bound.

* `hedge.py` — exponentially weighted average forecaster (Vovk 1990; Littlestone–Warmuth 1994;
  Freund–Schapire 1997; Cesa-Bianchi–Lugosi 2006). Cumulative performance falls short of the best
  single model *in hindsight* by at most O(√(T log N)), without knowing in advance which model that
  is. The Herbster–Warmuth (1998) fixed share competes with the best *sequence* of models, which is
  the right object when the world has regimes. Learning rate is either parameter-free
  `η_t = √(8 log N / t)` or set on validation months and frozen. **The reward is after-tax net
  return** — a model that forecasts well but trades expensively loses weight automatically.
* `drift.py` — Page-Hinkley change detection decides *when* to refit, instead of refitting annually
  because everyone else does. Two-sided, so an improvement also triggers. The threshold is
  calibrated to a false-alarm rate on validation months and then frozen. A firing detector triggers
  exactly one action: refit the current specification. The specification is never re-chosen, so
  this adds **no trials** to the multiple-testing count.
* `meta.py` — ties them together, with `assert_causal` checking on the produced panel that no
  combination weight could have seen the month it is applied to. The whole claim rests on that
  property, so it is asserted rather than trusted.

**The comparison that matters.** `compare()` always reports the adaptive rule next to (a) each
member alone, (b) the equal-weighted blend of the same members, and (c) the best member in
hindsight. Online aggregation routinely fails to beat an equal-weighted blend. If that is what
happens, the table says so and the pipeline prints it in words.

---

## 4. How to run it

```bash
# after-tax evaluation of every strategy that has weights
python pipelines/06_after_tax_eval.py --lot-methods hifo fifo tax_optimal

# tax-aware construction, with and without the wash-sale block
python pipelines/04_construct_portfolios.py --strategies cell_N-C-P-0 --tax-aware --suffix _taxaware
python pipelines/04_construct_portfolios.py --strategies cell_N-C-P-0 --tax-aware --wash-block \
    --suffix _taxaware_washblock

# self-adapting combination
python pipelines/07_adaptive_combine.py --members all --share 0.05
```

---

## 5. Results

*(filled in by the run recorded in `docs/AFTER_TAX_RESULTS.md`)*

---

## 6. What this changes in the research design

New axis for the factorial design, orthogonal to the existing four:

* **Tax regime (T)**: `0` tax-exempt (control, reproduces the literature) / `T` taxable.

This does **not** multiply the 16 cells into 32 trials. The tax layer is an *evaluation* applied to
weights that already exist, so it adds no fitting and no trials to the deflated-Sharpe count. Only
tax-*aware construction* adds trials, and it adds exactly three arms (tax-blind, tax-aware,
tax-aware + wash-block) on the selected cells, all logged to `outputs/trials.csv`.

## 7. Prior art we must not overrun

Added to `03_Research_Gaps/Closest_Prior_Art_Tracker.md`. All entries are `[verify]` until the
Crossref pass confirms them.

| Work | What it does | Why we are not it |
|---|---|---|
| Jeffrey & Arnott (1993) | Poses the after-tax alpha question for active equity | Poses it; does not test ML combination designs |
| Constantinides (1983, 1984) | Optimal realisation theory: realise losses, defer gains | Theory. We measure a pipeline |
| Dammon, Spatt & Zhang (2001, 2004) | Optimal rebalancing with capital-gains tax | Lifecycle consumption, not cross-sectional signal combination |
| Arnott, Berkin & Ye (2001); Berkin & Ye (2003) | Loss harvesting and HIFO accounting value | Long-only index strategies |
| **Sialm & Sosner (2018)** | **Taxes, shorting and active management — the closest work** | **Long/short tax treatment for factor portfolios. Does not do ML combination, and does not attribute across design ingredients. Threat: HIGH** |
| Israel & Moskowitz (2012) | Tax efficiency of equity styles | Style portfolios, not learned combinations |
| Chaudhuri, Burnham & Lo (2020) | Empirical evaluation of tax-loss-harvesting alpha | Harvesting as the strategy, not as a constraint on an alpha pipeline |
| Cover (1991); Blum & Kalai (1999); Li & Hoi (2014) | Universal portfolios, online portfolio selection | Aggregate over *assets*; we aggregate over *models*, scored after tax |
| Herbster & Warmuth (1998) | Tracking the best expert | The rule we use, cited not claimed |
| Gama et al. (2014) | Concept-drift adaptation survey | Source of the detector, cited not claimed |

**Decision rule, unchanged:** if a paper appears that does factorial attribution across two or more
of our ingredients, net of costs *and* tax, on stock-level data, we pause and re-scope.

## 8. Open items

1. `--tax-aware` construction has not yet been run over the full out-of-sample span; only the
   evaluation layer has. The three-arm comparison in section 2 is implemented but not yet measured.
2. The dividend yield is a flat configurable constant because neither panel carries a dividend
   column. `targets` (C4) now accepts an optional `div_next` column; Absar's real-data build should
   populate it. Until then, dividend tax is a sensitivity parameter, not a measurement.
3. The qualified-dividend test (s1(h)(11)) is applied at position level, not per share per
   ex-dividend date, which monthly data cannot resolve. Stated in the module docstring.
4. Tax rates are constant over the sample. Real rate schedules changed repeatedly across 1972–2025;
   a time-varying schedule is the honest version and is a known gap.

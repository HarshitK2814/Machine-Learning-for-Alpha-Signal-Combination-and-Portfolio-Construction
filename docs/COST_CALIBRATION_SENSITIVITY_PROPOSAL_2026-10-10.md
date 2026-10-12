# Cost-calibration sensitivity: proposal (Workstream B)

**Date:** 2026-10-10; revised 2026-10-12 after review. **Status: UNEXECUTED, and BLOCKED pending the exit-policy ruling
(`EXIT_POLICY_GATE_2026-10-12.md`).** Nothing in it has been run. The frozen cost contract stays the primary
specification. No cost sensitivity, model training or paper change happens until the gate is resolved and the
settings below are explicitly approved. Labels: **[V]** verified from a source I read in full; **[A]** abstract- or summary-level only;
**[D]** derived here by arithmetic from a [V] source; **[U]** unresolved.

## 1. Why this is needed

A referee will say the frozen impact coefficient (`k = 1`, square-root impact, total cost `~ |dw|^1.5`) overstates real
trading costs, so that the near-zero net Sharpe ratios and the ruinous uncapped books are a calibration artefact. The
review memo ranked this the most serious external objection. This proposal defines, in advance, how to test it without
selecting parameters because they flatter the result.

## 2. Non-negotiable rules

1. The frozen contract (`configs/base.yaml`: `impact_k 1.0`, `impact_power 1.5`, 1 bp commission, certified C6 spreads,
   `MODELLED_FLAT_BORROW_PROXY_V1` at 1%) remains the **primary** result everywhere. Sensitivity results are secondary,
   labelled, and never replace it.
2. **No arbitrary discounts.** Every non-frozen setting must be either (a) derived by a stated formula from a published
   estimate, with the derivation fixed *before* any outcome is computed, or (b) confirmed against the signed protocol with
   Maham (not yet done for any grid; see section 5).
3. **No outcome-driven selection.** Settings, tables, tests and decision rules below are fixed now. Nothing is added,
   dropped or re-tuned after results are seen. If a setting fails to run it is reported as failed.
4. **No silent changes.** Sensitivity runs use new, separately tagged output directories and new override files; the
   frozen config, the existing results and the Phase 1 / Phase 2 commits are not touched. Different settings must not be
   able to overwrite each other (tested; see section 10).
5. Whatever the outcome, **all** pre-specified tables are reported, including ones that change the conclusion.

## 3. Evidence reviewed

**Frazzini, Israel & Moskowitz, "Trading Costs" (Aug 2018 draft) [V, full text].**
* Data: $1.7 trillion of live executions, one large institutional manager (AQR), 21 developed markets, 1998-2016,
  algorithmic and patient execution (trade horizon up to 9.8 days). **Emerging markets are excluded**, so India is not
  covered. Germany and Japan are included.
* Cost definition: market impact (MI) versus the price when trading starts, on executed volume. It embeds the bid-ask
  spread, impact and commissions; the paper notes spreads and commissions "do not scale with size". The average MI in the
  sample is 9.97 bp and the average implementation shortfall 11.02 bp.
* Functional form: impact is concave in the fraction of daily volume (`x`); a power-law fit gives an exponent of about
  0.35; they adopt the **square root**, rejecting a linear form by an F-test. This supports the frozen exponent
  (per-dollar impact `~ sqrt(x)`, total cost `~ |dw|^1.5`) and not Kyle-linear.
* **Support: the live data cover trades of at most about 12% of daily volume**; the paper limits its model comparisons
  to that range.
* Calibrated model (global sample, other covariates at sample medians): **13.73 bp at 2% of daily volume and 32.34 bp at
  10%**. TAQ-calibrated models, same form: square-root 27.09 and 60.23 bp, linear-plus-square-root 29.07 and 64.21 bp,
  linear 44.89 and 223.31 bp. They find live costs about half the TAQ square-root estimates and "an order of
  magnitude" below earlier linear-impact studies.
* Cross-country: costs are higher in Australia, Hong Kong, Japan and Singapore, and close to the US in Sweden,
  Germany and France (a figure; no numbers extracted [U]).
* Short selling: no difference in cost between selling a long and selling short; **no borrow-fee measurement** beyond a
  US ETF cost comparison using lending-fee estimates from Blocher and Whaley.

**Frazzini, Israel & Moskowitz, "Trading Costs of Asset Pricing Anomalies" (Dec 2012 draft) [V]:** same data family,
break-even sizes for size, value, momentum of tens to hundreds of billions globally and about $9-13bn for short-term
reversal; square-root-of-volume impact.

**Novy-Marx & Velikov (Aug 2015 working paper) [V]:** effective-spread costs plus a capacity measure for the marginal
trader; high-turnover strategies have capacities of about $0.18-0.53bn. Different capacity definition from ours.

**Subsequent evidence, abstract- or summary-level only [A]:** Brière et al., a US institutional-trade study giving
annual costs of 16-23 bp for size and value and 222-274 bp for momentum, with a momentum break-even of about $310mn
(versions differ); Chen & Velikov (effective spreads only, no impact); Azevedo, Hoegner & Velikov (spread-based costs
for ML anomaly strategies, US). **No international live-execution study covering India was found [U]**; NSE's
published "impact cost" is a simulated market order against the displayed order book, a different quantity from
executed-trade slippage, so it is not used to calibrate.

## 4. What transfers, and what cannot be calibrated

| Component | Frozen value | Identifiable from our data? | External evidence | Treatment |
|---|---|---|---|---|
| Impact **exponent** | 1.5 total (sqrt per dollar) | no | FIM 2018 [V] supports sqrt over linear | keep fixed; curvature already tested earlier (Kyle-linear, level-matched) |
| Impact **level** `k` | 1.0 | no (no execution data) | FIM 2018 anchors at 2% and 10% of volume [V] | **derived settings S1, S2 below** |
| Spread (half-spread) | certified C6 spreads | partly (spread is an input, estimator-dependent) | MI embeds spread; no separable external spread level | hold fixed; no spread-only sensitivity (cannot be calibrated) |
| Commission | 1 bp | no | embedded in FIM execution prices | hold fixed |
| Borrow | 1% flat | no | none for DEU / IND / JPN found [U]; fee-bucket conventions exist (35 / 150 bp) but are not country estimates | no borrow sensitivity is run unless the grid in section 5 is first checked against the signed protocol |
| Exit treatment of names that leave the panel | Tier B zero-cost exit | no | n/a | an accounting convention, not a calibration; see Workstream A. Sensitivity inherits Tier B. |
| Country differences | single `k` for all | no | FIM: Japan above US, Germany near US [V, figure only] | none applied; stated as a limitation. India: **no external anchor**; the global anchor is applied as an explicit transfer assumption |

**Mapping of FIM to our cost function [D]. S1 and S2 are literature-anchored proxy scenarios, not direct
calibrations of our portfolios.** Our per-dollar impact for a trade of fraction `x = trade$/ADV` is
`k * sigma_d * sqrt(x)`. Anchor each scenario at the 10% point, the edge of the live-trade support, and attribute the
whole published cost at that point to impact (the published figure also contains spread and commission, which our model
charges separately, so this is, if anything, the higher of the defensible readings):

    k_live(c) = 32.34 bp / [ sqrt(0.10) * sigma_ref(c) ]          k_taq(c) = 60.23 bp / [ sqrt(0.10) * sigma_ref(c) ]

`sigma_ref(c)` is the median daily volatility over certified name-months in the frozen C6 inputs of country `c`,
2009-2019, computed from inputs only and written to a read-only registry before any outcome exists. **At the reference
`sigma_ref = 2%` per day: `k_live = 0.51` (S1) and `k_taq = 0.95` (S2).** Cross-checks at the same reference: the 2%
anchor gives 13.73 bp / (sqrt(0.02) * 2%) = 0.49 for S1, and an increment-based version, which removes the intercept,
gives 0.53 (S1) and 0.95 (S2); the three S1 readings agree within about 8%. The frozen `k = 1` therefore sits at the
TAQ-calibrated square-root level and about twice the live-trade level, a factor of about two and not an order of
magnitude. The country values will differ from these reference numbers by the ratio of `sigma_ref(c)` to 2%. FIM's
regression also depends on firm size, idiosyncratic volatility and market volatility, which this mapping ignores, and it
rests on one manager's patient execution, so S1 and S2 bracket a plausible range; they do not identify the cost
facing any of our books.

**Beyond the support of the evidence [measured, Workstream A].** The uncapped books trade at a notional-weighted
median of 128% (India $30mn), 172% (Japan $1bn), 596% (Germany $100mn) and 1,719% (Japan $10bn) of daily volume, with
54-98% of notional above 100%. The live evidence ends near 12%, so **no calibration can validate the uncapped
comparator's costs**; the capped books stay near the support (median 0.5-5%). Sensitivity of the uncapped book is
therefore a statement about extrapolation, whichever `k` is used.

## 5. Settings

| Id | Meaning | Impact `k` | Other terms | Status |
|---|---|---|---|---|
| **S0** | frozen contract (primary) | 1.0 | frozen | the contract |
| **S1** | live-trade anchored proxy scenario | `k_live(c)` (about 0.51 at the 2% reference) | frozen | active in the first sensitivity, once the gate is cleared |
| **S2** | TAQ-calibrated square-root anchored proxy scenario | `k_taq(c)` (about 0.95 at the 2% reference) | frozen | active in the first sensitivity, once the gate is cleared |
| G | joint cost multiplier {0.5, 1, 2, 3} on spread and impact together | n/a | frozen otherwise | **NOT adopted.** The values appear in `configs/base.yaml` (`sensitivity_multipliers`) and in the builder of the withdrawn PLAN_002 (`prereg/build_plan_002_international.py`). Whether they are in the signed protocol has **not been checked**; they may not be described as countersigned or pre-registered until that is verified with Maham |
| R | borrow-rate grid {0.3%, 0.6%, 1%, 4.3%, 7%} | n/a | frozen otherwise | **NOT adopted.** The values appear in `configs/workstream_a_frozen_decisions.json` (decision 6B). Same caveat as G |

The first eventual sensitivity is **S0, S1 and S2 only**. Nothing else is run. In particular there is no spread-only,
commission-only, exponent, country-specific, G or R setting unless the protocol check clears G and R.

## 6. Design

**Repricing of frozen weights only.** The frozen weights (the optimised books and the eight-cell decile books, capped and
uncapped) are re-priced with S0, S1 and S2 using the existing pipeline accounting (`after_tax_backtest` at zero tax;
Tier B). No model is trained and no portfolio is re-optimised. **Re-optimisation under any setting is excluded from this
proposal.** Caveat stated up front: a manager facing lower costs would trade more, so repricing understates what lower
costs allow; it answers "what do these same trades earn", not "what could a cost-aware manager earn".

**Exit policy gate.** Repricing inherits the pipeline's treatment of names that become uncertified, unpriced or leave the
price panel. That treatment is under review (`EXIT_POLICY_GATE_2026-10-12.md`) and no sensitivity runs until it is
ruled on or explicitly carried as an unresolved limitation.

Countries: Germany, India, Japan. Window: the frozen 2009-2019 evaluation. Cells: the 8 prediction cells. Mandates: $1bn
(the headline) and the Phase 2 valid rungs for B(A); India's transfer is labelled as such.

## 7. Outcomes, inference and decision rules (fixed now)

**Tables, each country by setting:** T1 optimised-book net Sharpe at $1bn with Newey-West t and 95% interval; T2 capped
decile-book net Sharpe at $1bn (matched-book) with t; T3 Tier B B(A) for every rung that is solvent under that setting,
with the number of solvent rungs, terminal wealth of the uncapped comparator and Holm-adjusted p within country and
setting; T4 trade-size support (share of notional beyond 12% of daily volume) per setting's affected books; T5 the
break-even table (section 8). All are reported whether or not they change the conclusion.

**Inference.** Net Sharpe against zero by Newey-West t; setting versus S0 by the existing paired Ledoit-Wolf
`sharpe_difference_test` on the same months; B(A) by `mean_difference_test`. **Multiplicity:** the claim "net
Sharpe differs from zero under a literature-anchored setting" is a family of 6 tests (3 countries x {S1, S2}); Holm
adjustment over that family. (If G and R are later cleared by the protocol check they would be descriptive curves with
no adjusted p-values.)

**Decision rules.**
* **R1 (primary conclusion robust):** under S1 and S2, no country's optimised-book net Sharpe at $1bn is significantly
  positive after Holm. Then the abstract claim stands as written and the sensitivity is reported as support.
* **R2 (calibration-dependent):** at least one country is significantly positive after Holm under S1 or S2. Then the
  claim "net performance is indistinguishable from zero" is **withdrawn as unconditional** and re-stated as conditional
  on the cost level, with the break-even and the literature bracket stated; the frozen result stays reported as the
  primary specification.
* **R3 (strengthened):** net Sharpe is non-positive under all of S0, S1, S2.
* **B(A):** the statement that the cap's accounting benefit is large only against ruined comparators is re-checked
  per setting by reporting, per rung, the uncapped terminal wealth and the share of notional beyond 100% of volume;
  no wealth threshold enters the primary analysis.
* A conclusion that changes is reported as changed; there is no reversion to the primary because it is more
  convenient.

## 8. Break-even (reproducible, not a chosen parameter)

For each country define `m*` as the smallest multiplier on the impact coefficient `k / k_frozen` in [0, 1], holding
spread, commission and borrow at their frozen values, at which the optimised-book net Sharpe at $1bn first has a
Newey-West t of at least 1.96. Under repricing of frozen weights the net return is monotone non-increasing in `k` for fixed weights, so
`m*` is found by deterministic bisection (tolerance 0.01, at most 20 steps), after a monotonicity check at five fixed
points; if the check fails, that is reported and no `m*` is given. `m*` is then placed against the literature bracket
`[k_live/k_frozen, k_taq/k_frozen]` computed in section 4, without adjustment. The break-even is a threshold the
data imply, reported with the bracket regardless of where it falls.

## 9. Prohibited

Arbitrary or "reasonable-looking" discounts; any setting not in section 5; choosing among settings after seeing
results; changing the frozen config, exponent, 600-name cap, window or cell set; re-optimisation under any setting,
model training, value-weighting, or data extensions; describing S1 or S2 as the truth rather than as a
bracket; quoting a sensitivity result without the frozen result beside it.

## 10. Reproducibility and tests

* Override files under `configs/sensitivity/` (new); output under `results/cost_sensitivity/<setting>/` with a manifest
  (hashes, git state, versions, commands), as in Phase 2.
* Tests to write before running: (1) the settings registry equals section 5 exactly; (2) with S0 the sensitivity driver
  reproduces the committed frozen numbers bit for bit; (3) two settings run into different directories cannot
  overwrite each other (audit task P0-6); (4) the bisection stops with an explicit failure if monotonicity fails;
  (5) `k_live` / `k_taq` follow the stated formula for given inputs.
* `sigma_ref(c)` and the resulting `k` values are computed and **written to the registry before any outcome is
  computed**, then the registry is read-only.

## 11. Limitations stated in advance

Single manager's execution; patient algorithmic trading; developed markets only (no India); support to about 12% of
volume; US-style definitions of MI; the mapping uses medians and ignores firm-size and volatility terms; repricing understates
the benefit of lower costs; the exit convention (Workstream A) is unresolved and inherited from Tier B.

## 12. Decisions and gates

1. **Gate (blocking):** the exit-policy ruling, or an explicit decision to carry it as unresolved.
2. Approve, amend or reject S1 and S2 and the derivation in section 4.
3. **Protocol check (not yet done):** compare the multiplier and borrow grids with the signed protocol with Maham before
   G or R are used or described as pre-registered.
4. Confirm repricing of frozen weights as the only first sensitivity.

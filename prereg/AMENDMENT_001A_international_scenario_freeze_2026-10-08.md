# Pre-registration amendment 001A — international scenario freeze

**Amendment date:** 8 October 2026
**Amends:** `PLAN_001_after_tax_attribution.json` (21 September 2026)
**Parent fingerprint:** `cae8140b7e2b7ee4` — **unchanged**
**Confirmatory trial count:** **N = 64** — **unchanged**
**Status:** `FROZEN_PRE_RESULTS`
**Drafted by:** Workstream B, on Workstream C's behalf, to Workstream A's specification
**Requires countersignature:** Maham (workstream C) before the confirmatory C11 run

```ini
REAL_RESULTS_INSPECTED_BEFORE_AMENDMENT = NO
PARENT_PLAN_OVERWRITTEN                 = NO
TRIAL_COUNT_CHANGED                     = NO
```

---

## 0. Why an amendment and not a new plan

PLAN_001 fixed the **grid** — 16 cells crossed with shrinkage ∈ {low, high} and capacity ∈
{small, large}. That grid is unchanged. What was never written down is the **empirical setting**
the grid runs in: which countries, which window, what the scenario labels mean numerically, and
which sensitivity runs are confirmatory.

Those gaps are what frozen decision 6B requires closing before any result is inspected. Closing
them does not change the grid, so the parent fingerprint and N survive. Writing a *new* plan with
a new N would have been the wrong move: it would reset the deflation hurdle on the basis of a
change that is not a change to the search.

This amendment is drafted by workstream B because workstream C is unavailable until Sunday and the
amendment is the critical path for everyone. **It is not final until Maham countersigns.** Any
numeric value she disagrees with should be changed here, before the run, not after.

---

## 1. Frozen: countries and panel structure

**DEU, IND and JPN are fitted, optimised and evaluated separately.** One model per country, one
portfolio per country, one tax ledger per country. Results are reported per country and, where a
single figure is needed, aggregated by equal country weight.

There is no pooled cross-section in the confirmatory design.

**Why separate rather than pooled.** Two reasons, one forced and one chosen:

- *Forced:* C14 tax year-ends differ — Germany and Japan in December, India in March. An after-tax
  ledger spanning the three has no well-defined tax year, so portfolio construction and the C12
  ledger must be per country regardless of how the model is fitted.
- *Chosen:* with the construction already per country, fitting per country turns the paper's design
  into **three independent replications of the same attribution**. For the headline claim —
  nonlinearity contributes X, state dependence Y — three markets agreeing is far stronger evidence
  than one pooled estimate, and it sidesteps the question of whether signals are cross-country
  comparable, which we cannot settle and a referee would press.

The cost is training data: each model sees one country's cross-section. This is mitigated because
pre-2009 observations remain available for training and feature construction (they may not seed tax
lots — see §2).

*Recorded dissent:* a pooled-fit / per-country-construct variant would buy roughly 3x the training
cross-section and may fit better. It is available in code as
`alphacomb.contracts.intl.PanelMode.POOLED_FIT_SEPARATE_CONSTRUCT`. Running it is **exploratory**
and must be labelled as such; it is not part of the confirmatory design.

## 2. Frozen: evaluation windows

| Window | Span | Role |
|---|---|---|
| Primary tax-dependent evaluation | **2009-01-01 → 2019-12-31** | All confirmatory after-tax results |
| Clean mechanism subwindow | **2014-01-01 → 2018-03-31** | Reported separately; inherits tax state from the 2009 inception |
| Training / feature construction | 1990-01-01 → evaluation start | Permitted; **may not seed tax lots or tax state** |

The dated ledger cold-starts on 2009-01-01 with no opening lots and no pre-2009 acquisition dates.

Neither window may be used to select a configuration. The mechanism subwindow in particular is a
*reporting* cut, not a selection cut — choosing the specification that looks best on 2014-2018 and
reporting it on 2009-2019 would be selection on the outcome.

These bounds come from Workstream A's pre-results amendment of 7 October and were set because the
span is complete under the frozen C14 source record, **not** because of anything observed in
strategy performance.

## 3. Frozen: the numerical meaning of the scenario labels

PLAN_001 named its grid levels but never bound them to numbers. Bound here, using values already
present in the code rather than new ones.

### 3.1 `shrinkage` ∈ {low, high} — uncertainty shrinkage κ

Applied in `portfolio.alpha_scaling.shrink_by_uncertainty`:
`alpha_i / (1 + κ · (s_i / mean(s))²)`.

| Label | κ |
|---|---|
| `low` | **0.5** |
| `high` | **2.0** |

Both are members of the existing `CellRunConfig.kappa_grid = (0.0, 0.5, 1.0, 2.0, 4.0)`.

> **Implementation change required before the confirmatory run.** The code currently *selects* κ
> from all five grid values on validation. That is a five-way search, not the two-way one PLAN_001
> registered. Left alone, the real confirmatory search would exceed N = 64 and the deflated Sharpe
> would be computed against a count that is too small — precisely the failure
> `validation/preregistration.py` was written to prevent.
>
> For confirmatory runs, `kappa_grid` must be restricted to `(0.5, 2.0)` for the uncertainty cells
> and `(0.0,)` for the non-uncertainty cells. Running the full five-value grid is exploratory and
> must be reported with its own, larger N.

In the eight cells with `U = 0`, κ ≡ 0 by definition and the shrinkage dimension is inert.

### 3.2 `capacity` ∈ {small, large} — AUM at which costs are assessed

Enters the square-root impact term `impact_k · σ_d · sqrt(AUM / ADV) · |Δw|^1.5` and the
participation cap `adv_participation_max = 0.05`.

| Label | AUM (2020 USD) |
|---|---|
| `small` | **1.0 × 10⁹** — the configured `costs.aum_usd_2020` |
| `large` | **1.0 × 10¹⁰** |

Capacity is a *design* dimension, not a sensitivity: both levels are part of the 64 and the
selected configuration is chosen within a capacity level, never across them.

## 4. Frozen: borrow-fee proxy

Certified C6 `borrow_fee` is null. `MODELLED_FLAT_BORROW_PROXY_V1` is injected at the
C11/experiment layer only and never persisted into C6. The legacy 25 bp fallback is prohibited.

| Role | Annual rate |
|---|---|
| **Primary** | **1.00%** |
| Pre-registered robustness | 0.30%, 0.60%, 4.30%, 7.00% |

Classification: `MODELLED_PREREGISTERED_PROXY_NOT_OBSERVED`. The short leg's cost is an assumption,
not a measurement, and the paper must say so. The five-rate band belongs in the **main** results,
not an appendix. If the headline does not survive 7.00% p.a., that is the finding.

Verified-unshortable security-months remain ineligible at every rate.

## 5. Frozen: confirmatory robustness vs exploratory

**Confirmatory robustness** — pre-registered, reported for the selected configuration, and
**outside** the trial count because none of them is used to select:

| Axis | Values |
|---|---|
| Borrow proxy | 0.30%, 0.60%, 4.30%, 7.00% (primary 1.00%) |
| Cost multiplier | 0.5, 2.0, 3.0 (primary 1.0) |
| Universe | `nyse_top500`-equivalent large-cap cut (primary: all stocks in C1) |
| Subperiods | 2009-2013, 2014-2019; plus the clean mechanism window |
| Seeds | reported as a stability diagnostic (E56), never used to select |

**Exploratory** — reportable, but must be labelled, and may not feed the headline:

- pooled-fit panel mode (§1)
- the full five-value κ grid (§3.1)
- any AUM level other than the two frozen capacity levels
- India TERM robustness cuts until Workstream A's independent RBI 91-day rebuild lands; the current
  India TERM state is provisional

## 6. Frozen: tax-aware vs tax-blind construction

Both are confirmatory and both are reported; the contrast is one of the paper's mechanisms.

| Arm | C11 construction |
|---|---|
| **Tax-blind** | optimiser excludes the tax term; C12 still accounts for tax after the fact |
| **Tax-aware** | optimiser includes the dated tax term (`portfolio.tax_terms`) |

This is a *construction* contrast applied to the already-selected configuration, not a selection
dimension. It does **not** multiply N: the configuration is chosen once, on validation rank IC,
and then built both ways.

## 7. The trial-count convention

**The deflated Sharpe ratio uses N = 64.** Not the number of rows in `outputs/trials.csv`, not the
number of fits, not the sensitivity reruns.

Two notes a referee will want, both pointing the conservative way:

1. **N = 64 is an upper bound, and deliberately so.** The shrinkage dimension is inert in the eight
   `U = 0` cells, so the count of *distinct* configurations is
   `8 × 2 × 2 + 8 × 1 × 2 = 48`, not 64. We report 64. Over-stating N raises the hurdle a result
   must clear, which is the safe direction to be wrong in.
2. **Comparators are not in N.** The five workstream-C baselines (`BASE-EW`, `BASE-THEME-EW`,
   `BASE-IC`, `BASE-OLS`, `BASE-RIDGE`) are reported unconditionally, whatever they show, so they
   are not part of the search that selects the reported strategy and do not inflate selection bias
   on the ML result. The one exception to disclose: `BASE-RIDGE` selects its penalty on validation,
   so the ridge comparator's *own* deflation should use N = 2, not N = 1.

`n_refits` is **11** (annual refit across 2009-2019). `n_fits = 64 × 11 = 704` is reported as the
conservative alternative count for any table that prefers it, with the table stating which it uses.

## 8. What must happen before the confirmatory run

1. Maham countersigns this amendment, or edits the numbers in §3 and countersigns.
2. `kappa_grid` is restricted per §3.1. **This is a code change and it is a blocker** — without it
   the run's real N exceeds 64.
3. `configs/base.yaml` splits are reconciled to §2. The file still carries the superseded US
   settings (`first_test_year: 1995`, `last_dev_test_year: 2020`, `lockbox 2021-2025`,
   `borrow_gc_bps_pa: 25.0`). None applies to the international design.
4. Only then is C11 produced and sent to Workstream A for the C12 run.

## 9. Superseded drafts

`PLAN_002_international_after_tax.json` was written by workstream B earlier on 8 October, before
Workstream A specified this amendment route. It proposed a separate plan with **N = 70**, counting
the five baselines into the trial count. It is **withdrawn, unused, and no result was produced
under it** — see `PLAN_002_WITHDRAWN.md`. The N = 64 convention in §7 supersedes it.

The disagreement is recorded rather than erased because it is a real methodological choice: whether
fixed comparators belong in the deflation count. Workstream A's position — that they do not,
because they are reported unconditionally and so do not drive selection — is the convention adopted
here, with the `BASE-RIDGE` exception disclosed in §7.

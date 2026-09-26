# What Harshit needs from Absar — workstream A → B

**22 September 2026.** Consolidates and supersedes `docs/ASK_ABSAR.md` and
`docs/HARSHIT_NEEDS_FROM_ABSAR.md`. Those two stay in the repository as history; this is the one to
work from.

---

## 0. The one-line version

**Workstream B is code-complete against synthetic data and blocked entirely on real data.** Not one
real return has entered the pipeline. Nothing else is close to binding.

**What "delivered" means here: analysis-ready files.** Every preprocessing step listed in §3 is
workstream A's, not a shared responsibility and not something workstream B does on receipt. Our code
reads contracts and applies no cleaning, no winsorising, no normalisation, no lagging and no
currency conversion. If a step below is skipped, the result is not a slower pipeline — it is a
silently wrong paper, because our tests check schemas and cannot detect a look-ahead you left in.

---

## 1. Priority 0 — a one-page feasibility note, this week

Before any data work begins. The research claim changed on 21 September and now requires
**international** panels, which is a materially larger ask than the original US-only design.

| Country | Can you source C1–C6? | History depth | Vendor | Licence cost | Your effort estimate |
|---|---|---|---|---|---|
| United States | | | | | |
| Germany **or** Japan | | | | | |
| India | | | | | |
| UK **or** Taiwan | | | | | |
| Hong Kong **or** Singapore | | | | | |

**If only the United States is feasible, say so immediately.** The claim reverts to a US-only
version. This is not a soft preference — it determines what the paper *is*, and we would rather know
in week one than after a year of work.

## 2. Priority 1 — the minimum viable data set

**United States + one flat-rate country + India.** Two countries is not enough: with only the US and
India the holding-period wedge and the transaction tax stay confounded, which is the exact confound
the whole design exists to break.

| Country | Why this one specifically |
|---|---|
| **United States** | 17-point holding-period wedge (40.8% short / 23.8% long), effectively no transaction tax. The treatment at full strength. |
| **Germany or Japan** | Flat capital-gains rate — **no holding-period boundary exists in law**. This is the placebo the identification rests on. A placebo written into statute, not one we constructed. Without at least one flat-rate country there is no identification and no paper. |
| **India** | Moderate wedge (7.5 points) **and** a large transaction tax (STT on both sides). The one country that discriminates between the turnover channel and the holding-period channel. |

Second tier, valuable but not blocking: **UK** (isolates the wash-sale rule — the 30-day
bed-and-breakfast rule differs from US §1091), **China A-shares** (dividend tax rate is itself
holding-period dependent, a wedge on the income side rather than the gains side).

---

## 3. The data engineering, in full

This section exists so that nothing is left ambiguous about who does what. **All of it is
workstream A.** Deliver per country, each country a separate directory.

### 3.1 Universe construction → C1 `universe.parquet`

Columns: `date, permno, in_universe (bool), me, price, exchcd, ff49, nyse_size_pct`

1. **Identifier spine.** One stable security identifier per country, `int32`, unique per
   `(date, permno)`. For non-US markets pick the vendor's permanent id and document the mapping.
   Handle changes of listing, ticker recycling and share-class consolidation **before** delivery.
2. **Survivorship.** Include dead and delisted names for the months they were alive. A universe
   built from today's constituents invalidates everything downstream.
3. **Screens, applied as the `in_universe` flag and not by dropping rows.** Keep the rows; flip the
   flag. That way a robustness universe is a change to one column rather than a change to the
   pipeline. US convention is price ≥ \$5, above the NYSE 20th size percentile, ≥ 12 months of
   history. **Each country needs its own documented screen** — a \$5 price floor is meaningless in
   JPY or INR. State the local equivalent and the reasoning.
4. **Industry classification** in `ff49`, or the closest local mapping, because it drives the
   optimiser's industry-neutrality constraints. If a country cannot support FF49, give us your
   scheme and the crosswalk; do not silently substitute.
5. **`me`** (market equity) in **local currency**, used for specific-risk shrinkage by size decile.
6. **`nyse_size_pct`** or the local analogue — the size percentile against the primary exchange.

### 3.2 Signals → C2 `signals.parquet` + C3 `signal_meta.csv`

Columns: `date, permno, sig_* (float32 in [-0.5, 0.5]), miss_<theme> (int8)`

**This is the step most likely to be under-specified, so it is spelled out.** Arrive at
`sig_*` having already done all of:

1. **Point-in-time construction.** Accounting items lagged to actual availability (not fiscal period
   end — a December year-end is not knowable in January). Document the lag convention per item.
   Prices and returns use information up to and including month end t only.
2. **Winsorise** at the cross-sectional 1st/99th percentile, per month, before normalising. State the
   percentile you used.
3. **Cross-sectional rank-normalise to `[-0.5, 0.5]`**, per month, within the `in_universe == True`
   set. Not z-scores — uniform ranks. Our models assume a bounded, scale-free feature.
4. **Missing values set to exactly `0.0`** (the cross-sectional median after rank-normalisation),
   **and flagged** in `miss_<theme>`. Never forward-fill a stale accounting item into a month where
   it was not available. Never impute from the cross-section in a way that uses other stocks' future.
5. **Theme assignment** in C3, one of the 13 themes per signal, plus `pub_year` and `source`. The
   theme composites drive the risk model, the conditional interactions and every interpretation
   output, so a signal with no theme is a signal we cannot use.
6. **`pub_year`** is the publication year of the originating paper, needed for the publication-gated
   robustness test (E54). Please populate it from the start rather than retrofitting.

### 3.3 Targets → C4 `targets.parquet`

Columns: `date, permno, r_1m, r_3m, r_6m, r_12m, ret_next`, **and `div_next`**

1. **Excess returns** over the local risk-free rate, in **local currency**. Name the risk-free proxy
   per country.
2. **Delisting returns applied**, with the convention documented (CRSP `dlret` handling, or the
   local equivalent). A delisting-to-zero that is silently dropped biases every result upward.
3. **`ret_next`** is the forward one-month total return aligned to the weight date — this is what the
   economic cells maximise and what weight drift uses. Get the alignment wrong and everything is
   wrong in a way no test will catch.
4. **`div_next` — please supply this, it is no longer optional in spirit.** The dividend component of
   `ret_next`, as a non-negative fraction, so `ret_next - div_next` is the price return. CRSP gives
   it directly as `RET - RETX`. The after-tax ledger needs the split because dividends and capital
   gains are taxed differently, at different rates, at different times. It matters *more*
   internationally: several jurisdictions tax dividends on a different schedule entirely, and China
   A-shares' dividend rate is itself holding-period dependent. Without it the ledger falls back to a
   flat configured yield and every dividend-tax number becomes an assumption rather than a
   measurement — which is exactly the sort of thing a referee circles.

### 3.4 States → C5 `states.parquet`

Columns: `date, MKTVOL, BEAR, ILLIQ, SENT, CREDIT, TERM, INFL, DRATE, DISP, FMOM_<theme>`

1. **Observable at t.** A state variable that uses month-t+1 information destroys the conditioning
   result and is undetectable downstream.
2. **Standardised with an expanding window only** — never full-sample. Full-sample standardisation
   leaks the future into every early month.
3. **Country-specific.** Each country needs its own states (its own volatility, credit spread, term
   spread, inflation), not the US series reused. A shared global state variable is a different
   research design and needs to be a deliberate choice, not a default.
4. Also needed later: `states_placebo.parquet`, the same columns with the time index shuffled, for
   the E53 placebo (shuffled states must destroy the conditioning gain).

### 3.5 Cost inputs → C6 `cost_inputs.parquet`

Columns: `date, permno, spread, sigma_d, adv_usd, borrow_fee`

1. **`spread` is a fraction, not basis points.** `0.0025` means 25 bp. The optimiser halves it for
   the half-spread. A units error here changes the paper's conclusion.
2. **`adv_usd` in currency units**, because the participation cap is `adv_usd * 5% / AUM`. Name the
   column `adv_usd` even where the currency is not USD — it is a contract name, and converting would
   break the tax layer. Document the currency in the country config.
3. **`sigma_d`** is daily return volatility, used in the impact term.
4. **`borrow_fee`** is the annual stock-loan fee as a fraction. For countries where shorting is
   restricted or unavailable (which includes parts of our candidate list), say so explicitly rather
   than filling zeros — a zero borrow fee and an unshortable market are very different facts.
5. **Spread estimator by era**, documented: TAQ from 1993, and EDGE or Abdi-Ranaldo before. For
   non-US markets state what you used. This is one of the open questions in §6.

### 3.6 Statutory charges and tax schedules → **C14, new**

This is the contract that did not exist before the international turn, and it is the one that makes
the paper's identification work. We need, **per country and dated**, the full charge stack.

Suggested shape, one row per `(country, effective_from, charge)`:

| Field | Meaning |
|---|---|
| `country` | ISO code |
| `effective_from`, `effective_to` | the statute's date range |
| `stt_buy`, `stt_sell` | securities transaction tax / stamp duty, as a fraction of trade value |
| `brokerage` | typical institutional commission, fraction of value |
| `gst_on_brokerage` | indirect tax applied to the brokerage, **not** to trade value |
| `exchange_fee`, `regulator_fee` | per-side turnover charges (SEBI, SEC §31, etc.) |
| `platform_fee_annual` | flat custody/platform fee as a fraction of NAV |
| `cgt_short`, `cgt_long` | capital-gains rates either side of the holding-period boundary |
| `holding_period_months` | where the boundary sits, or `null` if the country has none |
| `dividend_rate` | dividend tax rate, and note if it is holding-period dependent |
| `annual_exempt_local` | annual exemption in local currency (India's ₹1.25 lakh, Germany's Sparer-Pauschbetrag) |
| `loss_carryforward_years` | `0`, a number, or `inf` |
| `losses_ring_fenced` | whether relief is confined to one bucket |
| `ordinary_income_offset` | annual amount deductible against ordinary income |

**Rates change, and our sample spans decades.** India's STT and LTCG both moved materially in 2024.
A single constant rate across the sample is wrong and we will be asked about it in review. Dated
rows are the requirement, not a nicety.

**Every rate currently in `src/alphacomb/tax/jurisdictions.py` carries a `[verify]` marker** and was
taken from secondary sources by me. If you have access to a tax database, verifying these against
statute for each sample period is high-value and low-effort, and it removes a whole class of referee
objection. This is Priority 3 but it is genuinely important.

### 3.7 Properties the files must have

These are checked by `alphacomb.contracts.validate`, so please run it before handing over.

1. **`permno` is `int32`; `date` is a month-end timestamp**; `(date, permno)` pairs are unique. A
   silent duplicate corrupts every cross-sectional operation.
2. **Local currency throughout — do not convert.** Taxes are levied locally and thresholds are
   nominal local amounts. Converting to USD destroys the exemption thresholds and makes the tax layer
   meaningless.
3. **Local trading calendars** for the month-end convention. Month-end in Tokyo is not month-end in
   New York.
4. **Coverage from 1972**, or the earliest year you can support, so the expanding training window has
   history before the first test year.
5. **No look-ahead anywhere.** Our tests assume it; they cannot detect it for you. This is the single
   assumption of the whole project that rests entirely on workstream A.

---

## 4. The cost function must agree exactly

The optimiser embeds this as a convex term. `alphacomb.costs.trade_cost` must return the same number
for the same trade:

```
cost_i(dw) = 0.5 * spread_i * |dw_i| + (commission_bps / 10000) * |dw_i|
           + k * sigma_d_i * sqrt(AUM / adv_usd_i) * |dw_i|^1.5
borrow_i(w) = (borrow_fee_i / 12) * max(-w_i, 0)
```

`alphacomb.portfolio.cost_terms.trade_cost_numpy` is the reference implementation and
`tests/portfolio/test_optimizer.py::test_cvx_cost_matches_numpy_formula` pins it. **Please write a
matching test on your side.** If the two ever disagree, the net-of-cost attribution — which is the
paper's headline — is meaningless.

## 5. The backtest engine (C12) — do not rebuild what exists

`alphacomb.tax.after_tax_backtest` already produces a contract-valid C12 table with additive tax
columns, and `tools/dev_backtest.py` is the simple stand-in. If you take C12 on, **start from our
implementation rather than parallel to it.** Two independent engines will disagree and we will spend
a week finding out why — this has already happened once in this project with the optimiser, and it
cost a day (see `docs/FRONTIER_VALIDATION.md` §3).

What your version should add that the stand-in skips: the one-day implementation lag, delisting-month
handling, and hard-to-borrow escalation.

## 6. Open questions we need answered before the frozen run

1. Which spread estimator is primary for each era and each country?
2. What is the local liquidity screen for each non-US market, and what is the justification?
3. Is shorting available and borrowable in each candidate country over the whole sample? If not,
   from when?
4. What is the local risk-free proxy per country?
5. Can `div_next` be supplied for every country, or only some?

---

## 7. What is waiting for the data

So this is not a one-way ask. The moment C1–C6 land, the following runs:

* **Contracts C1–C13 frozen** at v1.1.0 with a validator — drop files in and the pipeline runs.
* **Nine tax jurisdictions** with lot-level ledgers: exact §1222 anniversaries, §1233, bidirectional
  §1091 with basis adjustment and holding-period tacking, four lot-selection methods, loss-relief
  architecture including carryforward life and ring-fencing.
* **An economic model** with a closed-form comparative static that the empirics test.
* **A full inference layer**: Newey-West, Lo/Mertens Sharpe standard errors, deflated Sharpe, PBO,
  Romano-Wolf, Hansen SPA, Benjamini-Hochberg.
* **A frozen pre-registration** (`prereg/PLAN_001`, 64 configurations, fingerprint
  `cae8140b7e2b7ee4`) so the trial count is honest before the first real fit.
* **~228 tests**, and a documented history of eleven silent failures that those tests now catch.

## 8. The honest caveat about our side

Workstream B has had a bad run of silent bugs, all now fixed and all documented in
`docs/SILENT_OPTIMISER_FAILURE.md` and `docs/FRONTIER_VALIDATION.md`. The most serious, found on
22 September, is that the optimiser's **solver selection rule was choosing infeasible books** — it
preferred a solver reporting `optimal` over one reporting `optimal_inaccurate`, and on this problem
the first is infeasible (139 of 827 names over their position cap) while the second is not. It is
fixed and verified. You should know this for two reasons: the synthetic results predating it may
move, and it is a live example of why your side's cost implementation needs its own independent
test rather than agreement-by-inspection.

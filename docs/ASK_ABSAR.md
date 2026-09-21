# What we need from Absar — consolidated and prioritised

**21 September 2026.** Supersedes the scattered asks in `HARSHIT_NEEDS_FROM_ABSAR.md`, which stays
as the detailed contract specification. This is the short version, in the order it matters.

---

## The one-line summary

**Everything is blocked on data. Nothing else is close to binding.** The code is built and heavily
tested; the research claim is reframed and has a theory behind it; the statistics are in place. What
does not exist is a single real return.

---

## Priority 0 — a feasibility note, this week, one page

Before any data work starts, we need to know what is actually sourceable. The research claim changed
on 21 September and now requires **international** panels, which is a much larger ask than the
original US-only design.

Please answer just this:

| Country | Can you source C1–C6? | History depth | Vendor | Cost | Effort |
|---|---|---|---|---|---|
| United States | | | | | |
| Germany **or** Japan | | | | | |
| India | | | | | |
| UK **or** Taiwan | | | | | |
| Hong Kong **or** Singapore | | | | | |

**If only the United States is feasible, say so immediately.** The claim reverts to a US-only
version and we would rather know now than after a year of work. This is not a soft preference — it
determines what the paper is.

---

## Priority 1 — the minimum viable data set

**US + one flat-rate country + India.** Two countries is not enough: with only the US and India the
holding-period wedge and the transaction tax stay confounded, which is the exact confound the design
exists to break.

Why each one:

* **United States** — 17-point holding-period wedge, effectively no transaction tax. The treatment
  at full strength.
* **Germany or Japan** — flat capital-gains rate, so **no holding-period boundary exists in law**.
  This is the placebo the whole identification rests on. Without at least one flat-rate country
  there is no identification and no paper.
* **India** — moderate wedge (7.5 points) *and* a large transaction tax (STT both sides). The one
  country that discriminates between the two channels.

## Priority 2 — contracts C1–C6, per country

Unchanged from `HARSHIT_NEEDS_FROM_ABSAR.md` section 1, plus these country-specific points:

1. **Local currency throughout.** Do not convert. Taxes are levied locally and thresholds are
   nominal local amounts (India's ₹1.25 lakh exemption, Germany's Sparer-Pauschbetrag).
2. **`div_next`** — the dividend component of `ret_next`, so `ret_next - div_next` is the price
   return. CRSP `RET` minus `RETX` gives it directly. Optional in contract v1.1.0, so nothing breaks
   without it, but dividend tax stays an assumption rather than a measurement until it arrives.
   It matters more internationally: several jurisdictions tax dividends differently from gains, and
   China's dividend rate is itself holding-period dependent.
3. **Statutory charge schedules by date.** Transaction taxes and capital-gains rates change. India's
   STT and LTCG rates both moved materially in 2024. A single constant rate across the sample is
   wrong and we will be asked about it.
4. **Local universe filters.** The `$5` price screen and NYSE size percentile are US conventions.
   Each country needs its own documented liquidity screen.
5. **Local trading calendars** for the month-end convention.

## Priority 3 — the C12 backtest engine

Still owned by workstream A and still a stand-in on our side (`tools/dev_backtest.py`). Lower
priority than it was, because `alphacomb.tax.after_tax_backtest` now does the work we need and
writes a contract-valid C12 table with additive tax columns. **Do not rebuild what exists** — if you
take C12 on, start from our implementation rather than parallel to it, or the two will disagree and
we will spend a week finding out why.

## Priority 4 — nice to have, not blocking

* `states_placebo.parquet` for experiment E53.
* The publication-gated signal list for E54.
* Anything that lets us verify the tax rates in `alphacomb.tax.jurisdictions` against statute for
  each sample period. **Every rate currently carries `[verify]`** and was taken from secondary
  sources. If you have access to a tax database, this is high-value and low-effort.

---

## What we have ready for the data the moment it lands

So this is not a one-way ask — here is what is waiting:

* **Contracts C1–C13 frozen** at v1.1.0, with a validator. Drop files in and the pipeline runs.
* **Nine tax jurisdictions** with lot-level ledgers: exact §1222 anniversaries, §1233, bidirectional
  §1091 with basis adjustment and holding-period tacking, four lot-selection methods, loss-relief
  architecture including carryforward life and ring-fencing.
* **An economic model** with a closed-form comparative static that the empirics test.
* **A full inference layer**: Newey-West, Lo/Mertens Sharpe standard errors, deflated Sharpe, PBO,
  Romano-Wolf, Hansen SPA, Benjamini-Hochberg.
* **A frozen pre-registration** (`prereg/PLAN_001`, 64 configurations, fingerprint
  `cae8140b7e2b7ee4`) so the trial count is honest before the first real fit.
* **222 tests**, and a documented history of six silent failures that those tests now catch.

---

## The honest caveat about our side

The tax-aware optimiser path was broken for most of 21 September and is **now fixed** - 36 of 36
months solving optimally and three times faster, after three attempts at the same bug. The story is
in `STATUS.md`. Nothing else was affected: the evaluation ledger never builds the optimiser's tax
term, so every after-tax number already published stands.

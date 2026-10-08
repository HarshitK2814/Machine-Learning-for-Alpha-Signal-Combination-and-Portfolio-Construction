# 18 — For Absar: C6 coverage, and the non-tradeability rule your C12 engine has to match

**From:** Harshit (workstream B)
**Date:** 8 October 2026
**Why you need this:** two of these items change what the real C12 engine must do, and one is a
question only you can answer about the promoted data. Nothing here blocks me — I have a working
treatment and the DEU exhibit is running — but if your engine implements a different rule than
mine, our weights and your returns will disagree and neither of us will know which is right.

---

## 1. The first real-data run of the 16-cell design failed, and the cause was in my layer

For the record, because it bears on how much to trust anything I have sent before: running the
factorial on the promoted DEU panel produced, for all eight prediction cells,

```
132 months, statuses {'failed_hold_missing_cost': 131, 'optimal_inaccurate': 1}
```

One month of strategy, then 131 months of a drifting 2009 book. My fault, in `construct`: when any
held name lost its certified cost inputs I held the **entire** prior book, which meant the book
never changed and so never regained eligibility. Fixed, documented in
`docs/NON_TRADEABLE_TREATMENT.md`, 13 regression tests.

The stale-portfolio guard that exists to catch exactly this did not fire, because it read
`counts.get("failed_hold", 0)` and the status was `failed_hold_missing_cost`. **If you have a
similar guard keyed on an exact status string, check it.** Mine now matches any `failed_hold*`.

## 2. C6 `adv_usd` is non-null for only 55% of DEU — is that expected?

This is the question I need you to answer. On the promoted DEU C6 (122,784 rows, 1990-2020):

| field | non-null |
|---|---|
| `spread` | 85.5% |
| `sigma_d` | 97.1% |
| **`adv_usd`** | **55.3%** |
| `borrow_fee` | 0% (certified null, as agreed — I inject the proxy at C11) |

`adv_usd` is the binding one. Over the frozen 2009-2019 window the share of each month's
signal-bearing cross-section with all three of spread, sigma_d and positive ADV is **65% on
average, 52% at worst, and never 100% in any of the 132 months.**

So the tradeable German universe is ~246 names a month, not the ~360 that carry a signal. I am
treating that as real and reporting it — document 13 requirement 2 says an uncertified
security-month is non-tradeable and must not be imputed, and I have not imputed anything.

**What I need from you:** is 55% ADV coverage the true extent of the source data, or is it a gap in
the promotion (a join that dropped rows, a unit/currency filter, a vendor field that was available
but not carried through)? The answer changes the paper's universe-construction section, and if it
is recoverable it materially increases the investable universe. I am proceeding on the assumption
that it is real.

Same question for IND and JPN — I have not profiled those yet, and if the pattern differs by
country, the cross-country comparison inherits it.

## 2b. One more fault, on the cost-objective axis: the projection had no trade cap

`project` - the C11 path the eight economic-loss cells use - built its own constraint list and took
no prior book, so it applied the per-name position cap but never the per-name **trade** cap
`|w - prev| <= adv_cap` that every prediction cell faces. Measured against the drifted prior book
(`tools/verify_trade_caps.py`):

| cell | tradeable trades | over `adv_cap` | worst | cumulative excess gross |
|---|---|---|---|---|
| `N-C-E-U` before the fix | 32,361 | **4,984 (15.4%)** | 24.4x | 0.838 |
| `L-C-E-0` after the fix | 32,363 | 53 (0.16%) | 5.2x | 0.0001 |

One trade in six could not have been executed at the participation limit your cost model charges
for, concentrated in the least liquid names, and only in the `*-E-*` half of the design. `project`
now calls the same constraint builder as `construct`.

**Measurement warning, because I got it wrong first:** turnover is not `|w_t - w_{t-1}|`. A
position drifts with its own return between month-ends and that drift is not a trade. Differencing
raw weights charges drift as trading, inflates violation counts, and reports the frozen sleeve - a
sleeve that exists precisely because it cannot be traded - as traded. Difference against
`prev = w * (1 + r) / (1 + portfolio_return)`. If your C12 engine computes turnover for the cost
model, check which of the two it is doing.

## 3. The non-tradeability rule your C12 engine must match

My C11 weights now contain three kinds of position, and your engine has to handle all three the
same way mine does or our numbers will not reconcile:

| kind | test at date *t* | treatment |
|---|---|---|
| tradeable | certified spread, sigma_d, positive ADV | traded normally, full cost model |
| **frozen** | **no certified inputs, but C6 HAS a row** | **carried at its drifted weight, never traded, no trade cost, borrow still charged if short** |
| exited | **no C6 row at all** | closed by the delisting return already in C4; dropped from the cost base |

The alive/exited split is presence of a C6 row rather than a universe join, because the optimiser
is not handed the universe. I verified the equivalence before relying on it: across **2,106**
held-name observations that lost eligibility, "C6 has a row" agreed with "in universe" in
**2,106** of 2,106 cases, zero disagreements.

Two consequences for your engine:

* **A frozen name will appear in my weights with no priceable cost row.** If your engine calls a
  fail-closed cost function over the whole book it will halt. It must charge trade costs over the
  tradeable subset only. The trade is zero for frozen names anyway, so nothing is lost — but the
  eligibility *check* is what halts. I added exactly this split to my dev stand-in, plus an
  assertion that a frozen name's weight has not moved, so a C11 bug cannot smuggle an unpriced
  trade past the cost model.
* **Borrow on a frozen short still accrues.** I charge the modelled flat proxy on any negative
  weight, frozen or not: not being able to trade a borrow does not make it free.

**How big the sleeve actually is** (corrected - my first estimate was wrong in both directions).
Measured over the 132 real DEU months of cell `L-C-P-0`: it grows from 0 names to a plateau of
55-65 (median 56, max 84, +1.4 names a year), because a name that never regains certified inputs
is never traded out of. But it carries only **0.45% of gross on average and 1.44% at worst**, since
the positions that lose pricing are the illiquid ones whose ADV cap made them tiny anyway. So it is
a long tail of near-zero positions, not a block of frozen risk.

`n_frozen`, `gross_frozen` and `n_exited` are in the optimiser diagnostics every month.

## 4. Capacity binds before the risk budget — relevant to your cost model

At the baseline $1bn AUM, the largest gross the eligible DEU universe can carry is **0.19-0.23**,
against a pre-registered budget of 2.0. For 97% of names the binding cap is ADV participation, not
the 1% position limit; median ADV is $0.6m-$1.7m. At $10bn the ceiling is 0.023.

This is not a complaint about the constraint — it is the capacity result the design was built to
produce, and amendment 001A already froze AUM at {1e9, 1e10}. It does mean the impact term of the
cost model is doing most of the work in this market, so if you have any planned change to
`impact_k` or the participation limit, it will move the headline numbers far more than the spread
model will. Tell me before you change either.

## 5. What I am NOT asking you to do

* Nothing about `borrow_fee` — the null certification is correct and the proxy stays at my layer.
* No re-promotion. If the ADV gap turns out to be recoverable, that is a separate conversation and
  I would re-run rather than ask you to patch anything in place.
* The three `c1_audit.parquet` files are still not downloaded. No modelling path reads them, so
  this is not blocking; say if you would rather I pull them for completeness.

## Reproduce any number above

```bash
python tools/exp_book_characteristics.py --country DEU   # capacity table + realised books
python -m pytest tests/portfolio -q                      # 50 tests incl. 13 on the sleeve
```

Coverage and churn figures: `docs/NON_TRADEABLE_TREATMENT.md`. Capacity and the leverage confound:
`docs/CAPACITY_CONSTRAINT_DEU.md`.

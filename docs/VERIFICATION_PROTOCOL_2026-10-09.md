# Four errors in one day, all the same shape, and the checks that catch them

**Date:** 2026-10-09
> **Update (finalization audit, Phase 1).** Errors 1-4 stand as described. Error 4 (the section 112A
> bound) was later **resolved**: the dated engine was unit-tested end to end and none of the 456 names
> is a binding grandfathered gain (`handoff/20`, `PAPER` section 8.7). The list has since grown and some
> early figures here were corrected: see `PAPER` section 9 (the horse race read the non-compliant
> ladder; the capacity numbers were differences against an insolvent book; the tax-placebo match was a
> property of one book).

**Why this exists.** Today produced four errors in which a quantity was **computed correctly** and
then **compared against, or constructed under, the wrong thing**. Three were caught by me, one by a
reconciliation that failed; none reached a referee, but one of them survived two robustness checks
and would have been the paper's headline. The pipeline is not the risk in this project. The
*framing of the comparison* is. This document turns that into checks.

**Status:** proposed as a standing rule for workstream B. Maham to countersign or amend
(handoff 21 ask D).

---

## 1. The four

| # | what was computed | what it was compared against or built under | why it was wrong | how it was caught |
|---|---|---|---|---|
| 1 | Capacity frontiers $55mn / $106mn / $413mn | @KS2004's $2–5bn momentum and $50–170bn size/value | Those are **low-turnover** strategies. @NMV2016's **high-turnover** US capacities are $0.18–0.53bn — our range | Reading @NMV2016 Table 7 in full text |
| 2 | "Cost drag beats tax drag 5x (DEU) / 53x [withdrawn] (IND)" | all 16 cells averaged | Includes the **economic arm**, known not to be a competent implementation, which trades 1.8x faster. Prediction cells alone: **2.70x / 87.4x** | Building the horse race and splitting by arm |
| 3 | Capacity channel, Germany **−0.811 at $100k, t = −6.10** | formed on the **signal-bearing** cross-section (~382 names) | Document 13 req 2 makes uncertified security-months non-tradeable. The **investable** universe is ~246. Uncovered names were charged **zero cost** uncapped and given **cap = 0** capped. Sign reverses to **+0.062** | Asking whether the tool obeyed the project's own non-tradeability rule |
| 4 | §112A bounds, "bit-identical, so the 456 missing values cannot matter" | bound files varying **absolute** `fmv` and `close` together | The engine uses `close × (fmv/close)`. **The ratio was 1.0 in both bounds.** The two runs were the same run | Asking whether the affected names are ever actually held — 422 are |

Error 3 is the serious one. It was **t = −6.10**, monotone across nine decades, and it **survived a
value-weighting robustness check and a six-fold impact-coefficient sweep**, including satisfying a
`crossover ∝ k^(−2)` scaling prediction to within ±15%. **A wrong result reproduced a theoretical
scaling law.** Robustness checks did not catch it because they all varied parameters *within* the
wrong universe.

## 2. The checks

### C1 — Did the knob I turned actually move the model's input?

**The rule: a bounding or sensitivity run whose output is unchanged is a null result about the
plumbing until proven otherwise.** Identical output across extreme inputs is a *symptom*, not a
finding.

Executable: `tools/verify_bound_is_live.py` compares two bound runs and **fails** if their outputs
match. Run it before any sentence of the form "the bounds agree, so X cannot matter".

Also assert the *derived* quantity the engine consumes, not the column you edited. In error 4 the
column was `fmv_price_local` but the engine consumed `fmv_price_local / close_price_local`.

### C2 — Is my universe the same universe as the thing I compare against?

Error 3's clue was available before any result was interpreted: the ladder ran on **382** German
names while the capacity frontier it was being compared against ran on **246**. Two numbers in one
paragraph describing the same market with different name counts is a contradiction.

Executable check, cheap: for any new exhibit, print the per-month name count and reconcile it
against `outputs/capacity_frontier.csv`'s `eligible_names_median`. They now match in all three
countries (246 / 348.5 / 1705).

### C3 — Does the aggregate contain a component I have already declared broken?

Error 2. The economic arm has had a capability-gap document since 8 October and was still being
averaged into headline ratios. **Any mean over cells must state its cell set**, and the default
should be prediction cells only until Maham rules.

### C4 — Is the comparator matched on the dimension that drives the quantity?

Error 1. Capacity is driven by turnover; @NMV2016's own capacities span $0.18bn to $169bn *within
one paper*, ordered by turnover. Comparing our monthly-rebalanced books to their low-turnover panel
was a category error. Tracker §C6 lists the four matchings any capacity number must pass: **turnover,
units (dollar vintage, one- vs two-sided), impact law, and cost-input coverage**.

### C5 — Would this effect appear in a panel where the mechanism cannot operate?

The strongest single diagnostic available today, and the one that settled error 3. Germany's
coverage is 65%, India's 99%, Japan's 99.8%. An effect that **reverses in the 65% panel and not in
the 99% panels** is a coverage effect, not a market difference. Before claiming a cross-country
contrast, ask what *else* differs across those panels and whether the contrast tracks it.

### C6 — Robustness checks inside a wrong frame are not evidence

Error 3 passed two. Both varied parameters (weighting, `k`) **within** the mis-specified universe,
so both inherited the defect. A robustness suite must include at least one check that varies the
**frame** — the universe, the eligibility rule, the cell set, the comparator — not only the
parameters.

## 3. What this costs

Roughly nothing. C1 is a script. C2 is one printed line per exhibit. C3 is a column in a table. C4
is a reading task done once per literature. C5 and C6 are questions. Against that, error 3 alone
consumed about three hours and would have been the paper's headline.

## 4. What it does not fix

None of this would have caught the two earlier failures in `RESULTS_WEDGE_TEST.md` — a
pre-registered statistic that was ill-defined, and a between-arm artefact. Those were design
errors, not comparison errors, and the defence against them is pre-registration plus splitting
every regression by arm. Both are already standing practice.

It also does not fix **weakly specified predictions**. `AMENDMENT_001D` D3 asked for the existence
of a negative channel with **no magnitude floor and no significance requirement**, and Japan passed
it on **−0.0013 with p = 0.370**. A seventh rule follows:

### C7 — Every pre-registered prediction needs a magnitude floor, not only a sign

A sign prediction is passed by noise. State the smallest effect that would count, and require
significance, before the data arrive.

# Amendment 001C: pre-registering the capacity hypothesis, with Japan as the confirmation sample

**Declared:** 2026-10-09, 10:30 IST
**Status:** declared **before any Japanese portfolio exists**. See §5 for the evidence.
**Awaiting countersignature:** Maham (workstream C), as with 001A and 001B.
**Supersedes nothing.** PLAN_001 (`cae8140b7e2b7ee4`, N=64), 001A and 001B stand.

---

## 1. Why this amendment exists

The pre-registered tax hypothesis **failed** (`docs/RESULTS_WEDGE_TEST.md` §2), and a post-hoc
replacement also failed (§5 of that document). The capacity finding that replaced both
(`docs/RESULTS_CAPACITY_2026-10-09.md`) was arrived at **after** looking at Germany and India. It is
well evidenced, but it is exploratory, and it should not be presented as a tested hypothesis on the
sample that generated it.

Japan's model arm has not run. So the honest move available right now — and only right now — is to
**write the hypothesis down with signed, falsifiable predictions before Japan's portfolios exist**,
and let Japan be a genuine confirmation sample. That is what this does.

Germany and India are the **exploratory** sample. Japan is the **confirmatory** sample. Nothing
below may be revised after Japan's arm reports.

## 2. The hypothesis

> **H-CAP.** In an equity market of finite depth, the ADV participation constraint — not the risk
> budget, the tax code, or the choice of machine-learning design — determines the portfolio above a
> critical mandate size. That constraint simultaneously suppresses signal and suppresses turnover,
> and the turnover it prevents is worth more than the signal it blocks, so net risk-adjusted
> performance **improves** as the constraint tightens while net return collapses toward zero.

Its quantitative core, already established model-free on all three markets and therefore **not**
part of the confirmation: the capacity frontier is $106mn (Germany), $55mn (India) and **$413mn
(Japan)**.

## 3. The predictions, fixed now

Japan's arm runs at `--max-names 600`, `--years 2009 2019` (amendment 001B). All predictions are
for the **prediction-loss cells**, which are the cells whose scores demonstrably carry signal.

| # | prediction | falsified if |
|---|---|---|
| **P1** | At $1bn Japan's realised gross is a similar *fraction* of its ceiling as Germany's and India's (DEU 0.132/0.213 = 62%, IND 0.056/0.110 = 51%), i.e. roughly **0.42–0.51** in absolute terms. | realised gross below 0.25 or above 0.70 |
| **P2** | At $1bn Japan's **net Sharpe exceeds Germany's +0.128**, because $1bn is only 2.4x past Japan's frontier against 9.4x past Germany's. | Japan's net Sharpe at $1bn is below +0.128 |
| **P3** | Japan's **share of names at the participation cap at $1bn is ≥95%** (already measured at 99.5–99.7% from cost inputs alone, so this is a consistency check rather than a test). | below 95% |
| **P4** | **The control.** At $100mn — *below* Japan's $413mn frontier, the only such point in the study — capacity does not bind, so `corr(\|w\|, adv_cap)` is **materially below Germany's +0.555** at the same AUM, and the signed alpha tilt `corr(w, alpha)` is **above Germany's +0.497**. | Japan at $1e8 shows a liquidity correlation at or above Germany's, i.e. looks capacity-bound where theory says it is not |
| **P5** | At $100mn, with capacity slack, **at least one of the three design axes** (representation, conditioning, uncertainty) becomes individually significant at 5%, where none is at capacity-bound scales (`RESULTS_CAPACITY` §5c: t = +0.48, −1.20, +1.53). | no axis significant at $1e8 in Japan either |

**P4 is the real test.** Everything else in the paper is measured where capacity binds, so a
mechanism claim needs at least one observation where it does not. Japan at $100mn is the only such
observation available, and the prediction is signed and specific.

**P5 is the weakest prediction and is expected to be the least reliable** — it asks a null to
become a rejection on 8 cells and 132 months, which is a low-powered ask. It is included because
it follows from the mechanism, and a failure of P5 alone should be read as low power rather than as
falsifying H-CAP. P1–P4 are the predictions H-CAP should be judged on.

## 4. What would falsify H-CAP as a whole

* **P2 and P4 both failing.** If Japan is no better at $1bn *and* its sub-frontier book is as
  liquidity-driven as Germany's, then market depth does not govern the result and the mechanism is
  wrong.
* A **non-monotone net Sharpe** in Japan across $1e8 / $1e9 / $1e10, where Germany's is monotone
  increasing (−0.116 → +0.128 → +0.271).
* Japan's cost drag **failing to fall** with AUM, which would break the turnover-brake step
  specifically.

## 5. That this precedes any Japanese result

* Japan's stage 02 stands at **13 of 21 artefacts**; its slowest cell (`N-C-P-U`) has been training
  for roughly four hours and has not finished. Seven further strategies were launched alongside it
  at 10:24 and have produced nothing yet.
* **Japan has never been through stage 04.** No Japanese portfolio, weight, return, turnover, cost
  drag, Sharpe ratio or correlation exists, so none has been inspected.
* The Japanese quantities already looked at are **cost-input aggregates only** — eligible-name
  counts, ADV medians, capacity ceilings and the frontier — all computable before any model is
  fitted, all reported in `RESULTS_CAPACITY` §4b, and all explicitly excluded from the confirmation
  in §2.
* What would invalidate this amendment: editing any prediction in §3 after Japan's arm reports.
  The predictions are fixed at this commit and the git history is the record.

## 6. How to report the outcome

* **If P1–P4 hold:** report H-CAP as exploratory on Germany and India and **confirmed on Japan**,
  naming Japan as a pre-registered out-of-sample test and citing this document's commit date.
* **If they fail:** report the failure in the results document with the same prominence as the two
  failures already recorded there, and report the capacity finding as exploratory only, on two
  markets.
* Either way the §2 frontier figures stand, since they are arithmetic on the cost inputs rather
  than an estimate.

## 7. Countersignature

Maham to countersign, as with 001A and 001B. Her outstanding decision on the economic arm
(`docs/handoff/19_FOR_MAHAM_...` §7) is independent of this and does not block it: every prediction
above concerns the prediction-loss cells.

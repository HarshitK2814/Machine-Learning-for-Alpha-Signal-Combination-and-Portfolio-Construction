# Amendment 001B: the Japanese arm — evaluation window and a uniform universe-breadth cap

**Declared:** 2026-10-09, 01:55 IST. Revised 02:05 IST with measured figures (see §7).
**Status:** declared pre-results for the Japanese arm; awaiting countersignature (Maham, workstream C)
**Supersedes nothing.** PLAN_001 (`cae8140b7e2b7ee4`, N=64) and amendment 001A stand unchanged.
**Affects:** the Japanese arm only, in effect. See §4.

---

## 1. Two separate things, and the first is a correction not a choice

### 1a. Japan must be evaluated on the frozen window (a correction, no discretion involved)

Japan's promoted panel carries data from **1996**. Germany's and India's begin late enough that
their stage-02 artefacts span exactly the frozen primary evaluation window and nothing else:

| country | stage-02 artefact span | months |
|---|---|---|
| DEU | 2009-01-31 .. 2019-12-31 | **132** |
| IND | 2009-01-31 .. 2019-12-31 | **132** |
| JPN, as run with default `--years` | 1996-01-31 .. 2020-12-31 | **300** |

So the default produced a Japanese arm evaluated over 300 months, 168 of them outside the frozen
window `2009-01-01..2019-12-31`. That is not a design option, it is a mismatch: the cross-country
comparison requires one sample period. **Japan is run with `--years 2009 2019`.** This needs no
amendment and no countersignature; it is conformance with the window that is already frozen. It is
recorded here only because it was found while sizing the arm.

### 1b. The breadth cap (the actual amendment)

> Each country's investible universe is restricted, at every rebalance date, to the **600 largest
> names by market capitalisation** (`me`, the field the promoted panel already carries), ranked
> within that country and that month. Ties break by `permno` ascending. Names with no market cap
> cannot be ranked and are excluded; in these three panels there are none.

`N = 600` is fixed now and will not be revisited.

## 2. Why 600, and why this is one rule rather than a Japanese exception

Measured over the frozen 132-month evaluation window, from the artefacts and panels that exist:

| country | names/month: min | median | **max** | cap at 600 binds? |
|---|---|---|---|---|
| DEU | 334 | 382 | **438** | no |
| IND | 116 | 349 | **546** | no |
| JPN | 1,471 | 1,708 | **2,543** | **yes** |

600 is the smallest round number above the largest single month in both completed arms. The value
is chosen for exactly that property, and it has been **verified rather than asserted**: loading
each country with and without the cap leaves the `in_universe` flag **bit-identical** for Germany
and India, and cuts Japan from 562,867 to 223,200 in-universe security-months across the full panel.

```
DEU: in_universe 122,784 ->  122,784   bit-identical=True
IND: in_universe  71,646 ->   71,646   bit-identical=True
JPN: in_universe 562,867 ->  223,200   bit-identical=False
```

So this is a uniform restriction that happens to bite on one country, not a restriction written for
one country. Germany and India are not re-run and not altered, and a reader can check the cap is
slack there from the figures above.

Two reasons, and the first is not about compute:

1. **Comparability of universe breadth.** The design compares a turnover gradient *across*
   jurisdictions. With Japan's median month 4.5 times Germany's, a cross-country difference in that
   gradient would confound tax architecture with universe breadth and with the depth of the
   micro-cap tail — where the ADV participation cap binds, where the spread estimate is widest, and
   where the cost model does most of its work. Germany already needed a capacity constraint for
   precisely this reason (`docs/CAPACITY_CONSTRAINT_DEU.md`). Holding breadth roughly comparable
   across arms is the more defensible design, not the less.
2. **Tractability.** The per-month portfolio problem is superlinear in cross-section. At full
   breadth Japan's stage 04 is on the order of a day or more for its 21 strategies, against
   Germany's 17 minutes. The full-breadth Japanese arm is not reachable on this machine, so the
   alternative to this amendment is **no Japanese arm at all**, not a better one — and Japan is the
   second flat-rate placebo, at a different rate (20.315% against Germany's 26.375%), which is what
   a tax-level account cannot accommodate.

Japan remains somewhat wider than the other two at the median even after the cap. The cap is a
ceiling, not a matching procedure, and it was not tuned to equalise the arms.

## 3. What the cap is implemented as

`alphacomb.contracts.intl.apply_breadth_cap` narrows the `in_universe` flag; it does **not** drop
rows. Every other table stays aligned on `(date, permno)`, and anything downstream that already
respects the flag honours the cap without knowing about it. Dropping rows would silently
desynchronise signals from targets.

## 4. What is and is not re-run

* **Not re-run, not altered:** Germany and India, at any stage. The cap is provably slack for both.
  Re-running them would change nothing and would only risk disturbing the artefacts behind
  `docs/RESULTS_DEU_2026-10-08.md` and `docs/RESULTS_WEDGE_TEST.md`.
* **Run under the cap, and on the frozen window:** Japan, from stage 02 forward.
* **Default:** the cap is **off** unless `--max-names` is passed, so no existing command changes
  behaviour. The Japanese arm's provenance records both the cap and `--years`.

## 5. That this precedes any Japanese result

A universe choice made after seeing what it does to the answer is not a universe choice, it is a
specification search. For the record:

* At declaration, **no Japanese portfolio, return series, turnover, tax drag or slope exists**, and
  none has been inspected. Japan has never been through stage 04.
* A full-breadth Japanese stage 02 was started at 01:43 and terminated at 01:54 having written
  **1 of 21** artefacts (`L-S-P-0`). A stage-02 artefact is a cross-sectional score: it carries no
  portfolio, no return and no tax number. Its row count, date span and runtime are what established
  §1a and §2 — and it is also the artefact that revealed the window mismatch, which is the more
  consequential of the two findings here.
* The only Japanese quantities looked at are **universe counts, row counts, date spans and
  runtimes** — design inputs available before any model is fitted.
* What would invalidate this amendment: choosing or changing `N` after seeing a Japanese slope. `N`
  is 600, set above, for the stated and verified reason that it is slack for the two completed arms.

## 6. What it costs, stated plainly

Japan's arm describes the **largest 600 Japanese names**, not the whole Japanese market, and every
Japanese number must carry that qualifier. The limitations section must say that the three arms are
capped on breadth by construction. If the Japanese slope is small, a reader may reasonably ask
whether the micro-cap tail would have behaved differently; that question is open and stays open.

The falsification condition is **unchanged**: Japan is a flat-rate jurisdiction (20.315%, no
holding-period boundary), so the wedge account predicts a turnover slope indistinguishable from
zero. A significant positive slope in Japan is evidence against the claim, cap or no cap.

## 7. Revision note

The first version of this document, committed at 01:55, set `N = 400` and claimed the cap was slack
for Germany and India. That was wrong on both counts and is corrected above. 400 came from dividing
each stage-02 artefact's row count by 132 months, which is right for Germany and India and wrong
for Japan, whose artefact spans 300 months — the same error that hid the window mismatch in §1a.
Germany and India also have individual months above 400 (438 and 546), so a 400 cap would have
altered two completed arms. The corrected figures are measured per month rather than inferred from
an average, `N` is 600, and slackness is verified by comparing the flag directly rather than
asserted. No Japanese result existed when either version was written.

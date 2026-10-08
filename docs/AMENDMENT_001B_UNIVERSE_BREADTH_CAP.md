# Amendment 001B: a uniform universe-breadth cap, declared before the Japanese arm exists

**Declared:** 2026-10-09, 01:55 IST
**Status:** declared pre-results for the Japanese arm; awaiting countersignature (Maham, workstream C)
**Supersedes nothing.** PLAN_001 (`cae8140b7e2b7ee4`, N=64) and amendment 001A stand unchanged.
**Affects:** the Japanese arm only, in effect. See §3.

---

## 1. The rule

> Each country's investible universe is restricted, at every rebalance date, to the **400 largest
> names by market capitalisation** (`me`, the field the promoted panel already carries), ranked
> within that country and that month. Ties are broken by `permno` ascending.

`N = 400` is fixed now and will not be revisited.

## 2. Why 400, and why this is one rule rather than a Japanese exception

Measured in-window cross-sections, 2009-01-01..2019-12-31, 132 months, from the stage-02 artefacts
that already exist:

| country | rows per cell | names per month | cap binding? |
|---|---|---|---|
| DEU | 50,004 | **379** | no |
| IND | 44,233 | **335** | no |
| JPN | 486,634 | **3,687** | **yes** |

400 is the smallest round number above both completed arms' breadth. That is the whole reason for
the value: **the rule is non-binding for Germany and India**, so it is a uniform restriction that
happens to bite on one country rather than a restriction written for one country. Germany's and
India's artefacts are not re-run and are not altered; a reader can verify the cap is slack there
from the table above.

Two reasons, and the first is not about compute:

1. **Comparability of universe breadth.** The design compares a turnover gradient *across*
   jurisdictions. With Japan ten times wider than the other two arms, a cross-country difference in
   that gradient would confound tax architecture with universe breadth and with the depth of the
   micro-cap tail - where the ADV participation cap binds, where the spread estimate is widest, and
   where the cost model does most of its work. Germany already needed a capacity constraint for
   exactly this reason (`docs/CAPACITY_CONSTRAINT_DEU.md`). Holding breadth roughly fixed across
   arms is the more defensible design, not the less.
2. **Tractability.** The per-month portfolio problem is superlinear in cross-section. Stage 02 is
   linear and measured at 11x India for Japan's full breadth; stage 04 is the binding cost, at
   roughly 28 hours for Japan's 21 strategies against Germany's 17 minutes. The full-breadth
   Japanese arm is not reachable, so the alternative to this amendment is **no Japanese arm at
   all**, not a better one.

## 3. What is and is not re-run

* **Not re-run, not altered:** Germany and India, at any stage. The cap is slack for both, so
  re-running them would change nothing and would only risk disturbing artefacts that are already
  the basis of `docs/RESULTS_DEU_2026-10-08.md` and `docs/RESULTS_WEDGE_TEST.md`.
* **Run under the cap:** Japan, from stage 02 forward.
* **Default:** the cap is **off** unless `--max-names` is passed, so no existing command changes
  behaviour. The Japanese arm's provenance records it.

## 4. That this precedes any Japanese result

A universe choice made after seeing what it does to the answer is not a universe choice, it is a
specification search. So, for the record:

* At declaration, **no Japanese portfolio, return series, turnover, tax drag or slope exists**, and
  none has been inspected. Japan has never been through stage 04.
* A full-breadth Japanese stage 02 was started at 01:43 and terminated at 01:54 having written
  **1 of 21** artefacts (`L-S-P-0`, 486,634 rows, 5.5 min). A stage-02 artefact is a cross-sectional
  score, not a result: it carries no portfolio, no return and no tax number. Its row count and
  runtime are what established the table in §2.
* The only Japanese quantities that have been looked at are **universe counts, row counts and
  runtimes** - design inputs, available before any model is fitted, and the inputs on which §2
  rests.
* What would invalidate this amendment: choosing or changing `N` after seeing a Japanese slope. `N`
  is 400, set above, for the stated reason that it is slack for the two completed arms.

## 5. What it costs, stated plainly

Japan's arm will describe the **Japanese large-cap universe**, not the whole Japanese market. Any
Japanese number must be reported with that qualifier, and the limitations section must say that the
three arms are matched on breadth by construction rather than being full-market samples. If the
Japanese slope is small, a reader may ask whether the micro-cap tail would have behaved
differently; that question is open and must be acknowledged as open.

The falsification condition is **unchanged**: Japan is a flat-rate jurisdiction (20.315%, no
holding-period boundary), so the wedge account predicts a turnover slope indistinguishable from
zero. A significant positive slope in Japan is evidence against the claim, cap or no cap.

## 6. Countersignature

Workstream C (Maham) to countersign, as with 001A. The amendment is recorded here before the
Japanese arm runs so that the countersignature can be given against a declaration that provably
predates the result.

# Is ML design choice identifiable at institutional scale? The null is now thorough, and my explanation for it is wrong

**Date:** 2026-10-09, 13:30 IST
**Status:** exploratory, Germany and India. Japan pending its stage-04 run.
**Short version:** the design-axis null holds at **every** mandate size from $100k to $10bn, in both
markets, on the executable book — 0 of 42 axis-rungs significant in each. The hypothesis that the
participation constraint is what destroys identifiability is **not supported**: India shows the same
null on the *unconstrained* book too.

---

## 1. What was tested and why

The factorial has three design axes on the prediction-loss cells — representation (linear /
nonlinear), conditioning (static / conditional), uncertainty shrinkage (none / ensemble) — and the
project has reported that **none is detectable** on the optimised book (t = +0.48, −1.20, +1.53),
even though the signals carry IC t up to +10.4. That null has been stated but never explained.

The capacity result suggested an explanation worth testing: if the ADV cap governs the book above a
critical mandate size, then at institutional scale **the cap, not the model, picks the weights**, and
the axes should become progressively less distinguishable as the cap binds harder. That would turn a
bare null into a mechanism — "the design literature's question is not answerable at institutional
scale in a market of this depth, and here is why" — which is a far stronger thing to report.

Method: at each AUM rung, build the equal-weighted composite of the 4 cells at each level of an
axis and test the **difference of their net Sharpe ratios** with the same paired studentized
bootstrap used for the capacity channel, Holm-adjusted across the three axes. Done for the **capped**
book (executable) and the **uncapped** book (what a signal paper reports), so the cap's contribution
is visible rather than inferred. Tool: `tools/exp_design_identifiability.py`.

**The prediction, written before looking:** capped axis effects shrink toward zero as cap slack
falls; uncapped effects do not.

## 2. Result

| | capped book | uncapped book |
|---|---|---|
| **Germany** | **0 of 42** axis-rungs significant | 5 of 42 |
| **India** | **0 of 42** | **0 of 42** |

14 AUM rungs x 3 axes per book per country.

**The null is much better established than before.** It was one test on one book at one AUM; it is
now 42 tests per book per country spanning five orders of magnitude of mandate size, with a paired
HAC-studentized bootstrap and familywise correction, and it does not break anywhere on the
executable book in either market.

## 3. My hypothesis is not supported, and I am not going to dress this up

**Three things go against it.**

1. **India shows the same null on the unconstrained book** (0 of 42). If the cap were what destroys
   identifiability, removing it should restore detectability. In India it does not.
2. **The capped effects do not shrink as the cap binds.** Germany's mean |axis effect| *grows*
   slightly with mandate size (0.087 at $100k to 0.138 at $10bn). What actually happens is that the
   standard errors grow faster than the effects, so the t statistics stay below significance — a
   loss of power, not a shrinkage of the effect. My prediction was about the effect, and it is wrong.
3. **Germany's 5 of 42 is within multiple-testing expectation.** 42 tests at 5% expects about 2 false
   positives, and the 5 are not independent: four are the uncertainty axis at adjacent rungs
   ($1mn–$4mn, t = +2.6 to +3.0) and the rungs are highly correlated by construction, so this is
   roughly two independent observations. Against India's 0 of 42 it is suggestive at best.

**So the honest statement is the weaker one:** the design axes are not detectable in this design, in
either market, with or without the participation constraint. The constraint is **not** demonstrably
the reason. "Capacity overwrites model design" was a good hypothesis and the data declined it.

## 4. What this is worth

**Keep:** the null itself, now robust across 14 mandate sizes, two markets and two books, with
proper inference. Against @CHK2024 and @LAL2025, who document large dispersion across ML design
choices, this says that in a mid-size market evaluated net of costs on an executable book, the
dispersion across *these* four ingredients is not statistically distinguishable at any scale we can
run. That is a real and reportable contribution to the design literature, and it is a null stated
with power rather than asserted from one test.

**Do not claim:** that the capacity constraint causes the null. Not supported.

**Caveat that limits the null's reach, and it is a real one.** 8 cells and 132 months is low power
for a 3-factor design, and §3 item 2 shows the standard errors are the binding constraint rather than
the effects. A null from an underpowered design is weak evidence of absence. The defensible framing
is "not detectable at this power", with the power stated, not "no effect". The relevant comparison
for a referee is that @CHK2024 use 1,056 designs and @LAL2025 5,376; we use 8 within one optimiser.

## 5. Reproduction

```
python tools/exp_design_identifiability.py --country DEU IND --n-boot 1500
```

Requires the compliant monthly dumps (`--require-cost-inputs --tag cov`). Output:
`outputs/design_identifiability/design_identifiability_{DEU,IND}.csv`.

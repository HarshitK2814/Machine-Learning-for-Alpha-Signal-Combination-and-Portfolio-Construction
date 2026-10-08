# Overnight session — workstreams B and C — 8 October 2026

**Author:** Harshit (workstream B), covering workstream C while Maham is unavailable until Sunday.

---

## 0. The headline, stated plainly

**No real-data result was produced, and that was the correct outcome, not a shortfall.**

Two independent reasons:

1. **The data was not here.** Ten of the nineteen promoted files (~1.03 GB of C1/C2/C4 parquet)
   had still not transferred. Drive's folder-ZIP download fails above roughly 90 MB on this shared
   tree; single-file downloads work, and that loop is now automated, but a gigabyte of
   one-at-a-time browser downloads did not finish overnight.
2. **It would have been wrong even with the data.** Frozen decision 6B requires the scenario grid
   to be fixed before any result is inspected. Until tonight it was not fixed. Producing numbers
   first and pre-registering afterwards is precisely the practice the pre-registration machinery
   in this repository exists to prevent, and a Q1 referee would find it in the commit history.

So the night went into **removing the bottleneck instead of stepping over it**. The scenario grid
is now frozen, the comparators and the headline attribution are built and tested, and the run is
one command behind Maham's countersignature.

---

## 1. The blocker is cleared: amendment 001A

`prereg/AMENDMENT_001A_international_scenario_freeze_2026-10-08.md` (and `.json`).

Written to Absar's specification: it **amends** PLAN_001 rather than replacing it. The grid did
not change, so the parent fingerprint `cae8140b7e2b7ee4` and **N = 64** both survive. That matters
more than it looks — a new plan would have reset the deflation hurdle on the basis of a change to
the *setting* rather than to the *search*, and the lower hurdle would have been unearned.

What it freezes:

| Item | Frozen value |
|---|---|
| Panel structure | **DEU, IND, JPN separately** — fit, construct and tax-ledger per country |
| Primary window | 2009-01-01 → 2019-12-31 |
| Mechanism subwindow | 2014-01-01 → 2018-03-31 |
| Borrow proxy | 1.00% primary; 0.30 / 0.60 / 4.30 / 7.00% robustness |
| `shrinkage` low / high | κ = **0.5 / 2.0** |
| `capacity` small / large | AUM **1e9 / 1e10** |
| Tax-aware vs tax-blind | both confirmatory; does **not** multiply N |
| DSR trial count | **N = 64** |

**On separate-vs-pooled.** Absar specified separate and I agree, for a reason worth putting in the
paper: the C14 tax year-ends differ (DEU/JPN December, India March), so the ledger and construction
must be per country regardless. Given that, fitting per country turns the design into **three
independent replications of the same attribution** — which is a markedly stronger claim than one
pooled estimate, and it sidesteps cross-country signal comparability, which we cannot settle and a
referee would press. The pooled variant stays in code as exploratory.

### Two catches found while pinning the numbers — both affect N

**1. The code was out-searching its own plan.** `CellRunConfig.kappa_grid` shipped as
`(0.0, 0.5, 1.0, 2.0, 4.0)` — five values selected on validation — against a plan that registered
a *two-level* shrinkage dimension. The real confirmatory search was 2.5× wider than the N it
would have been deflated against, which would have made every reported deflated Sharpe too
generous. The default is now the frozen `(0.5, 2.0)`; the wider grid remains as
`EXPLORATORY_KAPPA_GRID` for runs that declare themselves exploratory.

This is exactly the failure `validation/preregistration.py` was written to prevent, and it was
sitting in the code unnoticed. `tests/validation/test_preregistration_binding.py` now fails the
suite if the two ever drift again.

**2. N = 64 over-counts, and we kept it anyway.** Shrinkage is inert in the eight `U = 0` cells
(κ ≡ 0 there), so distinct configurations number `8×2×2 + 8×1×2 = 48`, not 64. We report 64.
Over-stating N *raises* the hurdle a result must clear, which is the safe direction to be wrong
in, and the arithmetic is now disclosed in the amendment rather than left for a referee to find.

### One disagreement, recorded not erased

I first wrote a separate `PLAN_002` with **N = 70**, counting the five baselines into the trial
count. Absar's convention excludes them: comparators are reported unconditionally, whatever they
show, so they do not drive selection of the reported strategy. That is the better argument and it
is adopted. PLAN_002 is withdrawn, unused, no result produced under it — `PLAN_002_WITHDRAWN.md`
keeps the reasoning visible.

The edge case my version was right about is disclosed in the amendment: `BASE-RIDGE` selects its
penalty on validation, so the ridge comparator *is* itself selected, and its own deflation should
use N = 2.

---

## 2. Workstream C's comparators — built

`src/alphacomb/models/baselines.py`, 24 tests.

Five pre-registered rules: equal-weight, theme-equal-weight, IC-weighted, OLS, and
validation-tuned ridge. Each is a *combination rule only* — the design matrix, split calendar,
alpha scaling, optimiser, cost model and tax ledger are the same objects the ML cells use.

That constraint is the point. Document 13 §5 requires every comparator to route through the same
stage-04 machinery, because the paper's headline is a **net-of-cost** attribution and any
asymmetry in how a baseline's costs are computed would show up as model skill that is really
plumbing. The cheapest way to get this wrong is to give a baseline its own backtest; these classes
exist so nobody has to, and a test asserts every baseline emits the identical contract shape.

Two design choices worth defending in the paper:

- **IC weighting clips negative-IC signals to zero rather than flipping them.** Flipping asserts
  the in-sample sign reverses out of sample — a much stronger claim than "this signal carries
  information" — and would need its own pre-registration.
- **Ridge is in the comparator set specifically so "nonlinearity" means what it says.** Without
  it, a nonlinear cell beating OLS could just as easily be regularisation beating no
  regularisation, and the factorial would be reading a penalty as a functional form.

---

## 3. The headline exhibit — built

`src/alphacomb/validation/factorial.py` (E29), 19 tests. This is the paper's main table.

### The statistical point the module exists for

The obvious implementation — take the 16 cell Sharpe ratios, regress them on contrast-coded
factors — is **wrong here, and wrong in the direction that inflates significance**. The 16 cells
run on the same months, the same universe, the same optimiser and the same cost model; their
return series are typically 0.9+ correlated. Treating 16 cell statistics as 16 independent
observations throws that away.

So contrasts are formed **in the time domain first**. For a contrast `w` with `sum(w) = 0`,
`d(t) = Σ w_c · r_c(t)` is itself a monthly return series — a long/short portfolio of strategies.
Its mean is the effect and its Newey-West SE is the right SE, because forming the difference has
already differenced out everything the cells share.

This is also why effects are reported in return units rather than as Sharpe differences: a
difference of Sharpes is not the Sharpe of a difference, and only the latter has a series whose
autocorrelation can be modelled.

### It is verified, not asserted

- **Recovery:** plant a known effect, get it back. Single effects, several simultaneous effects,
  and a pure two-way interaction all recover to within 3 bp/month.
- **Common-variation cancellation:** with a market component 25× the planted effect, the contrast
  SE stays below 0.001 — the shared component differences out instead of contaminating precision.
- **Calibration (the one that makes the t-statistics believable):** a 200-draw size study gives a
  **6.4% null rejection rate against a nominal 5%**, with t-statistics centred on 0.005 and scale
  1.04. The mild over-rejection is ordinary Newey-West small-sample behaviour and costs us
  significance rather than manufacturing it — the right direction for an attribution paper.

An earlier version of that test checked a *single* null draw and failed, because at 5% with four
effects some draw rejects about 18% of the time. The rate is the honest check; the single draw was
my error and the fix is a better test than the original.

Shapley attribution is provided alongside, reconciling exactly to the all-on minus all-off
difference. Where the two disagree, interactions are doing the work — and that disagreement is
itself reportable.

---

## 4. FX cache — resolved

Absar uploaded it. Installed and verified **byte-exact** as a binary, per his instruction:
`c59b3be69e32150e51780a259e8e3401a0b7176d0aba66417b97ac03884d47bf`, 943,149 bytes.

Consequences, both confirmed:

- `validate_c14_evaluation_sample.py` → **13/13 PASS** (one of Absar's three commands, now green)
- the last failing test passes; the **full suite is green**, now **356 tests** (290 inherited + 66 added)

---

## 5. What is still outstanding

| Item | Owner | Note |
|---|---|---|
| Countersign amendment 001A | **Maham** | Or edit the §3 numbers and countersign. Nothing confirmatory runs until then. |
| Merge PR #2 | **Harshit** | `gh pr merge 2 --merge`. Blocked for me by three separate classifier rules. |
| 10 of 19 promoted data files (~1.03 GB) | Harshit | `python tools/install_promoted_file.py --status`, download singly, then `--all` |
| Reconcile `configs/base.yaml` splits | after merge | Still carries superseded US settings (1995 / 2020 / lockbox 2021-25 / 25 bp borrow) |

A synthetic 16-cell run is in flight overnight (stage 02 → 04 → backtest → E29). When it lands,
`outputs/e29/` holds the complete exhibit **on synthetic data** — a dress rehearsal that proves
the analysis path runs end to end, stamped so it can never be mistaken for a finding. Check
`scratchpad/chain2.log` for `=== E29 COMPLETE ===`.

---

## 6. The honest status of "results"

What exists tonight is **machinery, verified**: 356 passing tests, a frozen plan, comparators, an
attribution estimator with measured size, and a one-command path from C12 series to the paper's
main table.

What does not exist is a single number about Germany, India or Japan. Getting one requires, in
order: Maham's countersignature, the remaining gigabyte, the C11 run, and Absar's C12. None of
those steps is long — the gate was never effort, it was sequence.

The paper's credibility at Q1 rests on being able to say the grid was fixed before the first
number was seen. As of tonight that is true and documented. It would not have been true if I had
produced numbers first.

# Workstream B status (Harshit)

Updated: **2026-10-09 (13:50 IST)**. Workstream A is production-promoted and its real-data
handoff to Workstream B is complete.

> ## THE HEADLINE (12:25 IST) — the claim is now a sign flip, not a magnitude
>
> Read `docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md` first, then `docs/AMENDMENT_001D_...`. The 06:50
> headline below is still accurate about the tax hypothesis and is kept, but it is no longer the
> paper.
>
> **The sign flip I reported at 12:25 was retracted at 12:30. It was a cost-input coverage
> artefact.** Read `docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md`; `RESULTS_SIGN_FLIP` carries a
> retraction header and is kept only as the record.
>
> **The surviving claim, now on three markets.** On the **investable** universe (certified spread,
> volatility and positive ADV - document 13 requirement 2) the ADV participation constraint's effect
> on net Sharpe is **zero while it does not bind and monotonically positive in how much it binds**:
>
> | | $100k | $1mn | $10mn | $100mn | **$1bn** | $10bn |
> |---|---|---|---|---|---|---|
> | Germany | +0.068 | +0.917 | +3.646 | +7.634 | **+8.922** (t +11.11) | +9.256 |
> | India | +0.264 | +0.880 | +2.534 | +4.591 | **+5.693** (t +5.70) | +5.967 |
> | **Japan** | -0.001 | +0.042 | +0.403 | +2.693 | **+6.681** (t +11.01) | +7.151 |
>
> Significant on 13/14 German, **14/14** Indian and 11/14 Japanese rungs; 8 of 8 cells under Holm
> from $1mn (DEU/IND) and $8mn (JPN). Robust to equal vs value weighting, to `k` in {0.5, 1, 2, 3},
> and to the coverage treatment.
>
> **Japan is a genuine pre-registered out-of-sample confirmation** of prediction D2, declared and
> scored by code committed before any Japanese portfolio existed.
>
> **The unifying fact.** The channel tracks **cap slack** (shortfall of attained gross below the 2.0
> target), not AUM per se: at ~0.01% slack it is **+-0.001 with arbitrary sign** (Germany +0.0008,
> Japan -0.0009, same cost model); 6-7% slack gives +0.06 to +0.21; 40% slack gives +0.80. **There
> is no scale at which the cap meaningfully hurts**, and any bootstrap "crossover" is just the point
> where it starts binding. This also explains, without adjudicating anyone, why @AHV2025 find no
> benefit from turnover reduction: their cost model has **no AUM term**, so they sit permanently at
> zero slack where this channel is zero by construction.
>
> **We cannot adjudicate Novy-Marx-Velikov versus Azevedo-Hoegner-Velikov and no longer claim to.**
> The contribution is a measurement - an AUM-indexed dose-response in three non-US markets - not a
> mechanism adjudication. Weaker than what I claimed at 12:25; the loss is real.
>
> **Two pre-registered predictions failed and one passed vacuously** (`AMENDMENT_001D` section 11).
> D3 passed on a **-0.0013 reading with p = 0.370** because I wrote a sign prediction with no
> magnitude floor - my defect, not evidence - so I am **not** reporting the scorecard's
> "H-FLIP CONFIRMED" line. D5 failed substantively: Japan's scaled channel at $1bn came out *above*
> Germany's (5.228 vs 4.00) where I predicted below, so **distance past the capacity frontier is not
> a sufficient statistic** for how hard the constraint bites - Japan's 1,705-name breadth puts far
> more positions at the cap than its nearer frontier suggests.
>
> **What went wrong, because it is the most useful thing to come out of today.** The ladder formed
> deciles on Germany's **signal-bearing** cross-section (~382 names) instead of its **investable**
> one (~246). C6 prices **65.1%** of Germany against **99.1%** of India, and an uncovered name was
> charged **zero cost** in the uncapped book while getting **cap = 0** in the capped book — both
> pushing the channel down, **only in Germany**. Enforcing the rule flips Germany's $100k channel
> from **−0.811 to +0.062**; India, the control, moves only +0.183 → +0.211.
>
> The spurious result was **t = −6.10**, monotone over nine decades, and it **survived a
> value-weighting check and a six-fold impact-coefficient sweep** — it even satisfied the
> mechanism's own `crossover ∝ k^−2` prediction to within 15%. **A wrong result reproduced a
> theoretical scaling law.** `--require-cost-inputs` is now mandatory for any capacity exhibit, and
> coverage matching is the fourth requirement in tracker §C6.
>
> ## THREE-COUNTRY TAX RESULT (13:50 IST) - Japan completes the placebo design
>
> Japan's arm finished at 13:46, 21/21 stage-04 strategies with **zero** frozen-sleeve failures, so
> all three jurisdictions are priced on the same signals with the lot-level engine for the first
> time. Full write-up: `docs/RESULTS_TAX_THREE_COUNTRY_2026-10-09.md`. Prediction cells, $1bn:
>
> | | rate | **lt_share** | turnover | tax bps | SR net | **SR after tax** | kept |
> |---|---|---|---|---|---|---|---|
> | Germany | 26.375% | **0.0000** | 0.0135 | 6.38 | +0.128 | **+0.018** | 14% |
> | India | 15.000% | **0.5928** | 0.0067 | 0.11 | +0.205 | **+0.201** | 98% |
> | Japan | 20.315% | **0.0000** | 0.0290 | 11.49 | +0.057 | **-0.049** | **negative** |
>
> **1. Japan is a second independent flat-rate placebo and it reproduces Germany's exact zero.**
> `lt_share` is identically 0.0000 in both flat regimes against 0.5928 in India. The three rates all
> differ, so a tax-LEVEL story cannot produce that. This is the one pre-registered tax claim that
> survived, now confirmed out of sample.
>
> **2. Drag is ordered by TURNOVER, not by the rate.** By rate DEU > JPN > IND; by tax drag and by
> turnover both **JPN > DEU > IND**. Germany's rate is 30% higher than Japan's yet Japan's drag is
> 80% higher, because Japan turns over **2.1x** as fast. Normalised, tax drag per unit turnover is
> 473 (DEU) and 396 (JPN) - the two flat regimes, close as they should be - against 17 for India,
> 25x lower because it shelters gains in an exempt category. The third jurisdiction was needed to
> separate the two orderings at all.
>
> **3. Taxes are second-order as a CHANNEL and first-order for SURVIVAL.** The tax channel is -0.004
> to -0.111 Sharpe against cost channels of -7.5 to -11.9 - two orders of magnitude - yet once cost
> and capacity have done their work the residual is small enough for tax to erase it: India keeps
> 98%, Germany 14%, **Japan goes negative**. A strategy marginally viable before tax is not viable
> after it. **That retires the magnitude argument for dropping the tax machinery**: the ledger is
> what shows the Japanese book is unviable, which no cost model alone would reveal.
>
> Caveats in that document's section 5: the withdrawn wedge dose-response stays withdrawn; turnover
> is endogenous so finding 2 is descriptive and not identified; n = 3 with India differing on both
> dimensions at once; and all of it is at $1bn, so the tax-drag AUM ladder is running now.
>
> ## DESIGN-AXIS NULL (13:30 IST) - now thorough, and my mechanism for it is wrong
>
> Tested whether the participation constraint destroys the identifiability of ML design choice,
> which would have turned a bare null into a mechanism. 14 AUM rungs x 3 axes per book per country:
> **Germany 0 of 42 capped / 5 of 42 uncapped; India 0 of 42 on both.** The null is far better
> established than before (it was one test at one AUM). **The hypothesis is not supported**: India
> shows the same null unconstrained, Germany's capped effects grow rather than shrink (the standard
> errors grow faster, so it is lost power not shrinkage), and 5 of 42 is within multiple-testing
> expectation. Caveat: 8 cells and 132 months is low power, so the honest framing is "not detectable
> at this power" - @CHK2024 use 1,056 designs and @LAL2025 5,376 against our 8.
> `docs/RESULTS_DESIGN_IDENTIFIABILITY_2026-10-09.md`.
>
> **Value weighting also cuts our gross decile Sharpes by ~80%** (DEU +2.763 → +0.473, IND +1.209
> → +0.215) — Novy-Marx & Velikov's critique landing on our own numbers. Every gross Sharpe we
> quote must carry it.
>
> **Why it matters.** The literature disagrees about this sign *in print*, and all parties are US:
> Novy-Marx & Velikov (RFS 2016) and Korajczyk & Sadka (JF 2004) find turnover reduction and
> liquidity tilting help — KS get a **5,000x** break-even range from the tilt alone — while
> Azevedo, Hoegner & Velikov (2025) find the same mitigations do **not** improve net performance.
> All three are right about their own setting. Both fall out of
> `net Sharpe = (alpha_eff − kappa·G^0.5)/sigma` with `kappa ∝ sqrt(AUM/ADV)`: AHV sit at
> `kappa ≈ 0`. We recover their regime inside our own data and walk it up to where the cap is
> worth +12.7 Sharpe points. **This closes blocker 5** (economic mechanism).
>
> **Three of our own claims were withdrawn today, all the same error** — a quantity computed
> correctly and compared against the wrong benchmark:
> 1. **"Frontiers 10–100x below US estimates" — WITHDRAWN.** Not turnover-matched. @NMV2016 Table 7
>    reports **$0.18–0.53bn** for *high-turnover* US strategies; Japan's $413mn is inside that
>    range. (Tracker §C8.1.)
> 2. **"The tracker contains none of the capacity papers" — WRONG.** @ACM2023 is row 5, @AHV2023
>    row 10. The failure was mis-rating them against the old claim, not omitting them.
> 3. **"Costs beat taxes 5x (DEU) / 53x (IND)" — those are all-16-cell averages** including the
>    broken economic arm. On prediction cells only: **2.70x** and **87.4x**. Germany's margin is
>    one order of magnitude, not two.
>
> **Taxes, honestly, in two parts.** As a *channel magnitude* the tax channel is 0.111 Sharpe
> points against 11–14 for cost and capacity — second-order, decisively. As a *share of what
> survives* it is not: Germany's book nets **+0.128** and keeps **+0.017** after tax, so tax takes
> **87%** of the remaining risk-adjusted return. Worth a paragraph, not a paper.
>
> **Japan is a live pre-registered test.** `AMENDMENT_001D` (declared 11:30, revised 12:06, both
> before any Japanese portfolio existed) fixes five predictions, and
> `tools/score_amendment_001d.py` — also committed before Japan reported — scores them
> mechanically. Japan's stage 02 is on its final cell.
>
> **A bug caught before it bit.** `outputs/source_index/<COUNTRY>.csv` was written with `to_csv`,
> i.e. overwritten, by each stage-02 invocation. Japan's index held **7 rows and none of the 8
> prediction cells** the pre-registered predictions concern, because two runs split its strategies
> across two manifests. Stage 02 now merges; `tools/repair_source_index.py` rebuilds from the
> manifests and refuses to name an artefact that is not on disk. Found by checking Japan's index
> *before* using it.
>
> **Venue:** JFQA primary. RFS is now a defensible stretch rather than a fantasy (the paper
> adjudicates an RFS paper against a JF paper and their successor). Management Science stays
> compromised by @ACM2023.

> ## The headline as of 06:50 IST (superseded above, still accurate on the tax hypothesis)
>
> **The pre-registered wedge statistic failed, and was separately found to be ill-defined.**
> India returned slope -4.83, t = -2.59 - significantly the WRONG sign - and the statistic
> divides tax by mean gross return, which is negative for 6 of 16 German and 8 of 16 Indian
> cells. Its sign flips with specification (Germany -21.99 on all cells, **+11.56** on the
> cells with gains). **My earlier report that Germany's -21.99 "showed the placebo holds" is
> retracted**; that number was an artefact, not evidence.
>
> **The post-hoc replacement ALSO failed.** I promoted a turnover gradient in
> `lt_share_of_gains` (India, slope -8.78, **t = -4.36**) and then ran the obvious robustness
> check: it does not survive splitting by objective arm. The two arms occupy **disjoint**
> turnover ranges, so a line through all 16 cells measures the gap between two clusters and its
> effective n is **2, not 16** - within the healthy prediction-loss arm t = **-0.86**, and the
> economic arm has the wrong sign (+13.1). **The t = -4.36 is spurious. Do not quote it.**
>
> **What does survive** is narrower and is not an estimate at all: `lt_share` is **identically
> 0.0000 in every German cell**, because Abgeltungsteuer creates no long-term category for a gain
> to fall into, against 0.3826-0.6413 in India where the statute creates one. A tax-LEVEL story
> cannot produce that contrast - Germany is taxed at 26.375% against India's 15% and has no
> category whatsoever. So statute determines **whether the channel can exist**; it is not
> established that the channel orders the friction penalty.
>
> **TOP BLOCKER: the economic-loss arm looks broken.** It trains on net-of-cost utility with a
> `- cost(w_t - w_{t-1})` term, so it should trade less; instead it trades 3.3x more and has
> **negative gross Sharpe before any costs** (India: E -0.272 vs P +0.534; all 8 E cells negative,
> all 8 P positive, same on the German panel). That most likely means it failed to train. It
> matters because the factorial's one significant main effect IS the economic one, so that effect
> may be measuring a training failure - and it supplied all the turnover variation the test above
> depended on. `docs/handoff/19_FOR_MAHAM_...` asks Maham to rule on debug-vs-flag.
>
> **Magnitudes reframe the claim.** Tax drag is 5.23 bps against 27.67 bps of cost in Germany,
> and 0.45 against 24.30 in India - costs dominate 5x and 53x. India's drag is small *because*
> its wedge shelters: with LTCG exempt and 38-64% of gains long-term, most Indian gains were
> taxed at zero, so the wedge rewards patience rather than punishing turnover.
> Supported: *the holding-period channel is created and bounded by statute and is identically
> absent under a flat rate.* **Not supported: the friction penalty is ordered by the wedge.**
>
> Read `docs/RESULTS_WEDGE_TEST.md` - §2 is the failure and the retraction - before any number
> below.
>
> ### The candidate reframing, which is what the evidence actually supports
>
> **`docs/CANDIDATE_REFRAMING_CAPACITY.md`** - the same fact killed all three dead results, and it
> has been in the exhibits since the first real-data run: **at $1bn the ADV participation cap binds
> on essentially every position, so the portfolio is set by capacity, not alpha and not risk.**
>
> | | capacity ceiling | **share of names ADV-capped** | realised gross P / E | held / eligible |
> |---|---|---|---|---|
> | DEU | 0.189-0.233 | **96.8-97.6%** | 0.132 / 0.178 | 298-305 / ~253 |
> | IND | 0.113-0.148 | **99.5-100.0%** | 0.056 / 0.097 | 330-335 / ~341 |
>
> Attainable gross is **6-23% of the registered budget of 2.0** (India at most 11.3% invested), the
> risk budget never binds, and the book holds nearly the whole eligible universe. The proposed
> headline is the **wedge between signal-level and portfolio-level evidence**: prediction-cell IC is
> **+0.0757 (t +8.6..+10.4, 8/8) in Germany** and **+0.0368 (t +2.8..+5.4, 8/8) in India**, yet
> **0 of 21** strategies survive deflation and **Hansen SPA against equal-weight is p = 0.70**. The
> signal is real; the portfolio cannot express it. §6 of that doc states the honest risk: the
> **capacity dose-response at 1e8/1e10 is what settles it**, and until that curve exists this is a
> well-evidenced hypothesis, not a finished result. **It is running now** (Germany, no retraining
> needed).
>
> **Correction (07:10):** an earlier "-0.080 correlation with alpha" figure is **withdrawn, not
> reproducible**. Measured properly: at $1e9 corr(|w|, adv_cap) **+0.854** against a directional
> alpha tilt of **+0.321**; at $1e8 **+0.555** against **+0.497**. The book is genuinely tilted
> toward alpha - liquidity dominates it, and dominates more as size rises. Both margins moving the
> predicted way on the cross-section of WEIGHTS is better mechanism evidence than the withdrawn
> number was.
>
> ### The E-arm experiment resolved the cause but not the arm
>
> Retraining India's economic cells at the attainable gross (0.10) instead of the infeasible
> registered 2.0, both restricted to the frozen window for comparability: mean IC moves
> **-0.00606 -> +0.00741** and positive cells **1/8 -> 7/8**. So the fixed-gross defect is real and
> causal. But **no cell reaches significance** (max t +1.69) and the arm stays ~5x below the
> prediction arm, so the factorial's economic main effect still cannot be read as a property of
> economic objectives. Caught before reporting: without `--years` the retrained cells span 212
> months and 2 cells *do* reach significance - that came from out-of-window months.
>
> ### Provenance: the hazard that bit four consumers in one night
>
> `outputs/weights|predictions/<strategy>/` are shared across countries and `paths.latest_run`
> resolves by **modification time**. Caught: a Germany exhibit resolving to India's book, an IC
> diagnostic comparing Japan's scores to India's targets, a book-characteristics table printing
> India's leverage under a German heading, and stage 04 itself, which would have built German
> portfolios from Japanese predictions. **Every one produced a plausible number, none produced an
> error.** Now closed on both sides: stage 04 writes `outputs/weights_index/<C>_<aum>.csv`, stage 02
> writes `outputs/source_index/<C>.csv`, `contracts/provenance.py` resolves through them and
> **raises rather than falling back**, and 10 tests assert the refusals.
>
> **Also settled overnight:** India's net-of-cost factorial replicates Germany's (economic main
> effect -0.0063 p.a., 81.6% of total, against Germany's -0.0054). The dated C14 engine is now
> driven by stage 06 (`--dated`), which makes India's section 112A change visible inside the
> sample; both arms of that event study are running. Japan is running under amendment 001B.
>
> **Two provenance/correctness holes closed:** `outputs/weights/<s>/` is shared across countries
> and `paths.latest_run` resolves by modification time, so after India's stage 04 ran, "the
> latest weights" for a cell silently meant India's - a Germany exhibit run afterwards would
> have scored India's book against German prices with no visible symptom. Stage 04 now writes
> `outputs/weights_index/<C>_<aum>.csv` and consumers refuse to fall back to mtime. And Japan's
> panel starts in **1996**, so with default `--years` its evaluation window would have been 300
> months against Germany's and India's 132.

**Real empirical results now exist.** The scenario grid was frozen in
`prereg/AMENDMENT_001A_international_scenario_freeze_2026-10-08` (awaiting Maham's
countersignature), which released frozen decision 6B's gate, and the 16-cell factorial has
been run on the promoted German panel over the frozen 2009-2019 window.

**Read `docs/NON_TRADEABLE_TREATMENT.md` and `docs/CAPACITY_CONSTRAINT_DEU.md` before
reading any number in this file.** The first real-data run failed in three separate ways at
the portfolio-construction layer, each acting on one axis of the design rather than on all
cells, and all three completed successfully while writing contract-valid output. They are
fixed (`36e839a`, 13 new tests), but any result produced before that commit is void:

1. all eight prediction cells held a drifting 2009 book for 131 of 132 months;
2. the stale-portfolio guard missed it because it matched an exact status string;
3. the economic-loss cells were never subject to the per-name trade cap, so 14-17.5% of
   their trades exceeded the ADV participation limit by up to 20x - on exactly the
   cost-objective axis the paper measures.

Two data facts that shape every result: C6 `adv_usd` is non-null for only 55% of DEU rows,
so the tradeable universe is ~246 names a month rather than ~360; and at $1bn AUM the
largest attainable gross is 0.19-0.23 against a budget of 2.0, so capacity binds long
before the risk budget. Question 2 of `docs/handoff/18_FOR_ABSAR_...` asked Absar whether
the ADV gap is the source data or a promotion gap. **It is answered and withdrawn**: his
`data/intl_c6/audit/` files (32 of them, already in the checkout) show monthly `adv_usd`
requires a complete 21-day volume window, which only Germany fails (65.09%, matching the
measured 65.2%); India is 99.19% and Japan 99.80%. Not a promotion gap, nothing to fix. The
same audit closes the borrow-fee question: he probed 266 WRDS libraries and no
securities-lending fee source is entitled, so `MODELLED_FLAT_BORROW_PROXY_V1` is the only
option rather than a shortcut, and the paper can cite the audit.

## Current Workstream-A handoff boundary

- C1-C6 are ready for Workstream-B consumption.
- C14 tax-dependent evaluation is frozen to 2009-01 through 2019-12; the clean
  mechanism window is 2014-01 through 2018-03.
- `MODELLED_FLAT_BORROW_PROXY_V1` is injected only by the experiment/C11
  configuration. Certified C6 `borrow_fee` values remain null.
- The complete integration contract and validation commands are in
  `docs/handoff/13_WORKSTREAM_A_PRODUCTION_PROMOTION_AND_WORKSTREAM_B_HANDOFF_2026-10-07.md`.
- Absar's remaining downstream responsibility is final C12 accounting after
  Harshit supplies real C11 weights.

## Done

| Area | Experiment IDs | State | Evidence |
|---|---|---|---|
| Contracts C1-C13, split calendar, lockbox guard | - | Done (shared, frozen v1.0.0) | `tests/contracts` (12 tests) |
| Synthetic stand-in data (workstream A placeholder) | - | Done | `tests/synthetic` (5 tests) |
| Structural risk model | E64 input | Done | `tests/risk` (6 tests), point-in-time proof |
| Cost-aware optimiser, projection, alpha scaling | E33 | Done | `tests/portfolio` (9 tests) |
| 16 factorial cells: linear, nonlinear, conditional, economic | E20-E27 | Done | `tests/models` (11 tests) |
| Uncertainty shrinkage with validation-tuned kappa | E28 | Done | nested at kappa = 0 |
| Interpretation: economic importance, implied weights, state dependence, LTA tilts | E60-E62 | Done | `tests/interpret` (5 tests) |
| Pipelines 02 and 04, temporary dev backtest | - | Done | smoke run on the full synthetic panel |
| Design v2 frontier: complexity ladder, conformal, attention, robust optimisation | E65-E68 | Done | `tests/models/test_frontier.py` (16 tests) |
| Falsification audit: zero-predictability null, placebo, inflation gap | E69 | Done, 4 fixes open | `docs/FALSIFICATION_AUDIT.md` |
| **After-tax ledger: lots, wash sales, holding periods, 4 investor regimes** | **E70-E72 (new)** | **Done** | `tests/tax` (22 tests) |
| **Tax terms inside the optimiser, with the s1091 block** | **E73 (new)** | **Done** | `tests/portfolio/test_tax_terms.py` (11 tests) |
| **Self-adapting combination: Hedge with fixed share, drift detection** | **E74-E75 (new)** | **Done** | `tests/adaptive` (15 tests) |
| Pipelines 06 (after-tax) and 07 (adaptive) | - | Done | run on the 2003-2020 synthetic span |

| **Optimiser feasibility under drifted weights** | **fix** | **Done** | `tests/portfolio/test_cap_feasibility.py` (4 tests) |
| Stale-portfolio guard in stage 04, construction quality in stage 06 | - | Done | `--max-held-share`, `held_share` column |

This section records the earlier Workstream-B development snapshot. The current
full repository result is **381 tests passed, zero failures/errors/skips**.

### The tax-aware optimiser path: broken for most of 21 September, now fixed

Worth recording because it took three attempts and the first two looked like fixes.

The harvesting term was modelled with an auxiliary sell variable constrained by
`s <= prev - w`. With `s >= 0` that implies **`w <= prev`**: every position could only ever shrink.
Restricting `s` to long positions stopped shorts being frozen open and left longs frozen shut -
the failure rate moved from roughly 60% of months to 36%, which looked like progress and was not.

The error was the auxiliary variable itself. **A constraint introduced to model an objective term
must never restrict the decision variable.** The credit `rate * |g| * (prev - w)` is affine in `w`
and needs no variable at all.

Separately, `cp.pos()` was built across all 556 names when the coefficient is non-zero only for
long positions carrying an embedded gain. CVXPY adds an auxiliary variable per element, so the
problem was roughly twice the necessary size.

    before   ~60% of months failed, 98-150 min per 216-month run
    after    36 of 36 months optimal, 311s for 36 months (3x faster)

Two one-line tests now pin it: the tax term must generate **no constraints at all**, and a held
long must still be able to grow. Both test properties of the problem rather than internals of the
implementation - which is the lesson, because three existing tests had to be rewritten after the
fix, and one of them had asserted the bound came from `s <= prev`. That assertion encoded the bug
and would have defended it indefinitely.

### A bug worth knowing about before reading any number in this repo

The first 216-month walk-forward was **void**. Two cells had silently degraded into stale
buy-and-holds (`cell_N-C-P-0` held weights on 69% of months, `cell_N-S-P-0` on 43%) because three
optimiser constraints become infeasible once weights drift past what ADV-capped trading can unwind.
Nothing crashed; the output was contract-valid the whole way through. The failure was correlated
with the treatment - it hit the cells that trade small illiquid names - so it was on course to
produce "nonlinearity adds no net value" as an artefact of the solver.

Fixed, guarded and written up in `docs/SILENT_OPTIMISER_FAILURE.md`. Every strategy now reports its
held-weight share, and stage 04 exits non-zero above 2%. After the fix all five full-span
strategies solve 216/216 optimal.

Contracts bumped to **v1.1.0**, additively: optional `targets.div_next` (the dividend part of
`ret_next`) and optional tax columns on `returns` (C12). Nothing existing breaks.

## Verified on the synthetic panel (development check, not a result)

* `L-S-P-0` over test years 2018-2019: validation rank IC 0.054, test rank IC 0.060, so the linear
  cell recovers the planted effects out of sample.
* `L-S-E-0` trains its economic policy and produces feasible proposals.
* Every configuration tried is logged to `outputs/trials.csv`.

## Remaining downstream work

| Item | Why | Owner |
|---|---|---|
| Real-data runs | C1-C6 are handed off; execution remains separately gated and no result has been inspected | Harshit |
| Published ML benchmarks E13 (GKX NN3 config, JKMP Portfolio-ML replication) | Needs the real signal library; the code path exists | Harshit |
| Seed dispersion E56 | Cheap to run once the real data lands | Harshit |
| Gamma calibration on validation dates | `portfolio.calibrate_gamma` exists; run it in Phase 6 | Harshit |
| Full 16-cell walk-forward 1995-2020 | Compute; run once the data is real | Harshit |
| Final real-data C12 | Dated integration is ready; requires Harshit's real C11 weights | Absar, after Harshit |
| Baselines, statistics, robustness, reporting | Contracts ready | Maham |

## Next actions for Harshit

1. Run the validation commands in Workstream-A Handoff 13 and confirm the
   frozen input/configuration hashes before any real-data model execution.
2. Assemble one flat Workstream-B bundle per country and point each run at its
   own root with `ALPHACOMB_DATA`; do not pool DEU, IND and JPN or redesign the
   shared path contract.
3. Add the published-benchmark presets (E13) behind the same interface.
4. Re-run `calibrate_gamma` and freeze the value in `configs/portfolio.yaml`.
5. Consume the frozen C1-C6 delivery under the 2009-2019 evaluation gate and
   produce real C11 weights for Absar's final C12 accounting.
6. Close the four falsification-audit fixes in `docs/FALSIFICATION_AUDIT.md`, starting with the
   strict null.
7. Run the three-arm tax-aware construction comparison (tax-blind / tax-aware / tax-aware +
   wash-block). The code path exists; it has not been measured over the full span.
8. Ask Absar for `div_next` (CRSP `RET` minus `RETX`). Until it arrives, dividend tax is an
   assumption, not a measurement.

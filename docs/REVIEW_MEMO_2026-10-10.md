# Research-readiness review memo (Phase 2 frozen)

**Date:** 2026-10-10. **Status:** review memo only. Committed as `7ce1308`; no experiment run; no paper text changed.
Commits under review: `b8e21ba` (Phase 1), `ac669f2` (Phase 2).

> **Update:** section 2's candidate causes were tested afterwards; see `COST_PARITY_DIAGNOSTIC_RESULTS_2026-10-10.md`.
> The exit convention, not drift-plus-convexity, is the largest contributor in the uncapped books, and borrow explains
> the small capped-book gaps. Read that document for the current account. Labels: **[V]** verified in this session from
files or full text; **[I]** interpretation; **[U]** unresolved or not checked.

## 1. Provenance verification

**What the manifest's Git fields mean [V].** `results/capacity_return_difference/MANIFEST.json` as committed
records `git_head_when_written = b8e21ba…` and `git_dirty_when_written = true`. The manifest is written by the
`tables` stage, which last ran when HEAD was Phase 1's commit and the Phase 2 files were still uncommitted. So it
says "produced from `b8e21ba` plus uncommitted changes", which is true, and it does **not** name `ac669f2`. It is
historical execution metadata and is left as is. It is not evidence that the tables came from a clean tree.

**Separate verification event [V], 2026-10-10.** A clean detached worktree of `ac669f2` (no local changes, no
`data/`, no `outputs/`) was created. The 10 files the `tables` stage generates (`tierA_*.csv` x3, `tierB_*.csv` x3,
`reconciliation_*.csv` x3, `tables.md`) were **deleted**, then regenerated with
`python tools/exp_capacity_return_difference.py --stage tables`. Exit 0; **all 10 are byte-identical** to the
tracked versions (SHA-256). The only change the run made was to the manifest's two Git fields (head -> `ac669f2`,
dirty -> false), which confirms the recorded values were historical. The worktree was removed afterwards.

**Correction to my earlier wording [V].** I previously said "13 artifacts reproduce byte for byte". Precisely: **10**
are regenerated from tracked snapshots. The other 3 (`tierB_monthly_*.csv.gz`) are inputs to that stage, not
outputs of it.

**Three tiers of reproducibility.**
1. *From tracked snapshots only* (clean checkout): the 10 table artifacts above. Verified.
2. *Needs the frozen `data/` and stage-02 predictions, which are not in git:* `inputs/monthly_*_cov.csv` (wedge
   tool, tag `cov`), the re-dumped weights, and `tierB_monthly_*.csv.gz` (`--stage pipeline`). Not re-run here.
   Their integrity is covered only by the manifest hashes. The re-dump matched the Tier A returns exactly [V,
   earlier], which is a consistency check, not an independent regeneration.
3. *Stage-02 model training:* out of scope and not reproducible from git.

## 2. Tier A - Tier B discrepancies: diagnosis from existing results

All figures: percentage points of NAV per year. "Residual" = pipeline cost - implied borrow - wedge cost, where
implied borrow = 1% x short gross from the dumped target weights (an exact deterministic quantity). Gross returns
are identical to 1e-16 in every rung checked, so the whole discrepancy is in costs [V].

| Rung | B Tier A | B Tier B | A-B | uncapped cost A / B | residual, uncapped (% of A cost) | residual, capped | borrow's share of A-B |
|---|---|---|---|---|---|---|---|
| Germany $100k | +0.64 | -0.52 | +1.16 | 18.07 / 16.66 | -2.41 (-13.3%) | -1.17 | -0.08 |
| Germany $300k | +2.63 | -0.01 | +2.63 | 23.47 / 21.04 | -3.43 (-14.6%) | -0.58 | -0.22 |
| Germany $100mn | +215.98 | +171.72 | +44.26 | 243.99 / 199.81 | -45.18 (-18.5%) | 0.00 | -0.92 |
| India $30mn | +111.00 | +103.99 | +7.01 | 129.48 / 122.62 | -7.86 (-6.1%) | -0.06 | -0.79 |
| Japan $1bn (control) | +101.25 | +101.65 | -0.40 | 112.92 / 113.38 | -0.54 (-0.5%) | -0.01 | -0.93 |
| Japan $10bn | +327.16 | +289.32 | +37.83 | 338.05 / 300.22 | -38.83 (-11.5%) | 0.00 | -0.99 |

**What the existing fields establish [V].**
* Borrow fee: it is present in the pipeline and absent from the wedge tool, and it is exactly computable. It moves
  B by at most about 1 point, so it **cannot** explain a 1.2, 2.6, 7.0, 37.8 or 44.3 point gap. It explains
  the *level* gap in capped books (about 1 point) and almost none of the *B* gap.
* The residual is **in the uncapped book** (capped residuals are near zero except Germany at small AUM) and has the
  same sign everywhere (the pipeline charges less).
* In Germany the residual is **-13% to -18.5% of cost at every AUM from $100k to $100mn**. At $100k the cost is
  dominated by the spread, with negligible impact [I, from the cost formula and magnitudes]. A mechanism that
  works only through convex impact therefore cannot produce a 13% shortfall at $100k. **This weakens my earlier
  suggestion that drifted holdings plus convexity is the main explanation.**
* The residual is largest where cost-input coverage is lowest (Germany 65%) and about zero where it is highest
  (Japan 99.8%), with India (99.1%) in between [V for the pattern; the coverage link is a hypothesis, H2]. Japan
  $10bn breaks that pattern (-11.5%), which is what a second, AUM-driven mechanism (drift in near-ruined accounts,
  H1) would produce.
* At Germany $100k and $300k the unexplained component (1.2 and 2.6 points of A-B) is **as large as B itself**.
  The Tier A positive small-mandate B is not robust; Tier B's is indistinguishable from zero [V].

**Candidate causes, none established [U].** H1: the pipeline rebalances from drifted, NAV-scaled holdings while the
wedge charges target-to-target (one cell: turnover 0.917 vs 0.963). H2: names that the wedge prices but the pipeline
drops or freezes (`priced_at`, `eligible_cost_input_permnos`, the 600-name cap, frozen sleeve). H3: differences in
exit handling. Not tested: component split of the pipeline cost, the wedge's split, per-name trade sets.

**What existing fields cannot answer.** The tracked Tier B file keeps total cost only. Questions needing new
component-level outputs: spread vs impact vs borrow per rung; the fraction of target |weight| the pipeline does not
trade; drifted vs target trade sizes; exit charges.

### Proposed minimal diagnostic (not run; for review)

* **Scope:** the six rungs above, both books, 8 cells, 2009-2019, same frozen contract, same weights. No model
  training, no new AUM rungs, no cost-model variants, no sensitivity sweep.
* **Outputs per cell-month:** (a) pipeline `cost_spread`, `cost_impact`, `cost_borrow`; (b) wedge cost split into
  spread+commission, impact and exit charges, evaluated on the same target-to-target trades; (c) sum of |target
  weight| for names present in the weights but absent from the pipeline's `priced_at` / eligible / 600-name set, and
  frozen-name exposure; (d) trade size |dw| as the pipeline sees it (drifted) and as the wedge sees it (target).
* **Parity counterfactuals (accounting only):** evaluate the wedge cost function on the pipeline's actual `dw`
  (isolates drift, H1); evaluate the pipeline cost on the wedge's target-to-target `dw` and the restricted name set
  (isolates H2).
* **Acceptance criterion (fixed in advance).** (i) Measured components reproduce each rung's total Tier A - Tier B
  cost gap to within the larger of 0.05 points per year and 5% of the gap. (ii) A mechanism is called an
  explanation only if switching that mechanism alone closes at least 90% of the gap in at least 10 of the 12
  rung-book pairs. (iii) Otherwise the report states the gap as unexplained, with the measured split, and Tier B stays
  primary. No adjustment of results is made on the basis of the diagnostic.

## 3. Referee-style contribution audit

### Evidence base [V from the repository]
Gross decile signals are significant (t +7.14 / +3.19 / +4.11 for Germany / India / Japan); the optimised book's
net Sharpe at $1bn is indistinguishable from zero (t +0.53 / +0.82 / +0.18); the capped decile book's net is
negative (matched-book t -2.40 / -1.81 / -2.74). The cap raises net return against the uncapped plan, but the plan
is near-ruined at most valid rungs (terminal wealth under 0.1 at 6 of 11 / 7 of 10 / 4 of 14); where it is not, B is
small and mostly not significant after Holm. Tax channel: exact `lt_share` contrast (0 vs 0.5928), two orders of
magnitude below cost. Design axes: 0 of 42 per market, minimum detectable effect 0.25-0.81 Sharpe points; one
exploratory Japan result (t +2.84).

### Literature [V where marked full text, else abstract-level]
* **Frazzini-Israel-Moskowitz, "Trading Costs of Asset Pricing Anomalies" (2012 draft) - full text read [V].** Live
  trade data from 19 developed markets; they report real costs "less than a tenth as large" as prior studies and
  global break-even sizes of tens to hundreds of billions for size, value and momentum, with reversal far lower. Their
  impact function uses the square root of the fraction of daily volume, as ours does. **Consequence:** a referee
  will ask whether our frozen impact calibration (k = 1) overstates costs by a large factor, which would make the
  uncapped plans' ruin and much of B a calibration artefact. We have no calibration to live execution data and the
  contract is frozen. This is the single most serious external objection. [I]
* **Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs" (Aug 2015 working paper) - full text read
  [V].** Capacity is defined for the last executing marginal trader; high-turnover strategies have capacity of about
  $0.18-0.53bn (Table, Panel C), and the buy/hold spread is the most effective mitigation. (Journal-version
  differences not checked [U].) Our "capacity" is a different object (effect of an ADV cap) and must not be sold as
  comparable.
* **Abstract-level only [U for details]:** Jensen-Kelly-Malamud-Pedersen (implementable efficient frontier; ML with
  trading-cost-aware portfolio learning, US; RFS, listed as forthcoming May 2026 on the SFI page; full text not
  accessible, SSRN returned 403); Azevedo-Hoegner-Velikov (320 anomalies, US; reports about a 57% average performance
  reduction from costs, decay and post-decimalisation, LSTM strategies remain profitable; the cost model is effective
  spreads, no participation/capacity analysis found); Avramov-Cheng-Metzker (MS 2023; ML returns shrink under
  realistic trading costs and restrictions); Cakici-Fieberg-Metko-Zaremba (JEDC 2023; 46 markets, 148 characteristics;
  gains from familiar factors); Tobek-Hronec (JFM 2021; international, liquid-universe survival; cost handling not
  confirmed); Hanauer-Kalsbach (EMR 2023; emerging markets; a practitioner summary mentions costs, the paper's cost
  analysis not checked); Chen-Velikov (JFQA 2023; effective-spread-based net returns near zero for the average
  anomaly, no price impact). Adjacent: an arXiv paper (Alpha-R1, Dec 2025) uses a square-root impact law with AUM
  tiers on CSI 300.
* **Not found in searches [U]:** an ML equity paper that combines ADV-participation capacity and AUM ladders with
  after-tax evaluation across Germany, India and Japan. Absence from a handful of web searches is not proof of
  novelty; a systematic search (SSRN, RePEc, Google Scholar, forward citations of the papers above) is needed
  before any priority claim.

### Assessment
**What is plausibly new [I].** (1) A matched-book, cost-capacity-tax accounting for the same ML-derived decile books
in three non-US markets, including a market where the long-term capital-gains statute is a natural contrast (India
vs two flat regimes). (2) A documented verification protocol and a set of measurement pitfalls (cost-input coverage
artefact, insolvent comparators, accounting-convention gaps between tools) that a referee can reuse. (3) A power
statement for design choices. **What is not new:** that ML signals lose most of their value to costs (Avramov et al.,
Azevedo et al., JKMP, Chen-Velikov) or that high-turnover strategies have small capacity (Novy-Marx-Velikov, FIM).

**Do the capacity results support an economic conclusion? [I]** Only a narrow one. The positive reading ("the cap
creates value at scale") is not supported: B is large only against comparators that lose almost all of their value,
and for plausible comparators it is small and mostly not significant. The supportable statement is the negative one:
at institutional scale, none of the three markets' books earns a net return distinguishable from zero under the frozen
cost model, and the participation cap changes which way the loss goes, not whether there is one.

**Power and post hoc choices.** The design-axis null excludes only effects of about a quarter Sharpe point or more;
the Japan conditioning result is one of nine, exploratory, single AUM, and the half-wealth subset was chosen after
looking. Neither may carry a confirmatory claim.

**Do the unresolved cost differences threaten the principal findings? [I]** They threaten the Tier A ladders and any
statement about small-mandate B or the shape of B(A) (Germany $100k and $300k change sign between tiers). They do not
directly threaten the net-Sharpe-near-zero finding, whose books and costs come from the pipeline accounting, but that
finding inherits the single bigger risk: the cost calibration itself (FIM). The tiers' disagreement is exactly the
kind of thing a referee finds in the replication package, so it must be explained or reported as unexplained in the
paper.

### Proposed central contribution
"Implementable net performance of ML-derived equity signals in Germany, India and Japan: a matched cost, capacity
and tax accounting with a verification protocol." A measurement and benchmarking paper whose main finding is a
well-powered-where-possible null at institutional scale, with the accounting identities and pitfalls as the
reusable contribution.

### Strongest defensible abstract-level claim
"Under a participation-capped, square-root-impact cost model applied identically to three markets, decile books built
from gross-significant ML signals earn net returns indistinguishable from zero at a $1bn mandate in Germany, India and
Japan; the cost channel exceeds the tax channel by two orders of magnitude; the long-term capital-gains statute
determines whether the tax channel is measurable; and we cannot detect effects of design choices smaller than about a
quarter of a Sharpe point." It must not claim that capacity "creates" performance, that costs are calibrated to
live trading, that the result is novel relative to unread full texts, or that acceptance is likely.

### Likely referee objections (ranked)
1. **Cost calibration** (FIM): k = 1 square-root impact vs live-trading evidence of far smaller costs; ruinous uncapped
   plans look like a modelling artefact. *Needs approved sensitivity analysis anchored to published live-trade
   estimates; currently frozen and not run.*
2. **The comparator**: B is measured against a near-ruined, infeasible plan; "solvent" is a weak criterion.
3. **Unreconciled Tier A / Tier B costs** and the changing sign at small mandates.
4. **Power and multiplicity**: nulls, exploratory subsets, strongly dependent rungs.
5. **Composite is not a fund**; cells are alternative designs, not an allocation.
6. **Sample and external validity**: 2009-2019 only, three markets, equal-weighted decile books (value-weighting not
   re-run on the compliant universe), flat borrow proxy, no short-sale constraints beyond that.
7. **Novelty** relative to JKMP / Azevedo et al. / Cakici et al. until full texts are read.

### Essential versus optional
*Essential for credibility:* (a) the component-level accounting diagnostic (section 2); (b) a cost-calibration
sensitivity anchored to live-trading evidence, which needs approval since sweeps are barred; (c) the value-weighting
rerun on the compliant universe; (d) full-text reading of JKMP, Azevedo-Hoegner-Velikov, Cakici et al. and a
systematic novelty search; (e) the 2020-2025 extension after its exposure audit and protocol amendment. *Optional:*
borrow-fee sweep, Japan/India scale extensions, tax-aware optimiser, cross-market transfer, the LLM workstream, and any
single-fund average-weight strategy (needs its own proposal).

### Ranked journal fit (fit, not acceptance probability) [I]
1. *Journal of Empirical Finance*: empirical, rigorous, three markets; high desk-rejection rate reported in the audit.
2. *Quantitative Finance*: portfolio construction, microstructure and implementation; the most natural home for a
   cost-and-capacity accounting paper with null headline results.
3. *Journal of International Financial Markets, Institutions and Money*: international fit, lower bar on novelty.
4. *Review of Asset Pricing Studies* (stretch): not advisable until items (a)-(e) are done. Journal scope and
   policies come from the official pages checked earlier and must be re-verified before submission [U].

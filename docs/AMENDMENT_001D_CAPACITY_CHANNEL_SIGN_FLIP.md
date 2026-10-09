# Amendment 001D: the capacity channel changes sign with scale, and Japan tests it

**Declared:** 2026-10-09, 11:30 IST
**Status:** declared **before any Japanese portfolio exists**. See section 6 for the evidence.
**Awaiting countersignature:** Maham (workstream C), as with 001A, 001B and 001C.
**Supersedes nothing.** PLAN_001 (`cae8140b7e2b7ee4`, N=64), 001A, 001B and 001C all stand.
**Relation to 001C:** 001C pre-registered that the participation constraint *governs* the portfolio
above a critical size (H-CAP). This amendment pre-registers the sharper and more falsifiable claim
that the constraint's effect on net risk-adjusted performance **changes sign** at a measurable
scale, and that the published disagreement in the literature is a disagreement about which side of
that scale the authors stand on.

---

## 1. Why this amendment exists

Reading the full text of the capacity literature (recorded in
`research/03_Research_Gaps/Closest_Prior_Art_Tracker.md`, sections C1-C8) produced two findings that
change what this paper can claim.

**First, a claim of ours was wrong and is withdrawn.** The assertion that our capacity frontiers are
"10x to 100x below published US estimates" compared our monthly-rebalanced ML books against
*low-turnover* US strategies. Novy-Marx & Velikov (RFS 2016, Table 7) report, in the US,
**$0.38-0.44bn** for a high-frequency combination strategy and **$0.18-0.53bn** for industry
relative reversal. Turnover-matched, Japan's $413mn is *inside* that range. Details in tracker
section C8.1.

**Second, the literature contains a live disagreement about a sign, and we can settle it.**

* **Novy-Marx & Velikov (RFS 2016):** the buy/hold spread is the most effective cost-mitigation
  technique; reducing turnover **improves** net performance.
* **Korajczyk & Sadka (JF 2004):** a deliberate liquidity weighting raises momentum's break-even
  fund size from roughly $1mn (equal-weighted, full sample) to **over $5bn** -- a factor of 5,000
  from the liquidity tilt alone.
* **Azevedo, Hoegner & Velikov (SSRN 4702406, 2025):** the same mitigations "significantly reduce
  turnover and trading costs" but **do not improve net performance**, because the lost gross return
  more than offsets the cost saving. Their stated reason is that post-decimalisation costs are only
  20-25 bps per month.

All three are US. All three are correct about their own setting. We hold that the disagreement is
not empirical but **positional**: it depends on where on the cost curve the investor sits, and that
is the one thing our design varies exogenously.

## 2. The hypothesis

> **H-FLIP.** The effect of a participation constraint on net risk-adjusted performance is a
> monotone increasing function of the ratio of impact cost to alpha. That ratio is governed by
> `kappa`, which grows as `sqrt(AUM / ADV)`. Consequently the constraint **destroys** net Sharpe at
> small mandate sizes, where it forfeits signal without averting meaningful cost, and **creates**
> net Sharpe at large mandate sizes, where the cost it averts exceeds the signal it forfeits. There
> exists a market-specific crossover AUM at which its effect is exactly zero.

The mechanism, which is the one-page comparative static that blocker 5 of the readiness audit asks
for:

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff`
roughly **linearly** in the forfeited positions, but lowers the cost term as **`G^0.5`**. Tightening
therefore helps if and only if `kappa` is large relative to alpha. Azevedo et al. operate at
`kappa` near zero -- their cost model is an effective spread that does not contain AUM at all -- so
for them a mitigation can only destroy alpha. Novy-Marx & Velikov and Korajczyk & Sadka price
impact at scale, so for them it creates value. Both findings follow from one expression.

## 3. The exploratory evidence (Germany and India)

Measured on the decile-spread portfolios built from the same stage-02 scores, across nine decades of
AUM. Full ladder: `outputs/signal_vs_portfolio/capacity_channel_ladder.csv` (34 rows), committed
verbatim at **`docs/attachments/CAPACITY_CHANNEL_LADDER_2026-10-09.csv`** because `outputs/` is
gitignored and a pre-registration whose exploratory evidence is not version-controlled is worth
little.

**Capacity channel** = (net Sharpe, participation-capped) - (net Sharpe, uncapped).

| AUM | Germany | India |
|---|---|---|
| $1k | | **-0.0039** |
| $3k | | +0.0150 |
| $100k | **-0.6895** | +0.1833 |
| $1mn | -0.5371 | +0.7090 |
| $3mn | **-0.1269** | +1.2769 |
| $4mn | **+0.0264** | |
| $10mn | +0.8129 | +2.1179 |
| $100mn | +4.9733 | +3.7073 |
| $1bn | +8.7707 | +4.4077 |
| $10bn | +10.0150 | +4.5521 |
| $1tn (asymptote) | +10.4002 | +4.6042 |

Three facts, all exploratory, all on the sample that generated them:

1. **The channel is monotone increasing in AUM** in both markets, over nine decades, without
   exception.
2. **It changes sign.** Germany's crossover is between **$3mn and $4mn**; India's between **$1k and
   $3k**. Below the crossover the cap destroys net Sharpe, which is Azevedo et al.'s finding
   reproduced inside our own framework. At $100k Germany's capped book loses 0.69 Sharpe points to
   the cap; at $1bn it gains 8.77.
3. **The crossover does not scale with the capacity frontier.** In units of AUM/frontier the
   crossovers are 3.6e-2 (Germany) and 3.3e-5 (India) -- three orders of magnitude apart, against a
   frontier ratio of only 1.9x. Whatever sets the crossover, it is not depth alone. The candidate
   explanation, to be tested not asserted, is that it depends on how much alpha sits in the
   illiquid tail: Germany's decile spread has gross Sharpe +2.38 against India's +1.00, so Germany
   forfeits more by capping.

A fourth fact is a candidate regularity rather than an established one:

4. **The asymptotic channel, scaled by the signal's own gross Sharpe, agrees across the two
   markets to within 5%:** Germany +10.4249/2.3828 = **4.375**; India +4.6079/1.0024 = **4.597**.
   With n = 2 this is weak, and it is pre-registered below as a secondary prediction only.

## 4. The predictions for Japan, fixed now

Japan's arm runs at `--max-names 600`, `--years 2009 2019` (amendment 001B), on the
prediction-loss cells. The ladder will be the same nine decades.

| # | prediction | falsified if | weight |
|---|---|---|---|
| **D1** | Japan's capacity channel is **monotone non-decreasing** in AUM across $1k to $1tn | any decrease exceeding 0.05 Sharpe points between adjacent rungs | **primary** |
| **D2** | Japan's capacity channel is **negative at the bottom of the ladder** and **positive at $1bn**, i.e. a crossover exists strictly inside the range | no sign change anywhere in $1k..$1tn, or the channel is negative at $1bn | **primary** |
| **D3** | Japan's crossover AUM **exceeds India's** (between $1k and $3k), because Japan's market is deeper on every cost input we have measured | Japan's crossover is below India's | **primary** |
| **D4** | Japan's **asymptotic** capacity channel divided by its own decile-spread gross Sharpe lies in **[3.5, 5.5]** | outside that band | secondary (n = 2) |
| **D5** | Japan's capacity channel at $1bn, **scaled by its gross Sharpe**, is below Germany's +3.681, because $1bn is only 2.4x past Japan's $413mn frontier against 9.4x past Germany's $106mn | at or above +3.681 | secondary |

**D2 and D3 are the real tests.** D1 is close to mechanical given the cost model and should be read
as a consistency check: if it fails, something is wrong with the pipeline rather than with H-FLIP.
D4 rests on two observations and a failure should be reported as a failure of the regularity, not of
H-FLIP. D5 depends on Japan's gross Sharpe, which is unknown.

## 5. What would falsify H-FLIP as a whole

* **D2 failing.** If Japan shows no sign change across nine decades of AUM, then the sign of the
  constraint's effect is not governed by scale and the reconciliation of the literature fails.
* **D1 and D3 both failing.** A non-monotone channel together with a crossover ordered against
  market depth would mean `kappa` is not the governing parameter.
* A **negative capacity channel at $1bn in Japan** would be the single most damaging result, because
  $1bn is past Japan's frontier and the mechanism says the constraint must be helping there.

## 6. That this precedes any Japanese result

Checked immediately before writing this document:

* `outputs/weights_index/` contains **no** Japanese entry (DEU and IND only).
* `outputs/signal_vs_portfolio/` contains **no** Japanese file; the capacity-channel ladder exists
  for Germany and India only.
* A search of `outputs/` for any Japanese backtest, portfolio or summary artefact
  (`*jpn*` crossed with `bt_*`, `pf_*`, `summary*`) returns **zero** files.
* **Japan has never been through stage 04.** Stage 02 is still training: 7 of its remaining
  strategies have reported, the rest have not.
* The Japanese quantities already inspected are **cost-input aggregates only** -- eligible-name
  counts, ADV medians, capacity ceilings and the $413mn frontier -- all computable before any model
  is fitted, all reported in `RESULTS_CAPACITY` section 4b, and all excluded from this confirmation.
* What would invalidate this amendment: editing any prediction in section 4 after Japan's arm
  reports. The predictions are fixed at this commit and the git history is the record.

## 7. How to report the outcome

* **If D1-D3 hold:** report H-FLIP as exploratory on Germany and India and **confirmed on Japan**,
  naming Japan as a pre-registered out-of-sample test and citing this document's commit date. The
  paper then claims the sign flip and its scale parameter, and explicitly reconciles Novy-Marx &
  Velikov with Azevedo, Hoegner & Velikov.
* **If they fail:** report the failure with the same prominence as the two failures already recorded
  in `RESULTS_WEDGE_TEST.md`, and report the sign flip as exploratory on two markets only.
* Either way, the **withdrawal in section 1 stands**: the "10-100x below US estimates" claim is
  gone regardless of what Japan shows.

## 8. What this does not claim

* Not "first to measure strategy capacity" -- Korajczyk & Sadka, Novy-Marx & Velikov, Garleanu &
  Pedersen.
* Not "first to show turnover reduction can help" -- Novy-Marx & Velikov own the positive sign;
  Korajczyk & Sadka own the liquidity tilt.
* Not "first to show ML alpha is fragile to frictions" -- Avramov, Cheng & Metzker, in Management
  Science.
* Not "first to apply ML outside the US" -- Cakici, Fieberg, Metko & Zaremba, 46 markets, JEDC 2023.
* What is claimed: **the sign is scale-dependent, the crossover is measurable, the published
  endpoints are recovered as limiting cases of one expression, and the crossover is not a fixed
  multiple of the capacity frontier.**

## 9. Countersignature

Maham to countersign, as with 001A, 001B and 001C. Her outstanding decision on the economic arm
(`docs/handoff/19_FOR_MAHAM_...` section 7) is independent and does not block this: every prediction
above concerns the prediction-loss cells.

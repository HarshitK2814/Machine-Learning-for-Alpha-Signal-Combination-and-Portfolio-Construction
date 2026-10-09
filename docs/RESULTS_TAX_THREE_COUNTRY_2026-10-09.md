# Taxes across three statutory regimes: second-order as a channel, first-order for survival, and ordered by turnover rather than by the rate

**Date:** 2026-10-09, 13:50 IST
**Status:** Japan's arm completed at 13:46 (21/21 strategies, **zero** frozen-sleeve failures), so
this is the first time all three jurisdictions have been priced on the same signals with the
lot-level engine.
**Audience:** referee-facing.

---

## 1. The result

Optimised book at $1bn, **prediction cells only** (the economic arm is not a competent
implementation and averaging it in is how the previously published ratios were formed), taxable
regime, HIFO lot selection, 2009-2019.

| | statutory short rate | **lt_share of gains** | monthly turnover | tax drag (bps p.a.) | cost drag (bps p.a.) | SR net | **SR after tax** | share of net SR kept |
|---|---|---|---|---|---|---|---|---|
| **Germany** | 26.375% | **0.0000** | 0.0135 | 6.38 | 17.21 | +0.128 | **+0.018** | **+14%** |
| **India** | 15.000% | **0.5928** | 0.0067 | 0.11 | 9.96 | +0.205 | **+0.201** | **+98%** |
| **Japan** | 20.315% | **0.0000** | 0.0290 | 11.49 | 42.31 | +0.057 | **−0.049** | **negative** |

Three findings, in increasing order of how much they change the paper.

## 2. The statutory wedge determines whether the holding-period channel can exist — confirmed on a second placebo

`lt_share_of_gains` is **identically 0.0000** in Germany *and* **identically 0.0000 in Japan**,
against **0.5928** in India.

This is the one pre-registered tax claim that survived (`RESULTS_WEDGE_TEST.md`), and **Japan is a
second, independent flat-rate placebo that reproduces Germany's exact zero.** Neither
Abgeltungsteuer (26.375%) nor Japan's listed-share rate (20.315%) creates a long-term category, so
no realised gain can fall into one, at any turnover, under any model. India's statute creates the
category and 59% of its realised gains land in it.

A tax-**level** story cannot produce that contrast: Germany is taxed 1.3x Japan's rate and 1.8x
India's, and all three differ, yet the two flat regimes give the same exact zero and only the
wedge-bearing regime is non-zero. **Statute determines whether the channel exists; it is not an
estimate and it does not depend on anything we chose.**

## 3. Given the wedge, the drag level is ordered by turnover, not by the statutory rate

| ordering | sequence |
|---|---|
| by statutory short rate | **DEU > JPN > IND** |
| by **tax drag** | **JPN > DEU > IND** |
| by **turnover** | **JPN > DEU > IND** |

**Tax drag follows turnover, not the rate.** Germany's statutory rate is 30% higher than Japan's,
yet Japan's tax drag is **80% higher** (11.49 vs 6.38 bps), because Japan's book turns over **2.1x**
as fast (0.0290 vs 0.0135 monthly).

Normalising confirms it is turnover doing the work and not something idiosyncratic: tax drag per
unit of turnover is **473** (Germany) and **396** (Japan) — the two flat regimes, close together, as
they should be for rates of 26.4% and 20.3% — against **17** for India, 25x lower, because India
shelters most of its gains in an exempt long-term category.

So the cross-country pattern decomposes cleanly: **the statute sets the *rate at which* turnover is
taxed, and turnover sets *how much* of it you pay.** That is a sharper statement than anything in
`RESULTS_WEDGE_TEST.md`, and it needed the third jurisdiction to be visible at all — with two
countries the rate and turnover orderings could not be separated.

## 4. Taxes are second-order as a channel and first-order for survival

This is the part that changes how the paper should talk about tax, and the three-country data makes
it unavoidable.

**As a channel magnitude, taxes lose decisively.** At $1bn the tax channel is −0.106 (Japan),
−0.111 (Germany), −0.004 (India) Sharpe points, against cost channels of −7.5 to −11.9 and capacity
channels of +3.6 to +8.9. Two orders of magnitude. The tax-aware-investing literature
(Sialm-Sosner, Israel-Moskowitz, Huang 2019) is addressing a second-order friction at institutional
scale in these markets.

**As a share of what survives, taxes are decisive in two of three jurisdictions.** Once cost and
capacity have done their work the residual is small enough that the tax channel consumes it:

* **India keeps 98%** of its net Sharpe (+0.205 to +0.201). Taxes genuinely do not matter there.
* **Germany keeps 14%** (+0.128 to +0.018).
* **Japan keeps nothing — the book goes negative** (+0.057 to **−0.049**). A strategy that is
  marginally viable before tax is **not viable after it**.

So "taxes are second-order" is true about the *channel* and false about the *investor*. Both
statements are in the data and the paper must carry both. The honest formulation:

> Tax is the smallest of the three frictions by one to two orders of magnitude, and in two of three
> jurisdictions it is nevertheless what decides whether the strategy is viable, because cost and
> capacity have already reduced the net Sharpe to a level the tax channel can erase.

**This also retires the magnitude argument for dropping the tax machinery.** The ledger is not
decoration: it is what shows the Japanese book is unviable, which no cost model alone would reveal.

## 4a. You cannot grow out of the tax channel: the bill falls 25x, the Sharpe drag does not

The `$1bn only` caveat below is now closed for Germany. Running stage 06 on the existing books at
$100mn, $1bn and $10bn (prediction cells, taxable regime):

| AUM | turnover | cost bps | **tax bps** | SR gross | SR net | SR after tax | **tax channel** | kept |
|---|---|---|---|---|---|---|---|---|
| **$100mn** | 0.0522 | 60.47 | **23.28** | +0.654 | +0.255 | +0.100 | **−0.155** | 39% |
| **$1bn** | 0.0135 | 17.21 | **6.38** | +0.423 | +0.128 | +0.018 | **−0.111** | 14% |
| **$10bn** | 0.0017 | 2.20 | **0.94** | +0.469 | +0.186 | +0.063 | **−0.122** | 34% |

**The tax bill collapses with scale and the risk-adjusted drag does not.** Tax drag falls **25-fold**
(23.28 to 0.94 bps) as the participation cap suppresses turnover **31-fold** (0.0522 to 0.0017) —
and yet the tax channel in Sharpe points is approximately **flat at −0.11 to −0.16** across two
orders of magnitude of mandate size.

The reason is the same mechanism as everywhere else in this paper: the cap suppresses the tax bill
by suppressing trading, but it suppresses gross return in the same motion, so the *ratio* is
preserved. **An investor cannot escape the tax channel by growing.** That is worth saying because
the bps figures alone would suggest the opposite — a large fund looks almost untaxed at 0.94 bps,
and is not, in the units that matter.

`lt_share_of_gains` is **0.0000 at all three mandate sizes**, as §2 requires: the statutory fact is
invariant to scale, because no amount of trading can create a long-term category that the law does
not provide.

The "kept share" column is non-monotone (39% / 14% / 34%) and should not be read as a scale effect:
it tracks the denominator, net Sharpe, which happens to be lowest at $1bn (+0.128) and recovers at
$10bn (+0.186). The scale-invariant quantity is the tax channel itself.

**Still open:** the same ladder for India and Japan. Japan matters most, because its $1bn book is
the one that goes negative after tax, and if its tax channel is likewise scale-invariant then no
mandate size rescues it.

## 4b. Inference on the tax channel — and the "survival" framing does not survive it

§4 claims taxes are "first-order for survival". **That claim is now withdrawn in the strong form**,
because it compared point estimates and the comparison does not hold up once the net Sharpe is
tested against zero. Tool: `tools/exp_after_tax_inference.py`, which runs the same
`after_tax_backtest` the pipeline uses and tests the paired net-versus-after-tax series.

**Germany, $1bn, composite of 8 prediction cells, 132 months:**

| quantity | value | t | p | |
|---|---|---|---|---|
| net Sharpe | +0.1523 | **+0.53** | **0.595** | **not distinguishable from zero** |
| after-tax Sharpe | +0.0160 | +0.06 | 0.954 | not distinguishable from zero |
| **tax channel** | **−0.1363** | **−4.67** | **< 0.0001** | **significant**, 95% CI [−0.196, −0.087] |

Per-cell: 3 of 8 significant after Holm.

**Two things follow, and they point in opposite directions.**

1. **The tax channel is real.** −0.136 Sharpe points with t = −4.67 and a CI well clear of zero.
   Taxes measurably reduce risk-adjusted performance, and that is worth reporting — it is the
   paired test doing work the point estimates could not.
2. **But the book was never demonstrably viable before tax either.** Germany's net-of-cost Sharpe
   is **+0.15 with t = +0.53**. You cannot say "tax turns a viable strategy unviable" when the
   strategy is not significantly profitable to begin with. **Nothing survives to be decided.**

**The honest formulation**, replacing §4's third bullet:

> Taxes are the smallest of the three frictions by one to two orders of magnitude, and the tax
> channel is nevertheless statistically significant where cost and capacity have already reduced
> net performance to a level indistinguishable from zero. The sequence is not "costs and capacity
> leave a viable strategy that tax then kills" — it is **"costs and capacity leave nothing
> statistically distinguishable from zero, and tax makes it measurably worse."**

That is a weaker claim than §4 made, and it is the one the data supports. It also means the
jurisdiction-level framing — "capital-gains statute decides whether ML alpha is viable" — is **not
available to us**, because viability is not established in any jurisdiction at $1bn before tax.

### 4b.1 All three countries, and the statutory placebo appears in the inference

| | net Sharpe | t | p | after-tax Sharpe | t | p | **tax channel** | **t** | **p** | Holm |
|---|---|---|---|---|---|---|---|---|---|---|
| **Germany** (flat 26.375%) | +0.152 | +0.53 | 0.595 | +0.016 | +0.06 | 0.954 | **−0.1363** | **−4.67** | **<0.0001** | **3/8** |
| **India** (wedge 0.150) | +0.271 | +0.82 | 0.413 | +0.265 | +0.80 | 0.422 | −0.0054 | −1.93 | 0.096 | **0/8** |
| **Japan** (flat 20.315%) | +0.055 | +0.18 | 0.861 | −0.082 | −0.27 | 0.789 | **−0.1373** | **−4.99** | **0.0010** | **3/8** |

**Two conclusions, and the second is the one worth having.**

**(i) No country's net Sharpe is distinguishable from zero** (t = +0.53, +0.82, +0.18), and neither
is any after-tax Sharpe, including Japan's negative −0.082 (t = −0.27). So the strategies are **not
demonstrably profitable net of costs in any of the three jurisdictions** at a $1bn mandate. The
"Japan goes negative after tax" framing of §4 is arithmetic on two numbers that are each
indistinguishable from zero, and it is withdrawn.

**(ii) The tax channel's *significance* tracks the statute, with both placebos behaving.** This is
the statutory claim appearing in the inference rather than only in the point estimates:

> Under the two **flat-rate** regimes, which provide no long-term category
> (`lt_share` = 0.0000 exactly), the tax channel is **significant**: Germany t = **−4.67**, Japan
> t = **−4.99**, each with **3 of 8** cells surviving Holm. Under **India's** regime, whose statute
> exempts long-term gains and shelters 59% of realised gains, the tax channel is **not significant**
> (t = −1.93, p = 0.096, **0 of 8** cells under Holm).

Two independent flat-rate jurisdictions with a significant tax channel; one wedge-bearing
jurisdiction without one. The magnitudes are near-identical in the two placebos (−0.1363 and
−0.1373, within 1%) and an order of magnitude smaller in the treatment (−0.0054). **That is the
cleanest inferential result in the project**, it is the pre-registered direction, and it does not
depend on any portfolio being profitable.

What it says: **the capital-gains statute determines whether taxes measurably erode a
machine-learning equity strategy's risk-adjusted performance** — not the rate (Germany's is 30%
above Japan's and the channels match to 1%), but whether the law provides a long-term category at
all.

What it does **not** say: that taxes decide viability. Viability is not established anywhere (point
i), so there is nothing for taxes to decide.

## 5. What this does not establish

* **Not a dose-response in the wedge.** The pre-registered claim that the friction penalty is
  *ordered by* the statutory wedge failed and remains withdrawn (`RESULTS_WEDGE_TEST.md` §2, §5).
  Section 3 here is an ordering by **turnover**, which is an endogenous portfolio outcome, not by
  the statutory instrument. It is descriptive, not identified.
* **Turnover is not exogenous.** Japan trades 2.1x Germany because of its universe and signal, not
  because of its tax code. Section 3's ordering therefore cannot be read as a tax experiment; the
  only thing with an exogenous statutory instrument is §2's existence claim.
* **n = 3.** The rate-versus-turnover separation in §3 rests on three jurisdictions, one of which
  (India) differs on both dimensions at once. The normalised figures (473 / 396 / 17) are what
  carry it, and they are three numbers.
* **$1bn only.** All of §1 is at a single mandate size. Tax drag should be re-run across the AUM
  ladder, which has not been done and is the obvious next step.

## 6. Reproduction

```
python pipelines/06_after_tax_eval.py --country JPN --max-names 600 --strategies <16 cells> \
    --lot-methods hifo
python tools/exp_friction_horse_race.py --country DEU IND JPN
```

Inputs: `outputs/summary_after_tax_{DEU,IND,JPN}_1e9.csv`. Japan's arm: 21/21 stage-04 strategies,
0 `failed_hold` months.

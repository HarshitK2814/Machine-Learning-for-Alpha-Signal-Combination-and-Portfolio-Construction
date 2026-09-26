# The practitioner gap: what a $100bn industry is arguing about, and what we can settle

**21 September 2026.** Status: instrument built and validated, first results in, **dispute not
resolved** — and the reason we cannot resolve it yet is stated in section 5 rather than buried.

---

## 1. The dispute

Tax-aware long/short (TALS) has grown past **$100bn**, led by AQR at roughly $70bn. It is publicly
contested, and the contest is about *measurement*, which is unusual and is what makes it tractable.

**The criticism.** Nate Koppikar of Orso Partners: the product's true alpha "is simply extreme tax
avoidance … the mechanical goal of the fund is to aggressively realize net capital losses on the
short side while perpetually deferring the realization of gains on the long side." He compares it to
the options-basket trade that ended in a multi-billion-dollar IRS settlement and calls the leverage
a "ticking time bomb."

**The defence.** AQR's position is that the objective is **pre-tax alpha** and the tax treatment is
a by-product; that TALS is not an extension of direct indexing but comes from the opposite
direction, active management; and that greater tracking error is expected to deliver higher pre-tax
alpha rather than lower.

**The market is already acting on it.** Fidelity and Schwab have withdrawn from offering these
accounts, citing operational and regulatory tail risk. Goldman and BNY Pershing have moved in.

## 2. Why this is a measurement question, not a rhetorical one

Deferring a gain does not remove the tax. It accumulates an embedded unrealised gain - a **deferred
tax liability** the investor owns but does not see on a realised-basis performance report.

### What the standard actually says (checked against the primary document, 21 Sep 2026)

An earlier version of this file claimed the USIPC After-Tax Performance Standards and the SEC
**require both** a pre-liquidation and a mark-to-liquidation figure. **That was wrong.** Reading the
standard itself corrects it, and the truth is sharper:

**A.1.a — pre-liquidation is MANDATED, not offered as one of two:**

> "Firms **must** utilize a realized basis 'pre-liquidation' calculation methodology, namely a
> methodology equivalent to the After-Tax Modified Dietz Method, the After-Tax Modified BAI
> (Linked Internal Rate of Return) Method or the After-Tax Daily Valuation Method."

**And the standard says in its own words that this method can understate the burden:**

> "By ignoring such future taxes, the 'pre-liquidation' method **may understate the total tax
> burden** on security returns during the measurement period."

Mark-to-liquidation is *discussed* - the standard notes it "would appear to be more conservative by
taking into account all capital gain taxes ... even on unrealized profits" but "may be distorted" -
and it is **not required**.

**A.4.e — what IS required is the raw ingredient, not the computed liability:**

> "Firms **must** report the percentage of unrealized capital gains as compared to total after-tax
> composite assets as of the end of each (annual period end)."

**A.2.a — and it does cover tax-aware separately managed accounts:**

> "All actual, fee-paying, discretionary portfolios that are **managed on a tax-aware basis** (i.e.,
> taking into account the client's tax profile when conducting security buy and sell decisions)
> **must** be included in at least one of the firm's after-tax composites."

### The gap, stated precisely

The disclosure regime requires the **numerator** - the percentage of unrealised capital gains - and
mandates a return methodology that its own text says may understate the tax burden. It does **not**
require:

1. the **tax** implied by those unrealised gains, or
2. the **loss carryforward** that offsets it.

Our work shows (2) is decisive. On our tax-aware arm the embedded gain was 1.71% of NAV and the
carryforward 3.80% - so the liability was fully cancelled. **An investor reading the mandated
disclosure sees a 1.71% unrealised gain and has no way to know whether it represents a real future
tax bill or one already covered by an accumulated loss balance.** Both readings are consistent with
the required disclosure, and they differ by the entire amount.

That is a narrower claim than "the industry hides the liability", and a much more defensible one:
**the mandated disclosure is not sufficient to distinguish a sheltered embedded gain from an
unsheltered one, and the difference is material.**

## 3. What we built

`alphacomb.tax.overhang`:

* `deferral_overhang` — pre-liquidation and mark-to-liquidation side by side, plus the gap.
* `overhang_trajectory` — whether the gap compounds as a strategy ages, which is the crux.
* `harvesting_decomposition` — gross alpha, cost drag, tax paid, realised short- and long-term
  gains, wash-disallowed losses, embedded gain, carryforward, deferral.

Plus carryforward **life and ring-fencing** wired into the ledger, because they turned out to decide
the answer.

## 4. What we found

**Revised 22 September 2026.** The first version of this section concluded that the overhang is
small and cancelled by an accumulated loss carryforward. **That conclusion was an artefact of
testing an unlevered, tax-blind book** - which is not the product under dispute. Once the tax-aware
optimiser was repaired and the leverage sweep run properly, the result reversed.

### 4.1 Tax-awareness, not leverage, is what creates the overhang

216 months, taxable US top bracket, embedded gain as a share of NAV, first checkpoint to last:

| Book | Embedded gain 3y → 18y | Sheltered by carryforward | Net deferred tax |
|---|---|---|---|
| gross 2, tax-blind | +2.7% → **+3.6%** | 0% | +0.85% |
| gross 4, tax-blind | +2.1% → **+3.4%** | 17% | +0.82% |
| gross 6, tax-blind | +1.5% → **+3.9%** | 25% | +0.93% |
| gross 2, **tax-aware** | +8.9% → **+22.4%** | 16% | **+3.41%** |
| gross 4, **tax-aware** | +13.7% → **+26.2%** | 4% | **+5.65%** |
| gross 6, **tax-aware** | +17.2% → **+39.4%** | 24% | **+5.87%** |

Every tax-aware book accumulates. Every tax-blind book does not. Leverage amplifies the size - 22%
of NAV at gross 2 against 39% at gross 6 - but it is the **objective**, not the leverage, that
switches the phenomenon on.

### 4.2 The carryforward does NOT cancel it

This is where the earlier conclusion was wrong. On the unlevered tax-blind book the carryforward
(3.8% of NAV) exceeded the embedded gain (1.7%) and the net liability was zero. On a tax-aware
book the carryforward covers only **4% to 25%** of a much larger embedded gain, and the net deferred
tax settles at **roughly 5.9% of NAV**.

The mechanism is not mysterious. A tax-aware optimiser holds winners and sells losers. Selling
losers generates carryforward, but holding winners grows the embedded gain faster, so the shelter
falls behind.

### 4.3 What this means for the dispute

On our book, moved toward the product's design, **the criticism has support**:

* the stock of unrealised gain accumulates rather than recycling - 17% to 39% of NAV over fifteen
  years at gross 6;
* the loss carryforward does not cover it;
* a realised-basis report - **the one the standard mandates** - understates what the investor owes
  by about **5.9% of NAV**.

Note the two measures point different ways and both are in the table. The overhang as a share of
*annualised* performance **falls** with horizon (25.2% at 3 years to 15.7% at 18) simply because one
stock of liability is spread over more years. The **stock itself** more than doubles. The criticism
is about the stock. Our own verdict function originally checked the ratio and therefore reported
"does not grow" - a reminder that the summary statistic has to match the claim being tested.

## 5. What we have NOT shown, and why it matters

**Our strategy is not the product under dispute.** Three differences, each of which cuts against
generalising:

1. ~~No leverage~~ **addressed**: the sweep runs gross 2, 4 and 6. Leverage amplifies the embedded
   gain but does not cause it.
2. ~~No deliberate deferral~~ **partly addressed**: the tax-aware arm holds winners and sells
   losers, which is the mechanism. It is still not tuned to maximise deferral the way a commercial
   product would be, so our magnitudes are probably a **lower bound**.
3. **Synthetic data.** Unchanged and still the binding limitation. The embedded-gain trajectory
   depends on the return process, and ours is one we wrote.
4. **Our optimiser was broken until 21 September.** Three attempts were needed. The numbers above
   come from the repaired version with zero solver failures across all six cells, but the history
   is in `STATUS.md` and a reader is entitled to weigh it.

So the honest claim is narrow:

> We have built and validated the instrument, and shown on synthetic data that a **tax-aware**
> book accumulates an embedded gain the loss carryforward does not cover, reaching 39% of NAV and
> leaving roughly 5.9% of NAV in unreported deferred tax - while an otherwise identical tax-blind
> book does not. **Whether the magnitudes hold on real data, and whether a real product's design
> sits closer to our tax-aware or tax-blind arm, are both open.**

Anyone claiming we have vindicated or refuted AQR from this is misreading it.

## 6. Two things that came out unplanned

**The ledger independently reproduced a published result.** Realised short-term gains are
**negative** (−64 bps/yr) while long-term gains are **positive** (+190 bps/yr) — the
short-term-losses / long-term-gains pattern Sialm & Sosner (2018) and Krasner & Sosner (2024)
document. We did not target it. It is a useful validation that the accounting is right.

**Wash sales are the largest single deadweight we measure.** 403 bps/yr of harvested losses
disallowed against 61 bps of tax actually paid — a 6.6x ratio. Our month-end granularity makes this
an upper bound, but the order of magnitude suggests s1091 compliance, not tax rates, may be the
binding constraint on harvesting-driven strategies. Practitioners manage it with correlated proxies;
nobody has published what it costs.

## 7. Why this strengthens the research

1. **It is a live dispute with money and regulators attached**, not a gap we inferred from a
   literature search.
2. **It is a measurement question**, which is what our lot-level ledger is for.
3. **It connects to the identification strategy.** Whether the carryforward shelter works depends on
   loss-relief architecture, which varies by country — the same variation that identifies the
   holding-period channel.
4. **It gives the paper a reader outside asset pricing**: the disclosure question (should SMAs
   report mark-to-liquidation?) is a policy question with a clear answer once the magnitudes are
   known.

## 8. Next

1. **Calibrate a strategy to the actual product**: levered, long-biased on the deferral side,
   harvesting-driven. Then re-run sections 4.1–4.3. This is the experiment that speaks to the
   dispute.
2. **Real data.** Still the binding constraint on everything.
3. ~~Verify the USIPC and SEC reporting requirements~~ **DONE 21 Sep 2026.** The primary
   document was read and it corrected our claim: pre-liquidation is mandated rather than one of
   two required figures, and what must be disclosed is the percentage of unrealised gains, not
   the tax on them or the carryforward offsetting them. Section 2 is rewritten. The remaining
   `[verify]` item is the SEC mutual-fund rule specifically, which this document describes only
   in passing.

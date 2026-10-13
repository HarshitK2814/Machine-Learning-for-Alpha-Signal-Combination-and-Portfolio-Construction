#!/usr/bin/env python
"""Inference on the capacity channel and on the crossover AUM.

The gap this closes
-------------------
`AMENDMENT_001D` pre-registers a claim about a **sign change**: the participation cap destroys net
Sharpe below a crossover mandate size and creates it above. Until this tool existed, both the
channel and the crossover were point estimates off a ladder with **no standard errors anywhere**,
which is exactly the criticism that killed the project's two earlier headlines. The crossover *is*
the claim, so it needs an interval.

What this measures
------------------
For each country and each AUM rung, from the monthly series dumped by
``exp_signal_vs_portfolio_wedge.py --dump-monthly``:

1. **Per-cell capacity channel** ``SR(net capped) - SR(net uncapped)``, with the paired
   Ledoit-Wolf studentized bootstrap test (``sharpe_difference_test``). Paired because the two
   series are the same months from the same scores; an unpaired test would be badly oversized.
2. **Holm-Bonferroni across the 8 prediction cells** at each rung, so "the channel is significant"
   survives testing 8 cells at once rather than being 8 separate claims. Holm rather than
   ``romano_wolf``: that function studentizes and bootstraps the **mean** of each series, so
   pointing it at the return differences would test whether the cap raises mean *return* - a
   different and in fact oppositely-signed question, since the cap cuts gross. Holm is applied to
   the p-values of the paired **Sharpe**-difference tests, which is the statistic the claim is
   about. The cost is some conservatism, which is the right side to err on here.
3. **Composite channel.** The equal-weighted average of the 8 cells' monthly returns, capped and
   uncapped, tested the same way. This is the number the paper should quote, because it is one
   portfolio rather than an average of 8 Sharpe ratios.
4. **The crossover AUM, with a confidence interval.** A stationary bootstrap over months: each
   replication recomputes the composite channel at every rung and solves for the zero by linear
   interpolation in log(AUM). The spread of those zeros is the interval. A replication in which the
   channel never changes sign is recorded rather than dropped, because "no crossover in range" is a
   possible answer and silently discarding those draws would bias the interval.

Usage
-----
    python tools/exp_capacity_channel_inference.py --country DEU IND
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.validation.inference import (  # noqa: E402
    _stationary_bootstrap_index,
    sharpe_difference_test,
)

PERIODS = 12


def holm(p: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni step-down adjusted p-values, familywise error rate controlled."""
    items = sorted(((k, v) for k, v in p.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out: dict[str, float] = {k: float("nan") for k in p}
    run = 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def _sr(x: np.ndarray) -> float:
    s = x.std(ddof=1)
    return float(x.mean() / s * np.sqrt(PERIODS)) if s > 0 else np.nan


def composite(df: pd.DataFrame) -> pd.DataFrame:
    """Equal-weighted average across cells, month by month, for one AUM rung."""
    piv = df.pivot_table(index="date", columns="cell",
                         values=["net_ret_capped", "net_ret_uncapped", "gross_ret"])
    out = pd.DataFrame({
        "capped": piv["net_ret_capped"].mean(axis=1),
        "uncapped": piv["net_ret_uncapped"].mean(axis=1),
        "gross": piv["gross_ret"].mean(axis=1),
    }).dropna()
    return out


def crossover_ci(by_aum: dict[float, pd.DataFrame], n_boot: int, block: int,
                 seed: int) -> dict:
    """Stationary-bootstrap interval for the AUM at which the composite channel crosses zero."""
    aums = np.array(sorted(by_aum))
    log_aum = np.log10(aums)
    # Align all rungs on the common set of months so one bootstrap index serves every rung.
    common = None
    for a in aums:
        idx = by_aum[a].index
        common = idx if common is None else common.intersection(idx)
    common = pd.DatetimeIndex(sorted(common))
    cap = np.column_stack([by_aum[a].loc[common, "capped"].to_numpy() for a in aums])
    unc = np.column_stack([by_aum[a].loc[common, "uncapped"].to_numpy() for a in aums])
    T = len(common)

    def zero_of(channel: np.ndarray) -> float:
        """First sign change, linearly interpolated in log10(AUM). NaN if none."""
        s = np.sign(channel)
        for i in range(len(channel) - 1):
            if np.isfinite(channel[i]) and np.isfinite(channel[i + 1]) and s[i] != s[i + 1] \
                    and s[i] != 0:
                lo, hi = channel[i], channel[i + 1]
                if hi == lo:
                    return float(log_aum[i])
                w = -lo / (hi - lo)
                return float(log_aum[i] + w * (log_aum[i + 1] - log_aum[i]))
        return float("nan")

    point_channel = np.array([_sr(cap[:, j]) - _sr(unc[:, j]) for j in range(len(aums))])
    point = zero_of(point_channel)

    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        ix = _stationary_bootstrap_index(T, block, rng)
        ch = np.array([_sr(cap[ix, j]) - _sr(unc[ix, j]) for j in range(len(aums))])
        draws[b] = zero_of(ch)
    fin = np.isfinite(draws)
    res = {
        "point_log10": point,
        "point_usd": float(10 ** point) if np.isfinite(point) else float("nan"),
        "n_boot": int(n_boot),
        "frac_no_crossover": float(1.0 - fin.mean()),
        "months": T,
        "ladder_low_usd": float(aums[0]),
        "ladder_high_usd": float(aums[-1]),
    }
    if fin.sum() >= 50:
        lo, hi = np.percentile(draws[fin], [2.5, 97.5])
        res["ci95_low_usd"] = float(10 ** lo)
        res["ci95_high_usd"] = float(10 ** hi)
        res["ci95_low_log10"] = float(lo)
        res["ci95_high_log10"] = float(hi)
    else:
        res["ci95_low_usd"] = res["ci95_high_usd"] = float("nan")
        res["ci95_low_log10"] = res["ci95_high_log10"] = float("nan")
    res["channel_by_rung"] = {float(a): float(c) for a, c in zip(aums, point_channel)}
    return res


def run_country(country: str, src: Path, out: Path, n_boot: int, block: int,
                seed: int, tag: str = "infer") -> tuple[pd.DataFrame, dict]:
    path = src / f"monthly_{country}_{tag}.csv"
    if not path.exists():
        raise SystemExit(f"no monthly series at {path}; run the wedge tool with --dump-monthly")
    mon = pd.read_csv(path, parse_dates=["date"])
    rows = []
    by_aum: dict[float, pd.DataFrame] = {}
    for aum, g in mon.groupby("aum"):
        comp = composite(g)
        by_aum[float(aum)] = comp
        # composite test
        rc = sharpe_difference_test(comp["capped"].to_numpy(), comp["uncapped"].to_numpy(),
                                    periods=PERIODS, n_boot=n_boot, block=block, seed=seed)
        rows.append({
            "country": country, "aum": float(aum), "scope": "composite", "cell": "ALL",
            "months": rc.detail["n_obs"],
            "sharpe_capped": rc.detail["sharpe_a"], "sharpe_uncapped": rc.detail["sharpe_b"],
            "capacity_channel": rc.statistic, "se_hac": rc.detail["se_hac"],
            "t_stat": rc.detail["studentized"], "p_value": rc.p_value,
            "ci95_low": rc.detail["ci95_low"], "ci95_high": rc.detail["ci95_high"],
            "p_holm": np.nan,
        })
        # per-cell tests, then Holm across cells at this rung
        per = []
        for cell, gc in g.groupby("cell"):
            gc = gc.sort_values("date")
            r = sharpe_difference_test(gc["net_ret_capped"].to_numpy(),
                                       gc["net_ret_uncapped"].to_numpy(),
                                       periods=PERIODS, n_boot=n_boot, block=block, seed=seed)
            per.append({
                "country": country, "aum": float(aum), "scope": "cell", "cell": cell,
                "months": r.detail["n_obs"],
                "sharpe_capped": r.detail["sharpe_a"], "sharpe_uncapped": r.detail["sharpe_b"],
                "capacity_channel": r.statistic, "se_hac": r.detail["se_hac"],
                "t_stat": r.detail["studentized"], "p_value": r.p_value,
                "ci95_low": r.detail["ci95_low"], "ci95_high": r.detail["ci95_high"],
            })
        adj = holm({d["cell"]: d["p_value"] for d in per})
        for d in per:
            d["p_holm"] = adj.get(d["cell"], np.nan)
        rows.extend(per)

    tab = pd.DataFrame(rows).sort_values(["country", "aum", "scope", "cell"])
    xo = crossover_ci(by_aum, n_boot=n_boot, block=block, seed=seed)
    out.mkdir(parents=True, exist_ok=True)
    suffix = "" if tag == "infer" else f"_{tag}"
    tab.to_csv(out / f"capacity_channel_inference_{country}{suffix}.csv", index=False)
    return tab, xo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND"])
    ap.add_argument("--src", type=Path, default=ROOT / "outputs" / "signal_vs_portfolio")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "capacity_inference")
    ap.add_argument("--tag", default="infer",
                    help="which monthly_<country>_<tag>.csv dump to read; 'vw' for the "
                         "value-weighted ladder, 'k05'/'k20'/'k30' for the impact-k sweep. "
                         "Mixing tags would mix cost assumptions into one table")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--block", type=int, default=6, help="expected bootstrap block, months")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    a = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run_items
    _sfx = "" if a.tag == "infer" else f"_{a.tag}"
    claim_run_items([(a.out / f"capacity_channel_inference_{c}{_sfx}.csv", {"country": c}) for c in a.country]
                    + [(a.out / f"crossover_intervals{_sfx}.csv", None)], a)

    summary = []
    for c in a.country:
        print(f"\n{'='*78}\n{c}\n{'='*78}")
        tab, xo = run_country(c, a.src, a.out, a.n_boot, a.block, a.seed, a.tag)
        comp = tab[tab.scope == "composite"].sort_values("aum")
        print(f"\n  composite capacity channel (equal-weighted across "
              f"{tab[tab.scope=='cell'].cell.nunique()} prediction cells)\n")
        print(f"  {'AUM':>10}  {'SR capped':>10}  {'SR uncap':>10}  {'channel':>9}  "
              f"{'se':>7}  {'t':>8}  {'p':>7}  {'95% CI':>19}")
        for _, r in comp.iterrows():
            star = "*" if r.p_value < 0.05 else " "
            print(f"  {r.aum:>10.0e}  {r.sharpe_capped:>+10.4f}  {r.sharpe_uncapped:>+10.4f}  "
                  f"{r.capacity_channel:>+9.4f}  {r.se_hac:>7.4f}  {r.t_stat:>+8.2f}  "
                  f"{r.p_value:>7.4f}{star} "
                  f"[{r.ci95_low:>+8.4f},{r.ci95_high:>+8.4f}]")
        nsig = int((comp.p_value < 0.05).sum())
        print(f"\n  significant at 5% on {nsig} of {len(comp)} rungs (composite)")
        cells = tab[tab.scope == "cell"]
        if cells.p_holm.notna().any():
            hsig = cells.groupby("aum").p_holm.apply(lambda s: int((s < 0.05).sum()))
            ncell = cells.cell.nunique()
            print(f"  Holm survivors per rung (of {ncell} cells): "
                  f"{dict((f'{k:.0e}', int(v)) for k, v in hsig.items())}")
        print(f"\n  CROSSOVER (composite channel changes sign)")
        if np.isfinite(xo["point_usd"]):
            print(f"    point estimate       ${xo['point_usd']:,.0f}")
        else:
            print(f"    point estimate       none inside "
                  f"${xo['ladder_low_usd']:.0e}..${xo['ladder_high_usd']:.0e}")
        if np.isfinite(xo["ci95_low_usd"]):
            print(f"    95% bootstrap CI     ${xo['ci95_low_usd']:,.0f} .. "
                  f"${xo['ci95_high_usd']:,.0f}")
        print(f"    draws with no sign change in range: {xo['frac_no_crossover']*100:.1f}%")
        print(f"    months {xo['months']}, {xo['n_boot']} replications, block {a.block}")
        summary.append({"country": c, **{k: v for k, v in xo.items()
                                         if k != "channel_by_rung"}})
    sfx = "" if a.tag == "infer" else f"_{a.tag}"
    pd.DataFrame(summary).to_csv(a.out / f"crossover_intervals{sfx}.csv", index=False)
    print(f"\nwrote {a.out / f'crossover_intervals{sfx}.csv'} and per-country inference tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

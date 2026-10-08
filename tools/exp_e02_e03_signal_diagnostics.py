#!/usr/bin/env python
"""Run E02 (signal quality and decay) and E03 (redundancy) on the real international panel.

These are Phase-3 descriptive diagnostics of the signal library. They form no strategy, select
no configuration, and are independent of the frozen hyperparameter grid, so they are not gated by
decision 6B - see the module docstring of ``alphacomb.validation.signal_diagnostics``.

    python tools/exp_e02_e03_signal_diagnostics.py                 # all resolvable countries
    python tools/exp_e02_e03_signal_diagnostics.py --countries DEU
    python tools/exp_e02_e03_signal_diagnostics.py --max-signals 40  # quick pass

Output lands in ``outputs/e02_e03/`` as per-country CSVs plus a cross-country summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import intl  # noqa: E402
from alphacomb.validation import signal_diagnostics as sd  # noqa: E402


def run_country(code: str, max_signals: int | None, out_dir: Path) -> dict:
    tables = intl.load_country(code, with_costs=False)
    uni, sig, tgt, meta = tables["universe"], tables["signals"], tables["targets"], tables["signal_meta"]

    keep = uni.loc[uni["in_universe"], ["date", "permno"]]
    panel = (keep.merge(sig, on=["date", "permno"], how="inner")
                 .merge(tgt, on=["date", "permno"], how="left"))

    signals = [c for c in sig.columns if c.startswith("sig_")]
    if max_signals:
        signals = signals[:max_signals]

    print(f"\n{'='*72}\n{code}: {len(panel):,} security-months, {len(signals)} signals\n{'='*72}")

    quality = sd.signal_quality(panel, signals)
    red = sd.redundancy(panel, signals, meta)
    cov = sd.coverage(panel, signals)

    out_dir.mkdir(parents=True, exist_ok=True)
    quality.to_csv(out_dir / f"e02_signal_quality_{code}.csv", index=False)
    red["per_theme"].to_csv(out_dir / f"e03_per_theme_{code}.csv")
    cov.to_csv(out_dir / f"e02_coverage_{code}.csv")

    sig_share = float(quality["significant_5pct"].mean()) if len(quality) else float("nan")
    print(f"  mean IC across signals        : {quality['mean_ic'].mean():+.5f}")
    print(f"  signals with |NW t| > 1.96    : {quality['significant_5pct'].sum()} of {len(quality)} "
          f"({sig_share:.1%})")
    print(f"  median ICIR                   : {quality['icir'].median():+.4f}")
    if "autocorr_1m" in quality:
        print(f"  median 1m signal autocorr     : {quality['autocorr_1m'].median():.4f}")
    hl = quality["ic_half_life_months"].dropna()
    if len(hl):
        print(f"  signals halving IC within 12m : {len(hl)} of {len(quality)} "
              f"(median half-life {hl.median():.0f}m)")
    print(f"  signals / effective signals   : {red['n_signals']} / {red['effective_n_signals']:.1f}")
    print(f"  mean |corr| within theme      : {red['mean_abs_within_theme_corr']:.4f}")
    print(f"  mean |corr| across themes     : {red['mean_abs_cross_theme_corr']:.4f}")

    print(f"\n  top 8 signals by mean rank IC:")
    for _, r in quality.head(8).iterrows():
        star = "*" if r["significant_5pct"] else " "
        print(f"    {r['signal']:<28} IC {r['mean_ic']:+.5f}  ICIR {r['icir']:+6.3f}  "
              f"t {r['nw_t']:+6.2f} {star}")

    return {
        "country": code,
        "security_months": int(len(panel)),
        "n_signals": int(red["n_signals"]),
        "effective_n_signals": float(red["effective_n_signals"]),
        "mean_ic": float(quality["mean_ic"].mean()),
        "median_icir": float(quality["icir"].median()),
        "share_significant": sig_share,
        "mean_abs_within_theme_corr": float(red["mean_abs_within_theme_corr"]),
        "mean_abs_cross_theme_corr": float(red["mean_abs_cross_theme_corr"]),
        "n_themes": int(red["n_themes"]),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--countries", nargs="*", default=None)
    ap.add_argument("--max-signals", type=int, default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "e02_e03")
    args = ap.parse_args(argv)

    countries = args.countries or intl.available_countries()
    if not countries:
        print("no country resolves under data/intl_c*")
        return 2

    summaries = [run_country(c, args.max_signals, args.out) for c in countries]
    summary = pd.DataFrame(summaries)
    args.out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out / "e02_e03_summary.csv", index=False)

    print(f"\n{'='*72}\nCROSS-COUNTRY SUMMARY (E02/E03, real data)\n{'='*72}")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
    print(f"\nwrote {args.out}")
    print("\nThese are descriptive properties of the signal panel. No strategy was formed and no\n"
          "configuration selected, so decision 6B's results gate does not apply.")
    (args.out / "provenance.json").write_text(json.dumps({
        "experiments": ["E02", "E03"],
        "data_source": "real",
        "countries": countries,
        "forms_a_strategy": False,
        "selects_a_configuration": False,
        "gated_by_decision_6B": False,
    }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Stage 04 (workstream B): turn predictions (C9) or proposals (C10) into portfolio weights (C11).

Prediction cells and baselines go through the cost-aware optimiser; economic-objective cells are
projected onto the same constraint set. Every strategy therefore faces identical limits and costs.

    python pipelines/04_construct_portfolios.py --strategies all
    python pipelines/04_construct_portfolios.py --strategies cell_L-S-P-0 --cost-multiplier 2.0
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, new_run_id, paths, read_table, write_table  # noqa: E402
from alphacomb.portfolio import OptimizerConfig, TaxState, construct, project  # noqa: E402
from alphacomb.tax import TaxConfig, TaxLotLedger, get_regime  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402

log = logging.getLogger("stage04")


def discover(kind: str) -> dict[str, Path]:
    root = paths.outputs_root() / kind
    out: dict[str, Path] = {}
    if not root.exists():
        return out
    for folder in sorted(root.iterdir()):
        latest = paths.latest_run(kind, folder.name)
        if latest is not None:
            out[folder.name] = latest
    return out


def build_weights(strategy: str, artefact: Path, kind: str, bundle, risk: RiskCache, cfg: OptimizerConfig,
                  run_id: str, ledger: TaxLotLedger | None = None) -> tuple[Path, dict]:
    """Construct weights month by month.

    When ``ledger`` is supplied the optimiser is told, before each trade, what that trade would cost
    in tax. The ledger is the same object the after-tax backtest uses, so the optimiser cannot be
    optimising against a tax model the accountant would not recognise. It is advanced with the
    weights actually chosen, which keeps the embedded gains and the s1091 window honest.
    """
    table = read_table(artefact)
    weights_rows, statuses = [], []
    prev: pd.Series | None = None
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    nav = cfg.aum_usd
    for date, group in table.groupby("date"):
        rm = risk.model(date)
        if kind == "predictions":
            alpha = pd.Series(group["alpha"].to_numpy(), index=group["permno"].to_numpy()).dropna()
            tax_state = None
            if ledger is not None:
                ledger.expire_wash_window(date)
                tax_state = TaxState.from_ledger(ledger, alpha.index, date, wash_block=cfg.wash_block)
            res = construct(date, alpha, prev, rm, bundle.cost_inputs, cfg, tax_state)
        else:
            proposal = pd.Series(group["w_prop"].to_numpy(), index=group["permno"].to_numpy()).dropna()
            res = project(date, proposal, rm, bundle.cost_inputs, cfg)
        statuses.append(res.status)
        w = res.weights
        weights_rows.append(pd.DataFrame({"date": pd.Timestamp(date), "permno": w.index.astype("int32"),
                                          "w": w.to_numpy()}))
        # drift last month's weights with realised returns so next month's trade is measured honestly
        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], w.index])).fillna(0.0).to_numpy()
        drifted = w.to_numpy() * (1.0 + r)
        port_ret = float((w.to_numpy() * r).sum())
        prev = pd.Series(drifted / (1.0 + port_ret), index=w.index)
        if ledger is not None:
            held = pd.Index(sorted(set(ledger.lots) | set(int(x) for x in w.index)))
            targets = pd.Series(0.0, index=held)
            targets.loc[[int(x) for x in w.index]] = w.to_numpy() * nav
            for permno in held:
                ledger.trade_to(int(permno), date, float(targets[permno]))
            ledger.accrue_returns(pd.Series(r, index=[int(x) for x in w.index]))
            nav *= (1.0 + port_ret)
    frame = pd.concat(weights_rows, ignore_index=True)
    out = paths.weights_path(strategy, run_id)
    write_table(frame, out, "weights")
    counts = pd.Series(statuses).value_counts().to_dict()
    log.info("%s: %d months, statuses %s", strategy, len(weights_rows), counts)
    return out, counts


def main() -> None:
    p = argparse.ArgumentParser(description="Construct portfolios from model outputs (contract C11).")
    p.add_argument("--strategies", nargs="+", default=["all"])
    p.add_argument("--data", default=None)
    p.add_argument("--gamma", type=float, default=None, help="risk aversion (default: configs/portfolio.yaml)")
    p.add_argument("--cost-multiplier", type=float, default=1.0, help="cost sensitivity (E31)")
    p.add_argument("--aum", type=float, default=None, help="AUM in 2020 dollars (E30/E32)")
    p.add_argument("--long-only", action="store_true")
    p.add_argument("--tax-aware", action="store_true",
                   help="put the tax consequence of each trade in the optimiser objective")
    p.add_argument("--tax-regime", default="taxable_us_top_bracket")
    p.add_argument("--wash-block", action="store_true",
                   help="also forbid repurchasing a name inside the s1091 window")
    p.add_argument("--harvest-haircut", type=float, default=1.0,
                   help="how usable a realised loss is (1.0 = fully offsets other gains)")
    p.add_argument("--suffix", default="", help="append to the strategy name, e.g. '_taxaware'")
    p.add_argument("--max-held-share", type=float, default=0.02,
                   help="fail the run if more than this share of months fall back to held weights "
                        "(see docs/SILENT_OPTIMISER_FAILURE.md)")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    bundle = load_bundle(a.data or cfg["data_source"])
    risk = RiskCache(StructuralRiskModel(bundle, cfg))

    opt = OptimizerConfig.from_files(cfg)
    updates = {"cost_multiplier": a.cost_multiplier, "long_only": a.long_only,
               "tax_aware": a.tax_aware, "wash_block": a.wash_block,
               "tax_harvest_haircut": a.harvest_haircut}
    if a.gamma is not None:
        updates["gamma"] = a.gamma
    if a.aum is not None:
        updates["aum_usd"] = a.aum
    opt = OptimizerConfig(**{**opt.__dict__, **updates})

    available = {("predictions", k): v for k, v in discover("predictions").items()}
    available.update({("weight_proposals", k): v for k, v in discover("weight_proposals").items()})
    if not available:
        raise SystemExit("no model outputs found; run pipelines/02_train_models.py first")
    wanted = None if a.strategies == ["all"] else set(a.strategies)

    rows, failures = [], []
    for (kind, strategy), artefact in sorted(available.items(), key=lambda kv: kv[0][1]):
        if wanted and strategy not in wanted:
            continue
        started = time.time()
        name = f"{strategy}{a.suffix}"
        run_id = new_run_id(f"pf_{name}")
        ledger = (TaxLotLedger(get_regime(a.tax_regime)) if a.tax_aware and kind == "predictions"
                  else None)
        out, counts = build_weights(name, artefact, kind, bundle, risk, opt, run_id, ledger)
        months = sum(counts.values())
        held = counts.get("failed_hold", 0)
        held_share = held / months if months else 0.0
        rows.append({"strategy": name, "source_artefact": str(artefact), "weights": str(out),
                     "run_id": run_id, "cost_multiplier": a.cost_multiplier, "aum": opt.aum_usd,
                     "gamma": opt.gamma, "tax_aware": a.tax_aware, "wash_block": a.wash_block,
                     "months": months, "n_optimal": counts.get("optimal", 0),
                     "n_inaccurate": counts.get("optimal_inaccurate", 0), "n_held": held,
                     "held_share": round(held_share, 4),
                     "minutes": round((time.time() - started) / 60, 2)})
        if held_share > a.max_held_share:
            # A held month is last month's book, not this month's model. A run with many of them
            # describes a stale portfolio while still producing a well-formed return series, and
            # the failure is correlated with which names a cell trades - so it is not comparable
            # to a clean cell. Fail loudly rather than let it reach a results table.
            failures.append((name, held, months, held_share))
            log.error("%s: %d of %d months (%.1f%%) are HELD weights, above the --max-held-share "
                      "threshold of %.1f%%. This strategy is not comparable to a clean one.",
                      name, held, months, 100 * held_share, 100 * a.max_held_share)
    manifest = pd.DataFrame(rows)
    path = paths.outputs_root() / "manifest_portfolios.csv"
    manifest.to_csv(path, mode="a", header=not path.exists(), index=False)
    print(manifest.to_string(index=False))
    print(f"\nmanifest: {path}")


if __name__ == "__main__":
    main()

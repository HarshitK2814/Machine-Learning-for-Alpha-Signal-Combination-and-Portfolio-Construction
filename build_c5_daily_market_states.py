"""Construct daily-data C5 MKTVOL and ILLIQ working candidates.

The output follows the existing C5 convention: raw state at month t is shifted
one month before expanding-only standardisation.  Pre-activation values are
neutral zero and explicitly flagged; post-activation gaps fail the build.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
MARKET_DAILY = ROOT / "data" / "intl_c6" / "staging" / "C5_WRDS_MARKET_DAILY.csv.gz"
SECURITY_PANEL = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
EXTERNAL = ROOT / "data" / "intl_c5" / "candidate_external_c5_working" / "C5_EXTERNAL_WORKING_CANDIDATE.csv"
OUT_DIR = ROOT / "data" / "intl_c5" / "candidate_daily_market_working"
OUT = OUT_DIR / "C5_DAILY_MARKET_WORKING_CANDIDATE.csv"
COMBINED = OUT_DIR / "C5_FULL_WORKING_CANDIDATE.csv"
AUDIT = OUT_DIR / "C5_DAILY_MARKET_WORKING_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def expanding_z_after_lag(raw: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    lagged = raw.shift(1)
    mu = lagged.expanding(min_periods=24).mean()
    sd = lagged.expanding(min_periods=24).std(ddof=1)
    z = ((lagged - mu) / sd).replace([np.inf, -np.inf], np.nan)
    active = mu.notna() & sd.gt(0) & lagged.notna()
    first_active = active.idxmax() if active.any() else None
    if first_active is not None and z.loc[first_active:].isna().any():
        missing_dates = z.loc[first_active:][z.loc[first_active:].isna()].index.astype(str).tolist()[:20]
        raise RuntimeError(f"Post-activation C5 state gaps: {missing_dates}")
    return z.fillna(0.0).clip(-5.0, 5.0), active, lagged


def main() -> None:
    market = pd.read_csv(MARKET_DAILY, parse_dates=["datadate"])
    panel = pd.read_csv(
        SECURITY_PANEL,
        usecols=[
            "country", "date", "permno", "prccd", "cshoc", "qunit",
            "usd_per_local", "return_obs_21", "volume_obs_21", "amihud_usd_21",
        ],
        parse_dates=["date"],
        low_memory=False,
    )
    countries = sorted(panel["country"].dropna().unique())
    dates = pd.date_range("1990-01-31", "2020-12-31", freq="ME")

    monthly_market_parts = []
    for country, g in market.groupby("country", sort=True):
        g = g.sort_values("datadate", kind="stable").copy()
        g["market_return_obs_21"] = g["market_vw_return_usd"].rolling(21, min_periods=1).count()
        g["market_sigma_21"] = g["market_vw_return_usd"].rolling(21, min_periods=21).std(ddof=1)
        g["date"] = g["datadate"] + pd.offsets.MonthEnd(0)
        endpoint = g.drop_duplicates("date", keep="last")
        endpoint["MKTVOL_raw"] = np.log(endpoint["market_sigma_21"].where(endpoint["market_sigma_21"] > 0))
        monthly_market_parts.append(endpoint[["country", "date", "datadate", "market_return_obs_21", "market_sigma_21", "MKTVOL_raw", "constituents", "expected_constituents", "constituent_participation"]])
    monthly_market = pd.concat(monthly_market_parts, ignore_index=True)

    panel["endpoint_market_cap_usd"] = (
        pd.to_numeric(panel["prccd"], errors="coerce")
        * pd.to_numeric(panel["cshoc"], errors="coerce")
        / pd.to_numeric(panel["qunit"], errors="coerce").where(lambda x: x > 0)
        * pd.to_numeric(panel["usd_per_local"], errors="coerce")
    )
    panel["amihud_15of21"] = panel["amihud_usd_21"].where(
        panel["return_obs_21"].ge(15) & panel["volume_obs_21"].ge(15)
    )
    panel["eligible_weight"] = panel["endpoint_market_cap_usd"].where(panel["endpoint_market_cap_usd"] > 0)
    panel["valid_illiq_weight"] = panel["eligible_weight"].where(panel["amihud_15of21"].notna())
    panel["weighted_illiq"] = panel["amihud_15of21"] * panel["valid_illiq_weight"]
    illiq = (
        panel.groupby(["country", "date"], sort=True)
        .agg(
            total_market_cap_usd=("eligible_weight", "sum"),
            valid_illiq_market_cap_usd=("valid_illiq_weight", "sum"),
            weighted_illiq_sum=("weighted_illiq", "sum"),
            investible_securities=("permno", "nunique"),
            illiq_securities=("amihud_15of21", "count"),
        )
        .reset_index()
    )
    illiq["illiq_weight_coverage"] = illiq["valid_illiq_market_cap_usd"] / illiq["total_market_cap_usd"]
    illiq["ILLIQ_vw_raw"] = illiq["weighted_illiq_sum"] / illiq["valid_illiq_market_cap_usd"]
    illiq.loc[illiq["illiq_weight_coverage"] < 0.50, "ILLIQ_vw_raw"] = np.nan
    illiq["ILLIQ_raw"] = np.nan
    for country, index in illiq.groupby("country", sort=True).groups.items():
        x = illiq.loc[index, "ILLIQ_vw_raw"]
        # Twelve-month trailing window, requiring at least nine observed
        # months.  Missing source months are ignored, never interpolated; this
        # prevents one explicit coverage failure from erasing the next eleven
        # otherwise observable detrended states.
        trailing = x.rolling(12, min_periods=9).mean()
        illiq.loc[index, "ILLIQ_raw"] = np.log(x.where(x > 0)) - np.log(trailing.where(trailing > 0))

    base = pd.MultiIndex.from_product([countries, dates], names=["country", "date"]).to_frame(index=False)
    raw = base.merge(monthly_market, on=["country", "date"], how="left", validate="one_to_one")
    raw = raw.merge(illiq, on=["country", "date"], how="left", validate="one_to_one")
    outputs = []
    for country, g in raw.groupby("country", sort=True):
        g = g.sort_values("date", kind="stable").copy().set_index("date")
        g["MKTVOL"], g["MKTVOL_active"], g["MKTVOL_lagged_raw"] = expanding_z_after_lag(g["MKTVOL_raw"])
        g["ILLIQ"], g["ILLIQ_active"], g["ILLIQ_lagged_raw"] = expanding_z_after_lag(g["ILLIQ_raw"])
        outputs.append(g.reset_index())
    out = pd.concat(outputs, ignore_index=True).sort_values(["country", "date"], kind="stable")

    cols = [
        "country", "date", "MKTVOL", "MKTVOL_active", "MKTVOL_lagged_raw",
        "ILLIQ", "ILLIQ_active", "ILLIQ_lagged_raw", "market_return_obs_21",
        "market_sigma_21", "datadate", "constituents", "expected_constituents",
        "constituent_participation", "ILLIQ_vw_raw", "illiq_weight_coverage",
        "investible_securities", "illiq_securities",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out[cols].to_csv(OUT, index=False)

    external = pd.read_csv(EXTERNAL, parse_dates=["date"])
    combined = external.merge(
        out[["country", "date", "MKTVOL", "MKTVOL_active", "ILLIQ", "ILLIQ_active"]],
        on=["country", "date"], how="left", validate="one_to_one"
    )
    if len(combined) != 1_116 or combined[["MKTVOL", "ILLIQ"]].isna().any().any():
        raise RuntimeError("Combined C5 working candidate contract failed")
    combined.to_csv(COMBINED, index=False)

    by_country = []
    for country, g in out.groupby("country", sort=True):
        by_country.append({
            "country": country,
            "rows": int(len(g)),
            "mktvol_raw_nonnull": int(g["MKTVOL_raw"].notna().sum()),
            "mktvol_active": int(g["MKTVOL_active"].sum()),
            "mktvol_first_active": str(g.loc[g["MKTVOL_active"], "date"].min().date()) if g["MKTVOL_active"].any() else None,
            "illiq_vw_raw_nonnull": int(g["ILLIQ_vw_raw"].notna().sum()),
            "illiq_detrended_raw_nonnull": int(g["ILLIQ_raw"].notna().sum()),
            "illiq_active": int(g["ILLIQ_active"].sum()),
            "illiq_first_active": str(g.loc[g["ILLIQ_active"], "date"].min().date()) if g["ILLIQ_active"].any() else None,
            "illiq_weight_coverage_min_after_active": float(g.loc[g["ILLIQ_active"], "illiq_weight_coverage"].min()) if g["ILLIQ_active"].any() else None,
        })
    audit = {
        "verdict": "PASS_DAILY_C5_MKTVOL_ILLIQ_WORKING_CANDIDATE",
        "scope": "working candidate only; not production",
        "rows": int(len(out)),
        "countries": countries,
        "MKTVOL_definition": "log sample standard deviation of last 21 certified country VW USD total returns; daily constituents frozen at prior month-end; then one-month lag and expanding z-score",
        "ILLIQ_definition": "USD-market-cap-weighted mean of 21-trading-day security Amihud with >=15 observed return/volume days; require >=50% mcap coverage; log deviation from trailing 12-month window mean with >=9 observed months and no interpolation; then one-month lag and expanding z-score",
        "standardisation": "expanding mean/std, minimum 24 lagged raw observations, clip [-5,5], neutral zero only before activation",
        "no_lookahead": "daily membership frozen at prior month-end; monthly raw states shifted one month before standardisation",
        "by_country": by_country,
        "inputs": {
            "market_daily": {"path": str(MARKET_DAILY.relative_to(ROOT)), "sha256": sha256(MARKET_DAILY)},
            "security_panel": {"path": str(SECURITY_PANEL.relative_to(ROOT)), "sha256": sha256(SECURITY_PANEL)},
            "external_c5": {"path": str(EXTERNAL.relative_to(ROOT)), "sha256": sha256(EXTERNAL)},
        },
        "outputs": {
            "daily_states": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
            "combined_working_candidate": {"path": str(COMBINED.relative_to(ROOT)), "sha256": sha256(COMBINED)},
        },
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

"""Audit the nullable working C6 candidate against the frozen C6 consumer.

Read-only with respect to Workstream B: this script documents incompatibilities
but deliberately does not change the shared schema or consumer behaviour.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts.schemas import SchemaError, validate
from alphacomb.portfolio.cost_terms import cost_inputs_for


CANDIDATE = ROOT / "data" / "intl_c6" / "candidate_working" / "C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
OUT = ROOT / "data" / "intl_c6" / "audit" / "C6_CONSUMER_COMPATIBILITY_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    candidate = pd.read_csv(CANDIDATE, parse_dates=["date"], low_memory=False)
    contract_error = None
    try:
        validate(candidate, "cost_inputs")
    except SchemaError as exc:
        contract_error = str(exc)

    sample_date = candidate["date"].min()
    sample = candidate.loc[candidate["date"].eq(sample_date)].copy()
    aligned = cost_inputs_for(sample_date, sample, pd.Index(sample["permno"].head(10)))
    observed_fill = sorted(aligned["borrow_fee"].dropna().unique().tolist())
    source = inspect.getsource(cost_inputs_for)
    uses_fixed_borrow_fill = 'fillna(0.0025)' in source

    hard_integration_failure = bool(candidate["borrow_fee"].isna().all() and uses_fixed_borrow_fill)
    audit = {
        "verdict": "FAIL_HARD_BORROW_FEE_INTEGRATION" if hard_integration_failure else "BLOCKED_C6_CONTRACT_AND_CONSUMER_POLICY_MISMATCH",
        "scope": "read-only audit; Workstream B not modified",
        "candidate_rows": int(len(candidate)),
        "candidate_borrow_fee_nonnull": int(candidate["borrow_fee"].notna().sum()),
        "candidate_null_counts": {
            column: int(candidate[column].isna().sum())
            for column in ["spread", "sigma_d", "adv_usd", "borrow_fee"]
        },
        "frozen_C6_schema_requires_nonnull_borrow_fee": True,
        "candidate_passes_frozen_C6_schema": contract_error is None,
        "schema_error_first_failure": contract_error,
        "schema_interpretation": "the validator reports spread first; all four frozen C6 market-input columns are non-nullable, so borrow_fee would remain blocking after spread completion",
        "consumer_uses_fixed_borrow_fee_fill": uses_fixed_borrow_fill,
        "consumer_observed_sample_fill": observed_fill,
        "hard_integration_failure": hard_integration_failure,
        "policy_conflict": "current consumer converts unavailable borrow fees to 0.0025; certified data policy requires null and forbids an unapproved proxy",
        "required_resolution": "obtain genuine lending-fee data or approve and preregister an explicit research-design fallback before C6 promotion or Workstream B consumption",
        "input": {"path": str(CANDIDATE.relative_to(ROOT)), "sha256": sha256(CANDIDATE)},
        "production_written": False,
        "workstream_b_modified": False,
        "github_written": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

# Phase C: recovered configuration of the original multi-regime after-tax runs

**Date:** 2026-10-14. Configuration and provenance only. From the after-tax summaries only the columns `strategy, country, regime, lot_method, months, dated, wedge` were read; weight files were hashed as bytes and not opened; no Sharpe, drag, NAV, return, price, dividend, cost or tax value was read. Internal researcher-led work; no external sign-off.

This document is separate from `PHASE_C_CONFIGURATION_RECOVERY_2026-10-14.md`, which recovers the **zero-tax capacity comparison B(A)** (commit `ac669f2`). That manifest is **not** a source for anything below. The two objects must not be mixed: the capacity run evaluates `tax_exempt` only, on re-dumped Tier B weights; the after-tax grid evaluates the statutory regime and `tax_exempt`, on stage-04 weights.

Tool and outputs: `tools/phase_c_recover_after_tax_config.py`, `results/phase_c_after_tax_config_recovery_2026-10-14/` (`after_tax_arms.csv`, `after_tax_weight_identity.csv`, `MANIFEST.json`).

## 1. What was recovered, and from where

Source of the commands: the project's working-session record (`~/.claude/projects/.../54ad60cf-....jsonl`, tool calls with UTC timestamps), cross-checked against file modification times, `pipelines/06_after_tax_eval.py`, `configs/base.yaml` and the tracked snapshots in `docs/attachments/`. The session record is a secondary source: the runs were not logged by the pipeline itself.

| Arm (summary file) | Recorded command (flags as typed; `$CELLS` = the 16 cells `cell_{L,N}-{S,C}-{P,E}-{0,U}`) | Recorded at (UTC) | Summary mtime (local, +05:30) |
|---|---|---|---|
| DEU 1e9 | `--country DEU --strategies $CELLS --lot-methods hifo` (no `--max-names`, no `--weights-aum`, default output, copied to `summary_after_tax_DEU_1e9.csv`) | 2026-10-08 19:22 | 2026-10-09 00:59 |
| IND 1e9 | `--country IND --strategies $CELLS --lot-methods hifo` (same shape; copied to `..._IND_1e9.csv`) | 2026-10-08 19:31 | 2026-10-09 02:03 |
| JPN 1e9 | `--country JPN --max-names 600 --strategies $CELLS --lot-methods hifo` (chain script; default output copied to `..._JPN_1e9.csv`) | 2026-10-08 20:35 | 2026-10-09 13:46 |
| DEU 1e8, 1e10 | `--country DEU --max-names 600 --strategies $CELLS --lot-methods hifo --aum A --weights-aum A --out outputs/summary_after_tax_DEU_A.csv` | 2026-10-09 08:22 (relaunch; the 08:19 launch omitted `--out`, both arms wrote the default file and collided, so it was discarded) | 13:54 |
| JPN 1e8, 1e10 | `--country JPN --max-names 600 --strategies $CELLS --lot-methods hifo --aum A --weights-aum A --out outputs/summary_after_tax_JPN_A.csv` | 2026-10-09 08:26 | 15:14 / 18:17 |

Settings not given on the command line (defaults of `pipelines/06_after_tax_eval.py` at HEAD; the file's last relevant change before these runs was `--dated` at `6e25433`, `--weights-aum` at `568fa13`):

| Setting | Value | Provenance |
|---|---|---|
| Regimes | `tax_exempt` and the statutory regime of the country resolved at `--as-of 2016-06-30`: `DEU_ABGELTUNGSTEUER`, `IND_STT100_LTCG_EXEMPT_STCG15`, `JPN_NORMAL_LISTED_SHARE_RATE_PLUS_RECONSTRUCTION` | script default; confirmed by the `regime` column of each summary |
| Lot method | `hifo` | command; confirmed by the `lot_method` column |
| Accounting | `accrual` | script default (`--accounting`) |
| Dated C14 engine | off (no `--dated`); the DEU 1e9 summary predates the `dated` column | commands; `dated = False` in the other six summaries |
| Dividend source | C4 `div_next` when the targets table has the column (flat 2% `--dividend-yield` only as an unused fallback) | `backtest.py` carries this logic since `4ea2c31` (2026-09-20), i.e. before every run above |
| Cost multiplier | 1.0 | script default |
| AUM / initial NAV | `configs/base.yaml` `aum_usd_2020 = 1.0e9`, overridden by `--aum A` for the 1e8 and 1e10 arms | config (last changed 2026-10-07, before the runs); command |
| Costs | commission 1.0 bp, `impact_k` 1.0, `impact_power` 1.5, modelled flat borrow 1.00% | `configs/base.yaml` |
| Breadth cap | `max_names = 600` on JPN and on DEU 1e8/1e10; **none** on DEU 1e9 and IND 1e9 | commands; script help (amendment 001B): slack for DEU/IND, binds on JPN; cap added at `cdebfff` |
| Exit policy | `as_run` (the `--exit-policy` flag did not exist; added at `f201f9c`, 2026-10-13) | commit dates |
| Strategies | the 16 cells above (weights also exist for 5 baselines, not evaluated here) | commands; `strategy` column (16 per summary) |
| Window | 2009-01-31 to 2019-12-31 (132 months; India 131) | `months` column |
| Pre-registration | `prereg/PLAN_001_after_tax_attribution.json`, fingerprint `cae8140b7e2b7ee4`, N=64 (its primary outcome names a US top-bracket investor; the international arms evaluate the statutory regime; that departure is not re-audited here) | prereg file |

## 2. Frozen weight references

Every summary has a `weights_index` (`outputs/weights_index/<C>_<AUM>.csv`) of 21 strategies with run ids and paths; all 16 evaluated cells per arm are present on disk (`exists = 16/16` in each of the 7 arms). The weight files and the indexes are git-ignored; SHA-256 values of the files as they are **now** are in `after_tax_weight_identity.csv` and `after_tax_arms.csv`.

| Arm | How the original run resolved weights | Evidence that the indexed weights are the ones used | Status |
|---|---|---|---|
| DEU 1e8, DEU 1e10, JPN 1e8, JPN 1e10 | pinned through `--weights-aum` (the index) | index written before the summary; tracked snapshot equals the live summary (SHA-256) | **Recovered** (identity by construction; hashes are present-state) |
| JPN 1e9 | modification time (unpinned) | indexed run predates the summary; no other stage-04 run of any of the 16 strategies lies between the indexed run and the summary; tracked snapshot equals the live summary | **Recovered, inferred** |
| DEU 1e9, IND 1e9 | modification time (unpinned) | indexed runs predate the summary and no other run of the 16 strategies lies between them and the summary; but the index file was written **after** the summary (reconstructed) and **no tracked snapshot** of these two summaries exists | **Inferred only; not provable** |

Today `outputs/weights/` has newer stage-04 runs for most strategies (only the JPN 1e10 arm's indexed runs equal the latest by modification time), which is exactly why the three unpinned arms could not be re-run by modification time now.

## 3. Gaps, reported rather than guessed

1. **No run-time hashes** of the weight files or of the code tree for any of the 7 arms. The code at each run was whatever was in the working tree; `tax/backtest.py`'s last commit before the runs is `1bbaac4` (2026-10-09 00:59), the same minute as the DEU 1e9 summary, so that run may predate its own committed code. `as_run` accounting is protected by the Phase 1/2 reproduction tests, but a bit-for-bit reproduction of the original numbers is not claimed.
2. **DEU 1e9 and IND 1e9 weight identity is inferred** (section 2), and their summaries have no tracked snapshot. If a revised analysis includes them, the weight set must be taken from the indexes and disclosed as inferred, or the arms must be dropped.
3. **All seven run commands have only a session-record source.** The pipeline writes no manifest of its own for stage 06 (the `claim_run` fingerprint guard was added later).
4. **DEU 1e9 was produced by an older version of the script** (no `dated` column; 24 columns instead of 25).
5. **Collision history:** the default `outputs/summary_after_tax.csv` is a shared fixed path; the two 08:19 launches wrote to it concurrently, and the file that remains there is not an arm. It is not used as a source.
6. **Valid-solvency list:** not applicable to these arms (no solvency filter was applied); a revised analysis that applies one must derive it with the frozen rule before inference (addendum 2).
7. **Strategy set:** the 5 baseline strategies were not part of these summaries; they are outside the recovered grid.

**Blocker status:** none of these prevents *describing* the configuration. For a revised run on the multi-regime grid, items 1 and 2 are *disclosure* requirements, not blockers, provided DEU 1e9 and IND 1e9 are labelled "weights inferred from the index".

## 4. What is **not** established here

* That the revised analysis should apply to the multi-regime grid rather than to B(A), or to both: that scoping is a decision for the reviewers (Phase C addendum 2 states the scope).
* That re-running reproduces the original numbers. The census (v3) and the carry_v1 run are separate analyses.

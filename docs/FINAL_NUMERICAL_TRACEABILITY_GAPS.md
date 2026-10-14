# Numerical traceability gaps: audit of three items (2026-10-14, sprint 2)

Internal researcher-led audit; not an external review; no approval by Maham or Absar is claimed. **Nothing was regenerated.** No experiment, training, optimisation, cost sensitivity, Phase C run or external access took place. The only numerical reading was of existing historical files (column means of already-written summaries and CSV rows, to compare with the values quoted in the documents). Untracked originals under `outputs/` were not modified. Statuses: `TRACEABLE_EXISTING_ARTIFACT`, `RECOVERABLE_WITH_EXACT_REGENERATION`, `MISSING_INPUT_OR_CONFIGURATION`, `UNKNOWN`.

| # | Item | Status | Action taken |
|---|---|---|---|
| 1 | India `lt_share_of_gains` = 0.5928 | `TRACEABLE_EXISTING_ARTIFACT` (provenance partly inferred) | verbatim snapshot committed with hash |
| 2 | Optimised-book after-tax summaries (Germany $1bn, India $1bn) | `TRACEABLE_EXISTING_ARTIFACT` (provenance partly inferred) | verbatim snapshots committed with hashes |
| 3 | Germany optimised-book after-tax inference row | `RECOVERABLE_WITH_EXACT_REGENERATION`, conditional (see 3.4); **not regenerated** | exact command, inputs, conditions and expected values recorded below; nothing run |

## 1. India `lt_share_of_gains` (0.5928)

* **Artifact:** `outputs/summary_after_tax_IND_1e9.csv` (untracked, git-ignored), modification time 2026-10-09 02:03:38 +0530, sha256 `e2fd34229e1e8b38f997...`, 32 rows, 25 columns. Mean of `lt_share_of_gains` over the 8 prediction cells (`-P-`) of the statutory regime (`IND_STT100_LTCG_EXEMPT_STCG15`): **0.5928**.
* **Is the file valid for this use?** The same file's cell means also reproduce the other India values the project quoted for the $1bn optimised-book table (net Sharpe 0.205, after-tax 0.201, turnover 0.0067, tax drag 0.11 bps, cost drag 9.96 bps). Five other `outputs/summary_after_tax_*.csv` files (DEU 1e8, DEU 1e10, JPN 1e8, JPN 1e9, JPN 1e10) are byte-identical to their tracked snapshots in `docs/attachments/`, which is consistent with the local `outputs/` files being the originals and not later overwrites. That is supporting evidence, not proof for this specific file.
* **Provenance record:** the command and settings are recovered in `docs/PHASE_C_AFTER_TAX_CONFIGURATION_RECOVERY_2026-10-14.md` (stage 06, statutory regime plus `tax_exempt`, HIFO, accrual, no `--dated`, no `--max-names`, 16 cells, 131 months). The weight set is **inferred** (modification-time ordering; the weights index `outputs/weights_index/IND_1e9.csv` was written after the summary), and no run-time hashes of code or weights exist.
* **Decision:** the value is present in an existing historical artifact whose content matches every documented value, so no regeneration is needed or proposed. A byte-identical copy was committed as `docs/attachments/SUMMARY_AFTER_TAX_IND_1E9_2026-10-09.csv` (sha256 verified equal to the original). The original was not touched. Disclose in any submission that the run-time provenance is only partly recoverable.
* **Regeneration, if ever wanted:** the stage 06 command in the recovery document, on the code tree of the time (not recoverable exactly: no tree hash), would be a reproduction attempt only if inputs and code match, and a new analysis otherwise. Not authorised, not needed for this item.

## 2. Optimised-book summaries (the "snapshot needed" item)

* **Existing tracked snapshots:** DEU $100mn and $10bn, JPN $100mn, $1bn and $10bn (all byte-identical to the local originals).
* **Missing tracked snapshots (now supplied):** `outputs/summary_after_tax_DEU_1e9.csv` (sha256 `84a8d5ff172cf1f6...`, mtime 2026-10-09 00:59:33, **24 columns**, i.e. produced by an older version of the script: no `dated` column) and `outputs/summary_after_tax_IND_1e9.csv` (above). Verbatim copies: `docs/attachments/SUMMARY_AFTER_TAX_DEU_1E9_2026-10-09.csv` and `..._IND_1E9_...`.
* **Contents versus documents (cell means over the 8 prediction cells; statutory regime for tax figures, `tax_exempt` for net Sharpe):**

| | net SR | after-tax SR | turnover | tax bps | cost bps | `lt_share` |
|---|---|---|---|---|---|---|
| Germany $1bn (file) | 0.128 | 0.0175 | 0.0135 | 6.38 | 17.21 | 0.0000 |
| paper section 6.3 | +0.128 | +0.018 | 0.0135 | 6.38 | 17.21 | 0.0000 |
| India $1bn (file) | 0.205 | 0.201 | 0.0067 | 0.11 | 9.96 | 0.5928 |
| paper section 6.3 | +0.205 | +0.201 | 0.0067 | 0.11 | 9.96 | 0.5928 |
| Japan $1bn (tracked snapshot) | 0.057 | -0.049 | 0.0290 | 11.49 | 42.31 | 0.0000 |
| paper section 6.3 | +0.057 | -0.049 | 0.0290 | 11.49 | 42.31 | 0.0000 |

* **Caveats that stay:** weight identity inferred (Germany and India); Germany produced by older code; no run-time code or weight hashes. These snapshots are historical as-run artifacts, not new results.
* **Effect on the candidate:** the turnover and tax-drag ordering at $1bn (Germany 0.0135 / 6.38, India 0.0067 / 0.11, Japan 0.0290 / 11.49) is now traceable and is stated descriptively with the caveats.

## 3. Germany's optimised-book after-tax inference statistic

### 3.1 What exists

The values (net Sharpe +0.1523, t +0.53, p 0.595; after-tax Sharpe +0.016, t +0.06; tax channel -0.1363, t -4.67, p < 0.0001, 95% interval [-0.196, -0.087]; 3 of 8 cells under Holm) exist only as **secondary records**: the message of commit `0e62a95` and `docs/RESULTS_TAX_THREE_COUNTRY_2026-10-09.md` (as of that commit). The CSV written by the same tool and committed in `0e62a95` (and the untracked `outputs/after_tax_inference/after_tax_inference_1e9.csv`, written 2026-10-09 17:25:08) contain India and Japan only. No file anywhere in the repository or the local outputs contains the German composite or per-cell rows.

### 3.2 Why the artifact lacks Germany (not established)

The tool writes one fixed-path file per AUM (`after_tax_inference_1e9.csv`) and, at that time, had no overwrite guard (`alphacomb.output_guard` was added on 2026-10-14, `8ec5cad`). The printed German values mean Germany was processed in some invocation; the surviving file is from an invocation that did not include it. A fixed-path overwrite by a later invocation is a plausible explanation and matches the failure class the project already documented ("fixed path, two runs overwrote each other"), but **it is a hypothesis, not a finding**: no log of the invocations exists.

### 3.3 Can the original be recovered? Inputs and configuration

| Requirement | State |
|---|---|
| Tool and its code | `tools/exp_after_tax_inference.py` at `0e62a95` (same tool at HEAD differs only by the output-collision guard, `8ec5cad`) |
| Weights | `outputs/weights_index/DEU_1e9.csv` (mtime 2026-10-09 01:37:34) lists 8 prediction-cell weight parquets, all present on disk. Identity inferred: the index was written after the summary; no run-time hash |
| Data bundle | `intl.load_country_bundle("DEU", max_names=600)` from the untracked `data/`; production tables are dated 2026-10-08 (before the run) but **no hash of them was recorded before 2026-10-14**, so unchanged-since-the-run is plausible, not provable |
| Config | `load_config("base")` with `costs.aum_usd_2020 = 1e9`; statutory regime `statutory_regime("DEU", "2016-06-30")`; `LotMethod("hifo")`, accrual, `dividend_yield_annual = 0.02`, initial NAV $1bn; breadth cap 600 (slack for Germany, whose worst month has 438 names; amendment 001B) |
| Inference | `sharpe_difference_test` studentised bootstrap, `n_boot = 2000`, block 6, seed 0; per-cell Holm bootstrap `min(n_boot, 800)`. **The inference library changed after the run** (`26957cc`, 2026-10-13), as did `tax/backtest.py` (`f201f9c`, opt-in `carry_v1`, default unchanged) and `tax/lots.py` |

### 3.4 Exact regeneration that would be needed (**not run, not authorised**)

```
git worktree add <new dir> 0e62a95          # the code state that produced the historical row
# in that tree, with the same untracked data root and the same outputs/weights_index/DEU_1e9.csv available:
python tools/exp_after_tax_inference.py --country DEU --aum 1e9 --out <new, empty directory>
```

Expected artifact: `<out>/after_tax_inference_1e9.csv` with a `composite` row and 8 `cell` rows for Germany; expected composite values as in 3.1. Provenance conditions for treating a match as a reproduction: new, empty output directory (never the old path); the run's stdout, command, `git rev-parse HEAD` of the worktree, and SHA-256 of the 8 weights files, of the production C1/C4/C6/C14 inputs and of the output recorded at run time; the result labelled "reproduction of a historical statistic" and kept separate from every revised result.

* **Run on the `0e62a95` tree with the same inputs:** this is an **exact historical reproduction attempt**. A match would restore a traceable artifact (with the weight identity still "inferred"). A mismatch would show that inputs or code differ and would **not** recover the historical number.
* **Run on HEAD:** this would be a **new analysis** (corrected inference library, later engine code), not a reproduction, and its numbers would not substitute for the historical ones.
* **Authority:** neither is authorised by the sprint instructions; the decision is the authors'. A mismatch is a possible outcome and must be disclosed, not resolved by choosing the version that matches the documents.

### 3.5 Classification

`RECOVERABLE_WITH_EXACT_REGENERATION`, conditional on (a) the `0e62a95` code state, (b) the inferred weight identity, (c) unchanged data. Component (c) cannot currently be verified (no recorded input hashes), so a successful reproduction would be informative and a failed one inconclusive about the cause. Until then Germany's optimised-book net-Sharpe and tax-channel figures stay `UNVERIFIABLE` and are omitted from the candidate; the matched-book decile-book figures for Germany (committed) are used instead.

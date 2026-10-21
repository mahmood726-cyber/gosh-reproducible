# GOSH plots in the browser: validation against the R package metafor

Validated allmeta GOSH fix commit `e749e98871dd2665b71e99cc998ac1ff8c50effe` (PR #119) and Validate panel commit `5e20358918c9366eb10c1a368f2ca1b0480faa84` (PR #121). Source page before the panel: SHA-256 `5f75ca566ba96f6f29923ea23cfd75de1f9a955bfeb87d610737776a4929a79c`. Upstream repository: https://github.com/mahmood726-cyber/allmeta. Release: allmeta release v1.5.0, https://github.com/mahmood726-cyber/allmeta/releases/tag/v1.5.0; DOI 10.5281/zenodo.23414184.

This archive tests FE/DL numerical software against **R 4.6.0, metafor 5.2-1, metadat 1.6-0**. It does not establish clinical independence of dependent/multivariate rows. Package examples include documented hypothetical/simulated datasets; these are explicitly software fixtures, not invented research findings.

The source construction searched 114 metadat datasets: 113 yielded **222 effect configurations × FE/DL = 444 model configurations**. Of the effect configurations, **88** were enumerated, **120** sampled, and **14** exceeded the page's 100-row cap. `dat.metap` supplies p-values without suitable effect/variance inputs. The data directory preserves source rows, recipes, exclusions, preparation attempts, coverage, documentation and the configuration ledger. No input rows are silently truncated.

Full historical comparison: **12,803,218/12,804,532 before → 12,813,556/12,813,556 after**. Fixes include omitted singleton subsets, misleading sampling/default claims, stale displays after refusal, explicit-axis padding, and later finite-coordinate/axis safeguards. The latest UI audit is **21,586/21,586** (round 11), extending the earlier **13,024/15,024 → 15,024/15,024** options matrix. These are different audit scopes; see bench/RESULTS.md and bench/REPORT11.md. Cap checks do not represent fitted R agreement.

## Reproduce

Use installed R and Python dependencies; no package downloads are performed. R needs metafor, metadat, jsonlite and digest. Python needs matplotlib and Pillow. Set `R_LIBS_USER` to the library containing the exact versions, and set `R_ENVIRON_USER` to an empty file before starting R (a user's .Renviron may otherwise override the library). The validator prepends this library and prints `.libPaths()` and loaded versions, then fails on a version mismatch.

The Python figure-library versions used here are pinned in `requirements.txt`. The figures were visually inspected; PNG/TIFF agreement, dimensions, DPI and deterministic regeneration are checked by the verifier.

```text
Rscript validate.R
python analysis/make_outputs.py
python analysis/test_safeguards.py
python analysis/verify_archive.py
```

`validate.R` SHA-256 checks inputs, validates exact keyed coverage, and processes every configuration with four R worker processes, fitting every accepted configuration and checking all page-cap refusals. It uses `gosh(rma(...))` for enumeration and `rma` on every captured sampled membership in original row order, retaining repeated draws. It prints the per-quantity comparison and final N/N verdict, writes `outputs/validate_R_table.csv`, and exits nonzero on any mismatch. Existing `.validate-work/reference` outputs are refused to prevent stale-cache success; move that directory aside before a new full run. The historical full reference wall time was 6852.135 seconds with four workers; this is a long computation, not a quick replay. R reruns statistical references; browser geometry checks use saved browser observations.

The paper uses 1e-9 relative to max(1, |R|), except I² uses difference / 100 <= 1e-9; memberships, cardinalities and categorical values are exact. The app panel uses the stricter relative tolerance for live I². Its declared browser replay is only 876,760 checks, covering all k <= 12, two fixed sampled configurations, and all page-cap configurations, both models. It is explicitly separate from this archive's full comparison.

## Layout and limits

`app/` contains byte-identical page dependencies and a SHA-256 inventory. They match allmeta commit 5e20358 except `app/r-shiny/shinylive/webr/repo/manifest.json`, which is kept as validated: at 5e20358 it also lists the metasens package (used by another app, not by GOSH), which is not shipped here. `bench/` preserves audit scripts (machine paths replaced with a redaction token), documentation and reports. `data/` contains input/provenance. `results/` uses the source per-configuration files and indexes instead of consolidated files exceeding GitHub's limit; no evidence records are discarded. Each file must stay below 90 MB. `expected/` holds the count contract. `analysis/` rebuilds comparison tables, figures, hashes and negative checks; `outputs/` contains derived results, not source evidence.

FE/DL only. Enumeration includes all non-empty subsets for k <= 15. The page's fixed-seed sampler selects uniform subset size 2..k with replacement and defaults to 5,000 draws; this differs from metafor's default. Inputs above 100 rows are refused. Sampled SE and internal Q/tau² are supplemental engine checks. No general clinical-validity or release-certification claim is made.

| Item | Static | Dynamic/source-backed |
|---|---|---|
| Models and limits | FE/DL, cutoff, cap, seed, tolerance | Actual captured memberships and engine values |
| Corpus | Source files, recipes and expected inventory | Exact coverage checks and fresh R refits |
| Findings | Historical before/after raw captures | Recomputed comparisons, tables and figures |
| App bundle | Byte-identical current assets and pins | Browser replay, live R and display mutations |

Results JSON is stored as deterministic xz, preserving each per-configuration path with a `.xz` suffix. Logical JSON paths inside evidence are unchanged; analysis readers resolve them to compressed storage. Redundant membership text exports are regenerated byte-for-byte from archived JSON into ignored `.validate-work/memberships/` before R runs; their original and regenerated hashes are recorded in `analysis/membership_compression_proof.json.xz`. No membership values are discarded. All inventories hash the stored compressed bytes. `analysis/compression_proof.json.xz` records canonical and exact-byte equality before original deletion. Scratch directories are ignored and excluded from all inventories.

Source JSON in `data/` is also stored as xz, with exact-byte and canonical preservation proof in `analysis/data_compression_proof.json.xz`. Native R reads the corpus through `xzfile`; the RDS/JSON equality gate is retained. TIFFs use lossless deflate compression with unchanged pixels and 300 dpi.

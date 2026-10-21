# Equivalence of the archived exact layer with allmeta v1.8.0

allmeta v1.8.0: tag `v1.8.0`, commit `1cb3f8409c7af75ed41f7e1811f9c502f900fc79`, DOI 10.5281/zenodo.23515177.
The exact all-subsets layer (`v1_1/exact/`) was taken from commit `1e3ef389cdfbce7c735c32e2794e67d3cbefb622`
(pull request #167), which is an ancestor of v1.8.0. `gosh/` is unchanged between the two commits.

All 21 files listed in `v1_1/PROVENANCE.json` were compared with their v1.8.0 blobs. 18 are byte-identical
(Git blob ids equal), including the four page files `gosh/exact-enum.js`, `gosh/exact-ui.js`, `gosh/index.html`
and `gosh/plus.js`, the corpus, both saved references, the manifest, the comparator, the numeric replay script and
its references, and both test files. The other three are the documented archive adaptations; their upstream
source blobs are unchanged in v1.8.0:

| File | Difference from v1.8.0 | Effect on results |
|---|---|---|
| `v1_1/exact/generate-exact-r.R` | archive adds an R 4.6.0 assertion (upstream blob `e4b1bb7` unchanged in v1.8.0) | none (optional R regeneration; not run by the replay) |
| `v1_1/exact/generate-exact-metafor.R` | archive adds an R 4.6.0 assertion (upstream blob `64a7187` unchanged in v1.8.0) | none (optional R regeneration; not run by the replay) |
| `v1_1/exact/replay.cjs` | archive-relative engine path, in-memory estimate plant, labelled totals (upstream blob `c3ec710` unchanged in v1.8.0) | none (comparison driver; engine bytes are the v1.8.0 bytes) |

No file needed replacing.

Check by execution (21 Oct 2026, Node v24.13.0, Python 3.13.13, Windows) on these v1.8.0 bytes:

- `ARCHIVE_V1_1_ONLY=1 python validate.py`: `EXACT R 345842/345842` (max normalised difference 8.54e-15) and
  `EXACT METAFOR 182826/182826` (5.62e-15), equal to the archived `outputs/v1_1/exact-clean.log`. The
  per-quantity `summary` block of the audit JSON is identical to the archived `outputs/v1_1/exact-clean.json`;
  only the `runs` timing block differs.
- Planted defects still fail (exit 1) with the archived counts: `--plant estimate` R 345841/345842 and metafor
  182826/182826; `--plant drop` R 343643/345842 and metafor 181759/182826.
- `node v1_1/exact/gosh/validate/replay-numeric.cjs`: base 533726/533726 and extras 584662/584662.
- `node v1_1/exact/gosh/tests/exact-enum.test.cjs` 19/19 pass; `exact-compare.test.cjs` 2/2 pass.
- `python v1_1/archive.py safeguards`: 11 tests OK. `python v1_1/archive.py replay`: legacy comparison
  12813556/12813556, unchanged.

R references were not regenerated. The layer has no browser tier.

The legacy v1.0 tier (`app/`, pinned at commit `5e20358918c9366eb10c1a368f2ca1b0480faa84`, allmeta v1.5.0) is
kept unchanged as validated and is not re-pinned; it is not claimed to be byte-identical to v1.8.0.

All of the archive's exact-tier comparison results therefore apply unchanged to allmeta v1.8.0.

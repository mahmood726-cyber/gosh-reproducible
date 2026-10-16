# GOSH round 11

PASS. Tests and audit harness changes only. Production page unchanged (SHA-256 `5f75ca566ba96f6f29923ea23cfd75de1f9a955bfeb87d610737776a4929a79c`). No commit/push; registry and workbook unchanged.

## Fixture strength

The shared 76-state FE/DL matrix now supplies distinct effects `(13 + 137*i)/100`, distinct non-unit SEs `(231 + 70*i)/1000`, and distinct labels `Distinct_11`, `Distinct_12`, etc. Node and native Chrome load these same study objects. Every supplied column is unique across studies and avoids 0, 1, 0.5, 2 and 10; a new pytest contract protects this requirement for all nonempty matrix sizes, including the 101-row refusal.

The independent Python oracle calculates inverse-variance FE estimates, DL estimates, Q/I², quantiles, and the documented fixed-seed sampled memberships directly from these fixture inputs. It never reads page results to construct expectations. Enumeration, 37/default-5000 sampling, refusals/recovery, producer failures, explicit/invalid axes and omissions remain covered. Existing special equal-value, roundoff, subnormal and overflow fixtures in the regression suite and native harness are retained; the distinct matrix runs alongside them.

Near-equal circle coordinates are sorted with rounded ordering keys to prevent harmless floating-point ties from mismatching different points; values are still compared with the existing absolute 1e-12 tolerance. An explicit `plot_empty` assertion now rejects plain text left in a refused/invalid plot even when there are no SVG geometry elements.

## Mechanical mutation sweep

`python mutate11.py`: **1232 inventory entries; 811 executed mutants; 811 assertion kills; zero survivors; zero execution/setup errors; 421 individually explained exclusions.** Evidence: `round11-inventory.json`, `round11-mutations.json`, `round11-inventory-results.log`, and source/result pairs in `round11-mutants/`.

The original AST-derived sink sweep remains. Added zero/one substitutions at displayed declarations, DOM/SVG sinks, serialized inputs and exported payload expressions; first-element and same-name-input operators are inventoried as well. Each result-download and chart-receipt result field is mutated independently, including nested labels, effects and SEs. First-study substitutions exercise nested fields. Array-valued fields use their first element; strings use their first character at DOM sinks. For derived scalars without a collection or same-name input, null is an explicit type-corruption operator. Static scalars without such an input/element are marked inapplicable.

Identity substitutions are excluded, not counted as kills: examples include a literal already equal to zero, the first character of a one-character string, and replacing an exported study SE with that same study's input SE. Those cannot be rejected by a correct test. Existing decorative/internal exclusions and duplicate-slot explanations remain in the inventory. Thus zero survivors describes the executed, nonidentity operators, not all possible faulty programs.

Mutants first run against the small enumerated cases; those still alive run the full matrix and restoration contract. Four subprocess workers are used; no sub-agents. Initial generator errors (unparenthesized number literals before `.toString()` and nonstring DOM-value replacements) were corrected, not counted as kills. The final evidence has no such errors. One malformed-SVG output was initially classified as a parser error; after making invalid SVG an explicit output-contract assertion, that mutant was rerun and its result replaced in the aggregate (full sweep plus one targeted rerun).

The exact round-10 callback-only SE=`1` replacement fails pytest and native Chrome: **52 native export checks fail**, while the unmodified page passes. Evidence: `round11-review-se-one-pytest.log`, `round11-review-se-one-capture.log`, `round11-review-se-one-comparison.log`, `round11-review-se-one-native.json`; reproduce with `python native11.py`. The mechanical callback SE-one mutant also dies on export assertions.

## Verification

| Check | Result |
|---|---|
| `python -m pytest gosh/tests -q` in `allmeta` | 101 passed; `round11-pytest.log` |
| `python scripts/lint_repo.py` in `allmeta` | PASS; pre-existing non-gating proportion-ma consolidation note; `round11-lint.log` |
| `python capture_matrix11.py` | 76 states × 25 fields = 1,900 logical checks; `round11-matrix.json` |
| Native `node test_ui.cjs patched`, then `python compare_options.py patched` in `../codex15` | 21,586/21,586; `round11-ui.log`, `round11-ui-comparison.log` |
| `python compare.py patched` in `../codex15` | 12,813,556/12,813,556; `round11-comparison.log` |
| `python package11.py` | `../codex15/fix.patch` regenerated; whitespace and reverse-apply checks PASS; `round11-source-check.json` |

UI changes by key: **`numeric_matrix_plot_empty`: absent/0 → 76 (+76)**. All other keys unchanged; total 21,510 → 21,586. Corpus changes by key: none. Machine-readable deltas are in `round11-ui-count-changes.json` and `round11-corpus-count-changes.json`.

The corpus was re-compared from saved captures/references, not re-captured; the page hash still matches the saved capture manifest. The patch is cumulative with the prior rounds; round 11 itself changes only tests/harnesses. Native axis transitions still use the audit callback, and receipt signing remains intercepted at its input boundary; this does not establish keyboard/mouse coverage or cryptographic signing correctness.

## Static versus dynamic disclosure

| Item | Static/dynamic | Evidence/limit |
|---|---|---|
| Distinct fixture sequences, schemas, state semantics | Static test contracts | Synthetic software fixtures, not research findings |
| Weighted estimates, sampling, quantiles, coordinates | Dynamic independent calculation | From fixture inputs, never page outputs |
| Mutation inventory | Dynamic source scan plus schema-driven callback paths | Operator limits and identities disclosed above |
| Matrix, callback and native observations | Dynamic execution | Actual page/callback behavior; signing intercepted |
| Corpus | Dynamic re-comparison | Existing captures and reference data; source hash unchanged |

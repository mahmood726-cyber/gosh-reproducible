# GOSH versus metafor validation

Source commit: `bdf777fb074804e09de59ac63db55f0ad90b2241`. Original source files were verified unchanged. All modifications are confined to the audit folder; [fix.patch](fix.patch) is a proposed patch, not an applied upstream change.

Original: **12803218/12804532 checks pass**. Patched: **12813556/12813556 checks pass**.
UI options: original **13024/15024**, patched **15024/15024**.

These totals separate coverage checks, per-subset numeric checks, summaries, rendering and page-cap checks. Page-cap refusals are not statistical agreement with R.

Versions: R version 4.6.0 (2026-04-24 ucrt); metafor 5.2.1 (the requested 5.2-1 release); metadat 1.6.0; meta 8.5.0; Chrome 155.0.8059.40.

## Corpus and evidence
114 datasets were enumerated programmatically from metadat; 113 supplied 222 effect-size configurations. Both FE and DL were requested, giving 444 model configurations. There were 88 enumerated, 120 sampled, and 14 over-cap effect configurations.
Numeric outputs were obtained from 101 datasets in 416 model configurations. Datasets whose configurations were all refused by the page cap: dat.bakdash2021, dat.besson2016, dat.curtis1998, dat.hartmannboyce2018, dat.lim2014, dat.linde2016, dat.mccurdy2020, dat.mcdaniel1994, dat.moura2021, dat.tannersmith2016, dat.white2020, dat.yusuf1985.
The only dataset without constructed effects was dat.metap: p-value collections without effect sizes and variances. Definitions, preparation warnings/errors, omitted rows, duplicate aliases and exclusions are retained in [coverage.json](coverage.json), [construction-attempts.json](construction-attempts.json), [configuration-ledger.csv](configuration-ledger.csv) and the installed [documentation](documentation/). The corpus uses stored effects and documented constructions, with explicit schema-checked supplemental endpoints. Different documented effect/variance vectors within a dataset are separate configurations; identical vectors are deduplicated.
Non-finite effects or non-positive variances are recorded and excluded before input, consistent with the page parser. Configurations with fewer than three valid rows are recorded in construction attempts. Inputs above 100 rows are passed to the page and reported as page-limit refusals, without truncating studies. Package examples may include hypothetical or simulated data as documented by metadat; this is a software-validation corpus, not a claim of independent clinical evidence. Dependent/multivariate rows are marginal numerical checks; clinical independence is not inferred.
Complete original-page records are consolidated in [app.json](app.json), with R results in [reference.json](reference.json). The corrected page records are indexed by [app-patched.json](app-patched.json) under the app-patched directory. Compact [app-index.json](app-index.json) and [reference-index.json](reference-index.json) link the per-configuration evidence without requiring the full files to be loaded.
All numerical inputs are in [corpus.json](corpus.json). Variances supplied to both engines are the same binary64 SE-squared values. Membership indices are one-based positions in the retained configuration, not inferred trial identifiers. Recipe and source-row information retain provenance.

## What was run
The shipped parser accepts finite effects and positive SEs; the page accepts 3 through 100 retained rows. Original enumeration produces 2^k - 1 - k subsets (sizes 2 through k); the patch produces 2^k - 1 (sizes 1 through k) for k <= 15. Above 15 the fixed seeded sampler draws 5,000 subsets by default, uniformly selecting size 2 through k and retaining repeated memberships. The control allows changing the draw count.
The shipped sampler is labeled xoshiro128** and resets its four-word state to [0xdeadbeef, 0x12345678, 0xabcdef01, 0x87654321] on every run. A partial Fisher-Yates shuffle selects distinct indices within each draw; memberships can repeat across draws.
The summary cards show draw/subset count, median estimate to three decimals, and median I2 to one decimal plus a percent sign. Export additionally includes type-7 estimate quartiles, minimum and maximum. Every retained result is plotted. Default X limits are min/max plus 10 percent of the estimate span (0.1 padding when constant); Y limits are 0 to 100 percent. Explicit X/Y overrides and both pooling models were exercised.
The real HTML page and its local dependencies were copied byte-for-byte and loaded via file URLs in headless Chrome. A CDP debugger wrapper around the private pool function records the actual ordered input memberships and returned values while invoking the original function unchanged. No pooling or sampler was reimplemented. The page itself calculates summaries and renders the SVG. Independent uninstrumented-page checks confirm the wrapper does not change output.
For k <= 15 the reference calls gosh(rma(yi, vi, method=...)) and compares every exact membership, irrespective of ordering. For 16 <= k <= 100 it calls rma on every captured draw using that draw’s actual member order, for both methods. Repeated sampled memberships retain a draw-occurrence key. No sampled draws are discarded. The default sample size is 5,000.
Reference values use 17 significant digits. Missing reference/app evidence, missing/extra subsets, non-finite comparisons and unexpected refusals cannot pass. Q, tau2 and SE captured from the private pool are supplemental engine checks: the displayed per-subset scatter itself exposes estimate and I²; k is retained internally. SE is checked against rma for sampled cases; GOSH does not return subset SEs.
Numeric tolerance is 1e-9 relative to max(1, abs(reference)) for estimates, Q, tau2 and SE. I² uses abs(app-reference)/100 <= 1e-9, i.e. 1e-7 percentage points on its 0–100 scale. Counts, memberships and k are exact. Numeric exact-check maxima are absolute differences; categorical exact-check maxima are 0/1 mismatch indicators. Numeric summaries use the same scale-specific tolerances. Displayed labels are checked at their actual decimal precision; Default SVG coordinates use absolute 1e-9; explicit-axis checks use 1e-9 relative to max(1, abs(expected coordinate)).

## Findings and fixes
1. **Singleton omission:** original gosh/index.html excludes subset.length < 2 in allSubsets despite claiming all non-empty subsets. The installed metafor documentation explicitly includes subset sizes 1 through k; the original fixture further filters k >= 2, concealing this error. The patch includes singleton subsets. Exact set coverage and full-reference summaries are rerun.
2. **Incorrect sampling claims:** the footer claims the k > 15 switch matches metafor, and the control claims a 10,000 default. Installed gosh.rma enumerates when 2^k - 1 <= 1,000,000 (k <= 19), otherwise draws 1,000,000 by default with binomial subset-size probabilities. The app draws 5,000 by default, uniformly chooses sizes 2 through k and samples with replacement using its fixed seeded generator. The patch states these differences explicitly without changing the sampler.
3. **Stale refused-input display:** the original clears the count/export but retains old plotted points and medians when the 3–100-row gate refuses input. The patch clears the chart and medians as well.
4. **Incorrect explicit X limits:** draw applies plot padding twice when assigning overridden X limits. The original fails all 2,000 tested X coordinates under explicit limits; the patch reverses the offset signs so requested limits are honored. Y limits and numerical pooling are unchanged.
See [gosh-documentation.txt](gosh-documentation.txt), [gosh-source.txt](gosh-source.txt), [fix.patch](fix.patch), and per-configuration failures/coverage in the results JSON files. The metafor-default metadata is derived from this installed source; the audit does not pretend to have run one million default GOSH samples for every large dataset.

## Per-quantity results
| Quantity | Original pass/checks | Patched pass/checks | Original max difference | Patched max difference |
|---|---:|---:|---:|---:|
| app_cap_refusal | 28/28 | 28/28 | 0 | 0 |
| app_evidence | 416/416 | 416/416 | 0 | 0 |
| axis_labels | 416/416 | 416/416 | 0 | 0 |
| configuration_key | 444/444 | 444/444 | 0 | 0 |
| coverage | 240/416 | 416/416 | 1 | 0 |
| display_count | 416/416 | 416/416 | 0 | 0 |
| display_median_est | 416/416 | 416/416 | 0 | 0 |
| display_median_i2 | 416/416 | 416/416 | 0 | 0 |
| plot_x | 1783856/1783856 | 1785360/1785360 | 6.8212102632969618e-13 | 6.8212102632969618e-13 |
| plot_y | 1783856/1783856 | 1785360/1785360 | 0 | 0 |
| plotted_count | 416/416 | 416/416 | 0 | 0 |
| reference_key | 444/444 | 444/444 | 0 | 0 |
| reference_present | 444/444 | 444/444 | 0 | 0 |
| reference_success | 416/416 | 416/416 | 0 | 0 |
| refusal_clears_chart | 0/28 | 28/28 | 5000 | 0 |
| sampling_control_visibility | 416/416 | 416/416 | 0 | 0 |
| sampling_mode | 416/416 | 416/416 | 0 | 0 |
| subset_I2 | 1783856/1783856 | 1785360/1785360 | 3.880984422721667e-13 | 3.880984422721667e-13 |
| subset_Q | 1783856/1783856 | 1785360/1785360 | 5.557136474135372e-12 | 5.557136474135372e-12 |
| subset_k | 1783856/1783856 | 1785360/1785360 | 0 | 0 |
| subset_mu | 1783856/1783856 | 1785360/1785360 | 2.3961388428972441e-13 | 2.3961388428972441e-13 |
| subset_se | 1200000/1200000 | 1200000/1200000 | 1.9472548573595816e-12 | 1.9472548573595816e-12 |
| subset_tau2 | 891928/891928 | 891928/891928 | 5.3318388665190428e-13 | 5.3318388665190428e-13 |
| summary_input_k | 416/416 | 416/416 | 0 | 0 |
| summary_max_est | 244/416 | 416/416 | 0.78015601486147734 | 3.7747582837255322e-15 |
| summary_median_est | 294/416 | 416/416 | 0.012231300340402679 | 1.4432899320127035e-15 |
| summary_median_i2 | 290/416 | 416/416 | 0.86933729588414532 | 1.0373923942097462e-14 |
| summary_min_est | 240/416 | 416/416 | 0.93445573395219461 | 6.9147306759257787e-16 |
| summary_model | 416/416 | 416/416 | 0 | 0 |
| summary_n_subsets | 240/416 | 416/416 | 15 | 0 |
| summary_q25_est | 244/416 | 416/416 | 0.027397034778827045 | 1.3322676295501878e-15 |
| summary_q75_est | 250/416 | 416/416 | 0.048195953209316696 | 8.3266726846886741e-16 |
| unique_enumeration | 176/176 | 176/176 | 0 | 0 |

## Runtime and exact final lines
Original browser: 623.743 s. Final patched browser: 740.561 s. Reference wall time: 6852.135 seconds; exit codes [0, 0, 0, 0]. Per-configuration R runtimes and warnings are in reference.json; reference workers ran concurrently.

```text
12803218/12804532 checks pass
12813556/12813556 checks pass
13024/15024 UI checks pass
15024/15024 UI checks pass
```

## Reproduction
Set ALLMETA_ROOT to the read-only source checkout, PLAYWRIGHT_ROOT to its installed Playwright module, and R_LIBS_USER to the supplied R library. No installation or network access is required. Run from this audit directory:

```text
Rscript --vanilla prepare.R
python setup.py
Rscript --vanilla corpus.R
python make_patch.py
node run_app.cjs original
python run_reference.py
node run_app.cjs patched
python prepare_ui.py
node test_ui.cjs original
node test_ui.cjs patched
python compare.py original
python compare.py patched
python compare_options.py original
python compare_options.py patched
python report.py
```
The execution used concurrent browser/reference workers; reference.R waits for sampled-membership files. Console captures are comparison-*.txt, ui-comparison-*.txt and reference-*.log. The comparison scripts are the equivalent browser E2E contract for this audit. Existing static/reimplemented fixture tests were reviewed as orientation, not counted as live browser evidence.

## Static versus dynamic disclosure
| Item | Type | Basis |
|---|---|---|
| Models and tolerances | Static | Task contract |
| Enumeration cutoff, cap, seed and default draw count | Static | Inspected shipped page |
| Dataset values and transformations | Dynamic | Installed metadat, stored columns and documented recipes |
| Reference outputs | Dynamic | Actual metafor GOSH/rma calls |
| App memberships, values, summaries and circles | Dynamic | Actual Chrome page execution |
| Counts, maxima and verdicts | Dynamic | Comparison artifacts |

## Dataset ledger
| Dataset | Configurations | Status/reason |
|---|---:|---|
| dat.aloe2013 | 3 | used: stored or documented effect-size definition |
| dat.anand1999 | 2 | used: stored or documented effect-size definition |
| dat.anker2025 | 4 | used: stored or documented effect-size definition |
| dat.assink2016 | 1 | used: stored or documented effect-size definition |
| dat.axfors2021 | 1 | used: stored or documented effect-size definition |
| dat.bakdash2021 | 1 | used: stored or documented effect-size definition |
| dat.baker2009 | 1 | used: stored or documented effect-size definition |
| dat.bangertdrowns2004 | 1 | used: stored or documented effect-size definition |
| dat.bartos2023 | 4 | used: stored or documented effect-size definition |
| dat.baskerville2012 | 1 | used: stored or documented effect-size definition |
| dat.bassler2004 | 2 | used: stored or documented effect-size definition |
| dat.bauer2002 | 2 | used: stored or documented effect-size definition |
| dat.bcg | 1 | used: stored or documented effect-size definition |
| dat.begg1989 | 2 | used: stored or documented effect-size definition |
| dat.berkey1998 | 1 | used: stored or documented effect-size definition |
| dat.berkey1998r | 1 | used: stored or documented effect-size definition |
| dat.besson2016 | 1 | used: stored or documented effect-size definition |
| dat.bonett2010 | 3 | used: stored or documented effect-size definition |
| dat.bornmann2007 | 1 | used: stored or documented effect-size definition |
| dat.bourassa1996 | 1 | used: stored or documented effect-size definition |
| dat.cannon2006 | 7 | used: stored or documented effect-size definition |
| dat.chiarito2020 | 6 | used: stored or documented effect-size definition |
| dat.cohen1981 | 1 | used: stored or documented effect-size definition |
| dat.colditz1994 | 1 | used: stored or documented effect-size definition |
| dat.collins1985a | 6 | used: stored or documented effect-size definition |
| dat.collins1985b | 5 | used: stored or documented effect-size definition |
| dat.craft2003 | 1 | used: stored or documented effect-size definition |
| dat.crede2010 | 1 | used: stored or documented effect-size definition |
| dat.crisafulli2020 | 1 | used: stored or documented effect-size definition |
| dat.curtin2002 | 1 | used: stored or documented effect-size definition |
| dat.curtis1998 | 1 | used: stored or documented effect-size definition |
| dat.dagostino1998 | 3 | used: stored or documented effect-size definition |
| dat.damico2009 | 2 | used: stored or documented effect-size definition |
| dat.debruin2009 | 1 | used: stored or documented effect-size definition |
| dat.demir2022 | 1 | used: stored or documented effect-size definition |
| dat.dogliotti2014 | 1 | used: stored or documented effect-size definition |
| dat.dong2013 | 1 | used: stored or documented effect-size definition |
| dat.dorn2007 | 1 | used: stored or documented effect-size definition |
| dat.dumouchel1994 | 1 | used: stored or documented effect-size definition |
| dat.egger2001 | 2 | used: stored or documented effect-size definition |
| dat.feng2019 | 2 | used: stored or documented effect-size definition |
| dat.fine1993 | 5 | used: stored or documented effect-size definition |
| dat.franchini2012 | 1 | used: stored or documented effect-size definition |
| dat.frank2008 | 4 | used: stored or documented effect-size definition |
| dat.furukawa2003 | 3 | used: stored or documented effect-size definition |
| dat.gibson2002 | 4 | used: stored or documented effect-size definition |
| dat.graves2010 | 1 | used: stored or documented effect-size definition |
| dat.greb2008 | 2 | used: stored or documented effect-size definition |
| dat.greenland1992 | 1 | used: stored or documented effect-size definition |
| dat.gurusamy2011 | 1 | used: stored or documented effect-size definition |
| dat.hackshaw1998 | 1 | used: stored or documented effect-size definition |
| dat.hahn2001 | 2 | used: stored or documented effect-size definition |
| dat.hannum2020 | 3 | used: stored or documented effect-size definition |
| dat.hart1999 | 2 | used: stored or documented effect-size definition |
| dat.hartmannboyce2018 | 1 | used: stored or documented effect-size definition |
| dat.hasselblad1998 | 2 | used: stored or documented effect-size definition |
| dat.higgins2008 | 2 | used: stored or documented effect-size definition |
| dat.hine1989 | 2 | used: stored or documented effect-size definition |
| dat.huber2000 | 1 | used: stored or documented effect-size definition |
| dat.ishak2007 | 4 | used: stored or documented effect-size definition |
| dat.kalaian1996 | 1 | used: stored or documented effect-size definition |
| dat.karner2014 | 8 | used: stored or documented effect-size definition |
| dat.kearon1998 | 4 | used: stored or documented effect-size definition |
| dat.knapp2017 | 1 | used: stored or documented effect-size definition |
| dat.konstantopoulos2011 | 1 | used: stored or documented effect-size definition |
| dat.landenberger2005 | 1 | used: stored or documented effect-size definition |
| dat.laopaiboon2015 | 1 | used: stored or documented effect-size definition |
| dat.lau1992 | 2 | used: stored or documented effect-size definition |
| dat.lee2004 | 1 | used: stored or documented effect-size definition |
| dat.lehmann2018 | 3 | used: stored or documented effect-size definition |
| dat.li2007 | 2 | used: stored or documented effect-size definition |
| dat.lim2014 | 1 | used: stored or documented effect-size definition |
| dat.linde2005 | 2 | used: stored or documented effect-size definition |
| dat.linde2015 | 2 | used: stored or documented effect-size definition |
| dat.linde2016 | 1 | used: stored or documented effect-size definition |
| dat.lloyd2010 | 4 | used: stored or documented effect-size definition |
| dat.lopez2019 | 1 | used: stored or documented effect-size definition |
| dat.maire2019 | 1 | used: stored or documented effect-size definition |
| dat.mccurdy2020 | 1 | used: stored or documented effect-size definition |
| dat.mcdaniel1994 | 2 | used: stored or documented effect-size definition |
| dat.meeker2017 | 1 | used: stored or documented effect-size definition |
| dat.metap | 0 | excluded: p-value collections; no effect sizes with sampling variances or raw outcome summaries for escalc |
| dat.michael2013 | 2 | used: stored or documented effect-size definition |
| dat.molloy2014 | 1 | used: stored or documented effect-size definition |
| dat.moore1998 | 2 | used: stored or documented effect-size definition |
| dat.moura2021 | 1 | used: stored or documented effect-size definition |
| dat.nakagawa2007 | 1 | used: stored or documented effect-size definition |
| dat.nielweise2007 | 2 | used: stored or documented effect-size definition |
| dat.nielweise2008 | 1 | used: stored or documented effect-size definition |
| dat.nissen2007 | 6 | used: stored or documented effect-size definition |
| dat.normand1999 | 2 | used: stored or documented effect-size definition |
| dat.obrien2003 | 2 | used: stored or documented effect-size definition |
| dat.pagliaro1992 | 2 | used: stored or documented effect-size definition |
| dat.pignon2000 | 1 | used: stored or documented effect-size definition |
| dat.poole2003 | 2 | used: stored or documented effect-size definition |
| dat.pritz1997 | 4 | used: stored or documented effect-size definition |
| dat.quan2000 | 2 | used: stored or documented effect-size definition |
| dat.raudenbush1985 | 1 | used: stored or documented effect-size definition |
| dat.riley2003 | 1 | used: stored or documented effect-size definition |
| dat.rivera2025 | 5 | used: stored or documented effect-size definition |
| dat.roever2022 | 1 | used: stored or documented effect-size definition |
| dat.senn2013 | 2 | used: stored or documented effect-size definition |
| dat.spooner2002 | 2 | used: stored or documented effect-size definition |
| dat.steurer2006 | 2 | used: stored or documented effect-size definition |
| dat.stowe2010 | 1 | used: stored or documented effect-size definition |
| dat.tannersmith2016 | 1 | used: stored or documented effect-size definition |
| dat.thompson1999 | 2 | used: stored or documented effect-size definition |
| dat.tian2009 | 3 | used: stored or documented effect-size definition |
| dat.ursino2021 | 1 | used: stored or documented effect-size definition |
| dat.vanhowe1999 | 1 | used: stored or documented effect-size definition |
| dat.viechtbauer2021 | 1 | used: stored or documented effect-size definition |
| dat.white2020 | 1 | used: stored or documented effect-size definition |
| dat.woods2010 | 1 | used: stored or documented effect-size definition |
| dat.yusuf1985 | 2 | used: stored or documented effect-size definition |

## Source locations
| Item | Original file:line |
|---|---|
| singleton_omission | gosh/index.html:203 |
| sampling_claim | gosh/index.html:159 |
| sampling_hint | gosh/index.html:116 |
| stale_refusal | gosh/index.html:257 |
| x_override | gosh/index.html:347 |
| sampler | gosh/index.html:211 |
| enumeration | gosh/index.html:196 |
| pool | gosh/index.html:176 |
| export | gosh/index.html:307 |

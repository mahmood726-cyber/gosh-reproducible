# Recorded runs of the GOSH replay counts (30 Oct 2026)

`run.cmd` cloned github.com/mahmood726-cyber/allmeta and, at each ref, ran in `hub/shared/tests`:
`npx playwright test validate-gosh.spec.mjs gosh-plus.spec.mjs -g "declared replay preserves|every quantity against pinned R corpus" --workers=1 --reporter=list,json`
(Windows, Node v24.13.0, @playwright/test 1.59.1, bundled Chromium; page served on 127.0.0.1:8088, the only host requested).

| ref | allmeta commit | offline replay | extras replay | Playwright |
|---|---|---|---|---|
| v1.7.0 | 15c0fa055c8cc79f7dac2d7e7ec8bfe43942a0e8 | 876760/876760 | 1153536/1153536 | 2 expected, 0 unexpected |
| 63ce78e5 | 63ce78e58c0f645099faa7dd3d5498a3ab9efb15 | 876760/876760 | 1153536/1153536 | 2 expected, 0 unexpected |

Each test asserts that the count equals the pinned manifest (gosh/validate/MANIFEST.json, MANIFEST-plus.json; SHA-256 in env.txt,
identical at both refs), that every check passed and that no check failed. `verify.py` re-reads results.json and requires these values.

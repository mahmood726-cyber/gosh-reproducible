# 1.1.1
Add v1_1/runs/2026-10-30: recorded browser runs of the paper's two replay counts at allmeta v1.7.0 (commit 15c0fa0) and at
commit 63ce78e5: offline replay 876760/876760 and extras replay 1153536/1153536 at both refs, with the run script, Playwright
JSON results, logs and request logs. verify.py now re-reads these records and fails unless both counts passed in full. No
scientific content, reference or earlier record changes.

# 1.1.0
Add the separately pinned v1_1/exact all-subsets tier, saved independent R and
forced-metafor references, offline replay, historical timing data and planted
defects. Preserve all v1.0 scientific content and original inventories; retain
the four superseded metadata files byte-for-byte in v1_1/legacy-metadata.
The allmeta release identifiers are filled: v1.8.0 (tag commit 1cb3f84, DOI
10.5281/zenodo.23515177), which contains pull request #167 (commit 1e3ef38).
RELEASE_EQUIVALENCE.md records that the 21 layer files match their v1.8.0 blobs and
that re-running the replays gives EXACT R 345842/345842, EXACT METAFOR
182826/182826 and the unchanged legacy 12813556/12813556. The verifier now
requires the filled values and the equivalence record instead of the tokens, and
v1_1/SOURCE_SHA256.json is re-pinned.

# 1.0.0
Initial GOSH validation archive; FE/DL, full captured memberships and independent R reference.

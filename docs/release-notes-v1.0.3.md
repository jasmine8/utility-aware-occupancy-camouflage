# Release notes — v1.0.3

**Tag:** `v1.0.3` · **Date:** 2026-10-16 · **DOI (all versions):** [10.5281/zenodo.23320735](https://doi.org/10.5281/zenodo.23320735)

## Added

- **`reproducibility/`** — the journal-independent occupancy-entropy reproduction
  package, previously distributed only as a side ZIP alongside the manuscript
  submission. This closes the gap noted in the submission checklist: the
  manuscript's data-availability statement says *all derived figures and tables*
  are in the repository, and the entropy artifacts were the missing piece.
  - `reproduce_entropy.py` — recomputes binary occupancy entropy of the marginal
    voxel-occupancy proportion for the same fixed 16-frame KITTI subset, using the
    same voxelization and deterministic low-utility removal rule as
    `experiments/main/run_utility_aware_pilot.py` (projection-count equivalence; no
    90,112,000-cell dense grid allocation)
  - `results/entropy_analysis.csv` — 160 rows (16 frames × 10 budgets, incl. the
    `budget = 0` no-removal baseline)
  - `results/entropy_analysis.json` — structured payload with metadata, summary and
    per-frame rows; `map` stays `null` with
    `map_status = "unavailable_without_verifiable_checkpoint"`
  - `results/entropy_summary.csv` — per-budget mean and sample SD
  - `results/entropy_budget.pdf` / `.png` — the budget-vs-entropy figure included
    in the manuscript
- Repository documentation extended to cover the package: repository layout and a
  verification recipe in `README.md` (§3.6), a released-artifacts row in
  `DATA_AVAILABILITY.md`, and run instructions in `docs/REPRODUCE.md` (§3.4).

## Verified

- End-to-end on the committed tree: the 16 frames restored from
  `data/kitti_velodyne_subset_manifest.json` via range requests, then
  `reproduce_entropy.py --compare-csv reproducibility/results/entropy_analysis.csv`
  → **`Comparison mismatches: 0`** (integers exact, floats `rtol=1e-10`).

## Changed

- `CITATION.cff`: `version` 1.0.2 → 1.0.3, release date 2026-10-16, abstract extended
  to mention the entropy package. `doi` remains the concept DOI.
- `README.md` made fully version-agnostic (no "current release" wording in the
  repository body — see `docs/REPRODUCE.md` §6 for the rationale).

## Unchanged

- Every numerical artifact of v1.0.2 is byte-identical here; nothing in
  `experiments/` or `paper/` was touched.
- KITTI frames are still **not** redistributed (manifest + fetch script only).
- No detector checkpoint and no mAP are reported.

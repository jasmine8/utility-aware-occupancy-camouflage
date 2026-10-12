# Release notes — v1.0.2

**Tag:** `v1.0.2` · **Date:** 2026-10-12 · **DOI (all versions):** [10.5281/zenodo.23320735](https://doi.org/10.5281/zenodo.23320735)

This is a metadata-only release. **No numerical result, figure, table, or script
changes** — every artifact is byte-identical to `v1.0.1`. It exists because a
published Zenodo snapshot is immutable, so two defects in the `v1.0.1` archive could
not be repaired in place.

## Fixed

- **`CITATION.cff` author affiliation was the placeholder `"TODO"`.** It now reads
  `Mingzhen Li — School of Software, Henan University of Engineering, Zhengzhou
  451191, China`. The placeholder had propagated into the public Zenodo record
  metadata; the record is corrected as well.
- **`CITATION.cff` `doi` was unset and the DOI backfill landed after the `v1.0.1`
  tag**, so the `v1.0.1` archive contained no resolvable DOI. The field now carries
  the *concept* DOI `10.5281/zenodo.23320735`, which always resolves to the newest
  archived version — a version-specific DOI cannot be written into its own snapshot,
  because Zenodo only mints it after ingestion.
- `README.md`, `DATA_AVAILABILITY.md`, and `docs/REPRODUCE.md` were aligned with the
  above, and the release-hygiene note in `docs/REPRODUCE.md` §6 now records both
  lessons: never tag two releases on one commit, and never publish with a `TODO` in
  `CITATION.cff`.

## Known cosmetic residue

`v1.0.0` and `v1.0.1` were both tagged on commit `dcfe54c`, so those two archives are
byte-identical *and* still contain the `TODO` placeholder inside their copy of
`CITATION.cff`. Both remain reachable and citable; `v1.0.2` is the first
self-consistent snapshot and is the recommended citation target.

## Unchanged, for the record

- Code: MIT · Data and derived artifacts: CC BY 4.0
- 9 removal budgets × 16 KITTI Velodyne frames, per-frame results unchanged
- KITTI frames are **not** redistributed; `data/kitti_velodyne_subset_manifest.json`
  plus `experiments/main/fetch_kitti_subset_from_manifest.py` restore the exact 16-frame
  subset over HTTP Range requests
- No detector checkpoint and no mAP are reported (no verifiable official Voxel R-CNN
  checkpoint); `experiments/main/artifacts/checkpoint_route_audit.json` records that search

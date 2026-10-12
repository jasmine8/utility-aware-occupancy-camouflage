# Utility-Aware Occupancy Camouflage for Point Cloud Privacy — Pilot Release

Code, per-frame numerical results, and figure/table artifacts for the scoped pilot study:

> **Utility-Aware Occupancy Camouflage for Point Cloud Privacy: A Scoped Pilot Study**
> *(manuscript under review; citation will be updated with the DOI on acceptance)*

This repository is the artifact bundle referenced by the manuscript's data-and-code
availability statement. It contains the **full 9-budget × 16-frame numerical results**
and the **reconstruction code**, plus every figure and table derived from them.

**Archived release:** v1.0.1 — https://doi.org/10.5281/zenodo.23320736
(concept DOI, always the latest version: https://doi.org/10.5281/zenodo.23320735)

---

## 1. What the pilot shows

Autonomous-driving stacks often exchange compact voxel features instead of raw point
clouds, on the assumption that compression is itself a privacy safeguard. This pilot
tests the opposite direction: it asks whether a sender can *selectively remove a small
fraction of occupancy evidence* so that a concrete occupancy-based reconstruction path
becomes measurably worse, while most of the scene remains available to perception.

**Method (utility-aware occupancy camouflage, UOC).** Occupied voxels are ranked by a
deterministic three-axis density-support proxy — no detector gradients, no semantic
labels, no learned utility model. The lowest-utility fraction is removed before
occupancy-based reconstruction.

**Setup.** A fixed 16-frame KITTI Velodyne subset; nine removal budgets
`{0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75}`; metrics averaged over all
16 frames. The *selected operating point* is the smallest tested budget whose mean
Chamfer-Distance degradation reaches at least 3×.

### Headline result

| Method | CD (cm) | CD ratio | HD (cm) | HD ratio | F1@15cm | F1 drop |
|---|---:|---:|---:|---:|---:|---:|
| Unmasked occupancy (baseline) | 3.2683 | 1.0000 | 6.0618 | 1.0000 | 1.0000 | 0.0000 |
| **UOC, 25 % removal (selected)** | **12.0130** | **3.6756** | **1982.9039** | **327.1165** | **0.9318** | **0.0682** |

The full budget sweep is monotonic in privacy degradation while reconstruction F1
degrades gradually — see [`paper/tables/removal_budget_sensitivity.md`](paper/tables/removal_budget_sensitivity.md).

### Scope boundary (read this before citing a number)

The pilot supports **privacy degradation only**. It does **not** claim task-utility
preservation: downstream 3D detection mAP was **not** evaluated, because the official
Voxel R-CNN checkpoint was not available from a verifiable source. The audit of that
search is preserved verbatim in
[`experiments/main/artifacts/checkpoint_route_audit.json`](experiments/main/artifacts/checkpoint_route_audit.json),
and every result file carries `map_status = "unavailable_without_verifiable_checkpoint"`.
Do not read these numbers as a privacy–utility tradeoff curve; they are a
privacy-degradation measurement under a fixed, non-adaptive reconstruction path.

---

## 2. Repository layout

```
.
├── data/
│   ├── kitti_velodyne_subset_manifest.json   # exact byte ranges of the 16 frames in the public archive
│   └── kitti_ImageSets_val.txt               # KITTI devkit val split (used to select the first 16 frames)
├── experiments/main/
│   ├── run_utility_aware_pilot.py            # UOC defense + reconstruction metrics  (core)
│   ├── run_occupancy_pilot.py                # baseline + random-jitter comparison    (core)
│   ├── fetch_kitti_subset_from_manifest.py    # restore the 16 frames via HTTP range requests
│   ├── download_kitti_subset.py              # original subset downloader (central-directory route)
│   ├── smoke_voxel_backbone.py               # optional OpenPCDet VoxelBackbone smoke test
│   ├── pcdet_import.py                       # loader shim for the OpenPCDet backbone
│   ├── configs/                              # official OpenPCDet KITTI / Voxel R-CNN configs
│   ├── artifacts/checkpoint_route_audit.json # audited search for a verifiable checkpoint
│   └── results/
│       ├── removal_rate_sweep/               # ← the nine canonical budget runs
│       │   ├── rate_0.05.json … rate_0.75.json
│       │   └── summary.json                  # operating-point selection + all rows
│       ├── utility_aware_budget_sweep.json   # complementary finer sweep over {0.01 … 0.25}
│       ├── utility_aware_pilot.json          # per-frame UOC result (rate 0.75 default)
│       ├── occupancy_pilot.json              # per-frame reconstruction baseline
│       ├── occupancy_rate_sweep.json         # random-jitter perturbation sweep {0.0 … 0.8}
│       └── voxel_smoke.json                  # backbone audit evidence
└── paper/
    ├── figures/                              # all figures (PDF + PNG) and the generator script
    ├── analysis/                             # per-figure data (JSON) consumed by the generators
    ├── tables/                               # main + budget-sensitivity tables (Markdown)
    ├── appendix/reproducibility.md           # protocol and scope boundary
    └── scripts/                              # manuscript-side derivation scripts (provenance)
```

The `experiments/main/**` and `paper/**` prefixes mirror the original research
workspace, so every command in the manuscript's reproducibility appendix runs
verbatim from the repository root.

---

## 3. Reproduce the released numbers

### 3.1 Environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Only `numpy` and `scipy` are needed to reproduce the numbers. `matplotlib` is used
solely to regenerate figures.

### 3.2 Restore the fixed 16-frame KITTI Velodyne subset

The manifest records the exact byte range of each frame inside the public KITTI
archive, so the subset can be restored with range requests — no full 12 GB download,
no central-directory dump:

```bash
python experiments/main/fetch_kitti_subset_from_manifest.py \
  --manifest data/kitti_velodyne_subset_manifest.json \
  --output   experiments/main/data/kitti/training/velodyne
```

Each frame is verified against its recorded `expected_size`; the script prints a
per-frame MD5. The frames land in `experiments/main/data/kitti/training/velodyne/`,
which is the default `--data-dir` of both pilot scripts.

> **Why the frames are not committed.** KITTI is distributed under its own
> non-commercial terms of use. This repository ships the *manifest* (offsets and
> sizes) and the fetch script instead of the raw frames.

### 3.3 Re-run the pilot and the 9-budget sweep

```bash
# baseline reconstruction (occupancy, no defense)
python experiments/main/run_occupancy_pilot.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output   experiments/main/results/occupancy_pilot.json \
  --perturb-rate 0.2 --seed 20261003

# the nine canonical budgets -> the released result files
for r in 0.05 0.10 0.15 0.20 0.25 0.30 0.40 0.50 0.75; do
  python experiments/main/run_utility_aware_pilot.py \
    --data-dir experiments/main/data/kitti/training/velodyne \
    --output   experiments/main/results/removal_rate_sweep/rate_$r.json \
    --removal-rate $r
done
```

The runs are fully deterministic (fixed 16-frame subset, no random seed in the
defense path), so the regenerated `rate_*.json` files reproduce the committed ones
value for value.

### 3.4 Regenerate the figures

```bash
python paper/figures/scripts/gen_all_figures.py
```

### 3.5 Protocol summary

| Item | Value |
|---|---|
| Frames | 16, fixed (first 16 entries of the KITTI val split) |
| Point-cloud range | `[0, −40, −3, 70.4, 40, 1]` m |
| Voxel size | `(0.05, 0.05, 0.10)` m |
| Utility proxy | sum of three axis-projection occupancy counts |
| Budgets tested | 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75 |
| CD / HD | symmetric nearest-neighbour distance, in cm |
| F1@15cm | 15 cm nearest-neighbour threshold |
| Operating-point rule | smallest tested budget with mean CD degradation ≥ 3× |
| Detection mAP | not evaluated (no verifiable checkpoint) |

---

## 4. License

- **Code** (`*.py`, configs, scripts): [MIT](LICENSE).
- **Data and derived artifacts** (result JSON, figures, tables, manifests):
  [CC BY 4.0](LICENSE-DATA).

Third-party components are not redistributed. The OpenPCDet source tree and the KITTI
dataset are referenced by URL only; see [`docs/REPRODUCE.md`](docs/REPRODUCE.md) for
their own licenses.

## 5. Citation

Author: **Mingzhen Li**, School of Software, Henan University of Engineering, Zhengzhou
451191, China. Machine-readable metadata is in [`CITATION.cff`](CITATION.cff).

To cite the released artifacts, use DOI **10.5281/zenodo.23320735**, which always
resolves to the newest archived version (currently **v1.0.2**). A version-specific DOI
is minted for each release — e.g. `10.5281/zenodo.23320736` for v1.0.1. The manuscript
is under review; its journal DOI will be added on acceptance.

## 6. Data availability

A ready-to-paste statement is provided in
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md).

# UOC Reproducibility Package — Occupancy Entropy Experiment

Journal-independent reproduction package for the occupancy-entropy experiment of the
UOC (Utility-Aware Occupancy Camouflage) pilot study. Nothing in this package depends
on the venue of the accompanying manuscript; it can be cited and reused regardless of
where the paper is published.

## Basis and format

Recomputes occupancy entropy from the fixed 16-frame KITTI Velodyne subset, using the
same voxelization and deterministic low-utility occupancy removal rule as
`experiments/main/run_utility_aware_pilot.py`. The frames themselves are **not**
committed anywhere (KITTI non-commercial terms); in this repository they are restored
from the byte-range manifest (see below), and in the standalone submission ZIP they
ship in the reviewer's `main.zip` — the code accepts either location via `--data-dir`.

- `results/entropy_analysis.csv`: **same 9 columns, same order and 160 rows** as the original entropy analysis CSV in the paper project.
- `results/entropy_analysis.json`: original pilot-like structured JSON, with metadata, summary and per-frame results.
- `results/entropy_summary.csv`: 10-row mean and sample standard deviation by removal budget.
- `results/entropy_budget.pdf`, `.png`: publication-ready plot of budget versus mean marginal binary occupancy entropy (with frame-wise SD error bars). This is the figure included in the manuscript (`figures/entropy_budget.pdf`).

File and folder names refer to the measured quantity (occupancy entropy, in bits) and are independent of any journal or submission.

## Reproduction

**In this repository** — restore the 16 frames from the manifest first, then run:

```bash
python experiments/main/fetch_kitti_subset_from_manifest.py \
  --manifest data/kitti_velodyne_subset_manifest.json \
  --output   experiments/main/data/kitti/training/velodyne

python reproducibility/reproduce_entropy.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output-dir /tmp/entropy_check \
  --compare-csv reproducibility/results/entropy_analysis.csv
```

`--compare-csv` is optional; with it the script asserts row-by-row equality against
the released CSV (integers exact, floats `rtol=1e-10`) and prints the mismatch count,
which must be `0`.

**From the standalone submission ZIP** (16 frames supplied in the extracted
`main.zip`):

```bash
python reproduce_entropy.py \
  --data-dir main/data/kitti/training/velodyne \
  --output-dir results \
  --compare-csv path/to/original_entropy_analysis.csv
```

Requirements: `numpy`, `matplotlib` (optional for figure). This code uses projection-count equivalence instead of allocating the original 90,112,000-cell dense grid; counts and removal choices are identical.

## Important evidence limits

- The entropy is binary entropy of the **marginal voxel occupancy proportion**, NOT spatial joint entropy or mutual information with a sensitive variable.
- `budget=0` is the explicit no-removal baseline; positive budgets use `score <= np.quantile(score, budget)` and therefore actual removal can exceed the nominal budget when scores tie.
- The figure and tables report actual data from the supplied 16 frames, not a new dataset or a privacy guarantee.
- The original pilot does not provide a verified detector checkpoint; no mAP is reported or inferred.
- KITTI point-cloud files are **not redistributed** in this package. Restore them via the repository manifest (above) or reuse the 16 `.bin` files already in `main.zip`.

# Checkpoint-Free Occupancy Pilot

This directory contains the smallest auditable reconstruction pilot that can run without the unavailable official Voxel R-CNN checkpoint.

## Scope

- Reconstructs point clouds from occupied voxel centers on the fixed 16-frame KITTI Velodyne subset.
- Applies a deterministic random occupancy-jitter defense at perturbation rate 0.2.
- Reports CD, HD, and F1@15cm.
- Does **not** report mAP: the accepted baseline contract requires mAP, and the official Voxel R-CNN checkpoint is unavailable from a verifiable source.

## Reproduce

```bash
python experiments/main/run_occupancy_pilot.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output experiments/main/results/occupancy_pilot.json \
  --perturb-rate 0.2 \
  --seed 20261003
```

A deterministic rate sweep is also available:

```bash
python experiments/main/run_occupancy_pilot.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output experiments/main/results/occupancy_rate_sweep.json \
  --rate 0.0 --rate 0.2 --rate 0.4 --rate 0.6 --rate 0.8 \
  --seed 20261003
```

A deterministic utility-aware pilot removes the lowest-utility quartile of occupied voxels:

```bash
python experiments/main/run_utility_aware_pilot.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output experiments/main/results/utility_aware_pilot.json
```

## Key outputs

- `experiments/main/results/occupancy_pilot.json`: 16-frame reconstruction metrics with explicit `map_status=unavailable_without_verifiable_checkpoint`.
- `experiments/main/results/occupancy_rate_sweep.json`: deterministic perturbation-rate sensitivity sweep over `{0.0, 0.2, 0.4, 0.6, 0.8}`.
- `experiments/main/results/utility_aware_pilot.json`: 16-frame deterministic low-utility occupancy-removal result; `map` remains explicitly unavailable.
- `experiments/main/artifacts/checkpoint_route_audit.json`: audited checkpoint source search.
- `experiments/main/configs/voxel_rcnn_car_official.yaml`: official OpenPCDet Voxel R-CNN configuration.
- `experiments/main/configs/kitti_dataset_official.yaml`: official OpenPCDet KITTI dataset configuration.

## Evidence boundary

The 16-frame result is a scope-restricted reconstruction pilot, not the complete main experiment. The complete experiment remains blocked until a byte-identical, verifiable official Voxel R-CNN checkpoint is available.

## Restore the frame subset

```bash
python experiments/main/fetch_kitti_subset_from_manifest.py \
  --manifest data/kitti_velodyne_subset_manifest.json \
  --output   experiments/main/data/kitti/training/velodyne
```

This uses the byte ranges recorded in the release manifest, so no full-archive
download and no central-directory dump are required. The original
`download_kitti_subset.py` route (central directory + `val.txt`) is documented in
`docs/REPRODUCE.md`, §2.

## Reproduce the nine-budget sweep

The released `results/removal_rate_sweep/` files are produced by running the
utility-aware pilot once per tested budget:

```bash
for r in 0.05 0.10 0.15 0.20 0.25 0.30 0.40 0.50 0.75; do
  python experiments/main/run_utility_aware_pilot.py \
    --data-dir experiments/main/data/kitti/training/velodyne \
    --output   experiments/main/results/removal_rate_sweep/rate_$r.json \
    --removal-rate $r
done
```

`results/utility_aware_budget_sweep.json` is a complementary finer sweep over
`{0.01 … 0.25}` kept for the low-budget regime.

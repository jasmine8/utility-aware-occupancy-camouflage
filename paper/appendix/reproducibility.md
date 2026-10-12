# Reproducibility Appendix

## Assets

- Fixed 16-frame KITTI Velodyne subset: `experiments/main/data/kitti/training/velodyne`
- Budget sweep summary: `experiments/main/results/removal_rate_sweep/summary.json`
- Selected 0.25 operating point: `experiments/main/results/removal_rate_sweep/rate_0.25.json`
- Defense implementation: `experiments/main/run_utility_aware_pilot.py`
- Detector-checkpoint audit: `experiments/main/artifacts/checkpoint_route_audit.json`
- Figure data: `paper/analysis/figure_removal_budget_tradeoff.json`

## Protocol

- Occupancy is computed with a voxel size of 0.05 m along x and y and 0.10 m along z.
- Occupied voxels are ranked by a deterministic three-axis density-support proxy.
- For each tested removal budget, the lowest-utility fraction is removed before occupancy reconstruction.
- The selected operating point is the smallest tested rate whose CD degradation is at least 3x on the fixed subset.
- CD and HD are reported in centimeters; F1@15cm uses a 15 cm nearest-neighbor threshold.
- All table values are means over the fixed 16 frames.
- Downstream mAP is not computed; the checkpoint audit records why it is unavailable.

## Scope boundary

The reproduction instructions describe the pilot only. They do not establish robustness to trained attackers or downstream detection utility.

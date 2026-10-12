#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

POINT_CLOUD_RANGE = np.array([0.0, -40.0, -3.0, 70.4, 40.0, 1.0], dtype=np.float32)
VOXEL_SIZE = np.array([0.05, 0.05, 0.1], dtype=np.float32)
GRID_SIZE = np.ceil((POINT_CLOUD_RANGE[3:] - POINT_CLOUD_RANGE[:3]) / VOXEL_SIZE).astype(np.int32)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("experiments/main/data/kitti/training/velodyne"))
    parser.add_argument("--output", type=Path, default=Path("experiments/main/results/utility_aware_pilot.json"))
    parser.add_argument("--removal-rate", type=float, default=0.75)
    return parser.parse_args()


def in_range_points(points):
    return points[
        (points[:, 0] >= POINT_CLOUD_RANGE[0])
        & (points[:, 0] < POINT_CLOUD_RANGE[3])
        & (points[:, 1] >= POINT_CLOUD_RANGE[1])
        & (points[:, 1] < POINT_CLOUD_RANGE[4])
        & (points[:, 2] >= POINT_CLOUD_RANGE[2])
        & (points[:, 2] < POINT_CLOUD_RANGE[5])
    ]


def occupied_voxels(points):
    coordinates = np.floor((points[:, :3] - POINT_CLOUD_RANGE[:3]) / VOXEL_SIZE).astype(np.int32)
    return np.unique(coordinates, axis=0)


def voxel_centers(voxels):
    return voxels.astype(np.float32) * VOXEL_SIZE + POINT_CLOUD_RANGE[:3] + VOXEL_SIZE / 2


def nearest_distances(source, target):
    if len(source) == 0 or len(target) == 0:
        return np.array([], dtype=np.float32)
    return cKDTree(target).query(source, k=1)[0]


def reconstruction_metrics(ground_truth, reconstruction):
    gt_to_rec = nearest_distances(ground_truth, reconstruction)
    rec_to_gt = nearest_distances(reconstruction, ground_truth)
    threshold = 0.15
    precision = float(np.mean(rec_to_gt <= threshold)) if len(rec_to_gt) else 0.0
    recall = float(np.mean(gt_to_rec <= threshold)) if len(gt_to_rec) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "cd_cm": float((np.mean(gt_to_rec) + np.mean(rec_to_gt)) / 2 * 100),
        "hd_cm": float(max(np.max(gt_to_rec), np.max(rec_to_gt)) * 100),
        "f1_15cm": float(f1),
        "precision_15cm": precision,
        "recall_15cm": recall,
    }


def remove_voxels(voxels, removed):
    if len(removed) == 0:
        return voxels.copy()
    removed_view = np.ascontiguousarray(removed).view([("", np.int32)] * 3).ravel()
    voxels_view = np.ascontiguousarray(voxels).view([("", np.int32)] * 3).ravel()
    return voxels[~np.isin(voxels_view, removed_view)]


def utility_aware_defense(points, voxels, removal_rate):
    grid = np.zeros(tuple(GRID_SIZE), dtype=np.int32)
    flat_indices = np.ravel_multi_index(voxels.T, GRID_SIZE)
    np.add.at(grid.ravel(), flat_indices, 1)
    occupied = grid > 0
    yz_counts = occupied.sum(axis=0)
    xz_counts = occupied.sum(axis=1)
    xy_counts = occupied.sum(axis=2)

    utility = (
        yz_counts[voxels[:, 1], voxels[:, 2]]
        + xz_counts[voxels[:, 0], voxels[:, 2]]
        + xy_counts[voxels[:, 0], voxels[:, 1]]
    )
    threshold = np.quantile(utility, removal_rate)
    removed = voxels[utility <= threshold]
    return remove_voxels(voxels, removed), utility, threshold


def run(args):
    frame_results = []
    for input_path in sorted(args.data_dir.glob("*.bin")):
        points = in_range_points(np.fromfile(input_path, dtype=np.float32).reshape(-1, 4))
        voxels = occupied_voxels(points)
        baseline_reconstruction = voxel_centers(voxels)
        defended_voxels, utility, threshold = utility_aware_defense(points, voxels, args.removal_rate)
        defended_reconstruction = voxel_centers(defended_voxels)
        frame_results.append(
            {
                "frame": input_path.name,
                "points": int(len(points)),
                "occupied_voxels": int(len(voxels)),
                "defended_occupied_voxels": int(len(defended_voxels)),
                "removed_voxels": int(len(voxels) - len(defended_voxels)),
                "utility_threshold": float(threshold),
                "baseline": reconstruction_metrics(points[:, :3], baseline_reconstruction),
                "defense": reconstruction_metrics(points[:, :3], defended_reconstruction),
            }
        )
    baseline_summary = {metric: float(np.mean([frame["baseline"][metric] for frame in frame_results])) for metric in frame_results[0]["baseline"]}
    defense_summary = {metric: float(np.mean([frame["defense"][metric] for frame in frame_results])) for metric in frame_results[0]["defense"]}
    result = {
        "run_id": "run-uoc-pilot-002",
        "method": "voxel-occupancy-reconstruction",
        "defense_variant": "deterministic-low-utility-occupancy-removal",
        "removal_rate": args.removal_rate,
        "frame_count": len(frame_results),
        "baseline_summary": baseline_summary,
        "defense_summary": defense_summary,
        "privacy_degradation_ratio_cd": defense_summary["cd_cm"] / baseline_summary["cd_cm"],
        "privacy_degradation_ratio_hd": defense_summary["hd_cm"] / baseline_summary["hd_cm"],
        "f1_drop": baseline_summary["f1_15cm"] - defense_summary["f1_15cm"],
        "map": None,
        "map_status": "unavailable_without_verifiable_checkpoint",
        "map_reason": "The official Voxel R-CNN checkpoint is not available from a verifiable source; mAP is not inferred.",
        "frames": frame_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["run_id", "frame_count", "removal_rate", "baseline_summary", "defense_summary", "privacy_degradation_ratio_cd", "privacy_degradation_ratio_hd", "f1_drop", "map_status"]}, indent=2))


if __name__ == "__main__":
    run(parse_args())

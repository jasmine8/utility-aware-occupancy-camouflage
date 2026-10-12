#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


POINT_CLOUD_RANGE = np.array([0.0, -40.0, -3.0, 70.4, 40.0, 1.0], dtype=np.float32)
VOXEL_SIZE = np.array([0.05, 0.05, 0.1], dtype=np.float32)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("experiments/main/data/kitti/training/velodyne"))
    parser.add_argument("--output", type=Path, default=Path("experiments/main/results/occupancy_pilot.json"))
    parser.add_argument("--perturb-rate", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20261003)
    parser.add_argument("--rate", type=float, action="append", help="Override the single-rate run and execute a deterministic rate sweep; repeatable.")
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


def perturb_occupancy(voxels, perturb_rate, rng):
    grid_size = np.ceil((POINT_CLOUD_RANGE[3:] - POINT_CLOUD_RANGE[:3]) / VOXEL_SIZE).astype(np.int32)
    keep = rng.random(len(voxels)) >= perturb_rate
    unchanged = voxels[keep]
    perturbed = voxels[~keep].copy()
    offsets = rng.integers(-1, 2, size=(len(perturbed), 3), dtype=np.int32)
    perturbed += offsets
    perturbed = np.clip(perturbed, 0, grid_size - 1)
    return np.unique(np.concatenate([unchanged, perturbed], axis=0), axis=0)


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
        "cd_cm": float((np.mean(gt_to_rec) + np.mean(rec_to_gt)) / 2 * 100) if len(gt_to_rec) and len(rec_to_gt) else None,
        "hd_cm": float(max(np.max(gt_to_rec), np.max(rec_to_gt)) * 100) if len(gt_to_rec) and len(rec_to_gt) else None,
        "f1_15cm": float(f1),
        "precision_15cm": precision,
        "recall_15cm": recall,
    }


def mean_metrics(frames, key):
    values = [frame[key] for frame in frames]
    return {
        metric: float(np.mean([value[metric] for value in values]))
        for metric in values[0]
    }


def run_single_rate(rate, args):
    rng = np.random.default_rng(args.seed + int(rate * 100000))
    frame_results = []
    for input_path in sorted(args.data_dir.glob("*.bin")):
        points = np.fromfile(input_path, dtype=np.float32).reshape(-1, 4)
        points = in_range_points(points)
        voxels = occupied_voxels(points)
        baseline_reconstruction = voxel_centers(voxels)
        perturbed_voxels = perturb_occupancy(voxels, rate, rng)
        defended_reconstruction = voxel_centers(perturbed_voxels)
        baseline_metrics = reconstruction_metrics(points[:, :3], baseline_reconstruction)
        defense_metrics = reconstruction_metrics(points[:, :3], defended_reconstruction)
        frame_results.append(
            {
                "frame": input_path.name,
                "points": int(len(points)),
                "occupied_voxels": int(len(voxels)),
                "perturbed_occupied_voxels": int(len(perturbed_voxels)),
                "baseline": baseline_metrics,
                "defense": defense_metrics,
            }
        )
    baseline_summary = mean_metrics(frame_results, "baseline")
    defense_summary = mean_metrics(frame_results, "defense")
    result = {
        "run_id": "run-uoc-pilot-001",
        "method": "voxel-occupancy-reconstruction",
        "defense_variant": "random-occupancy-jitter",
        "perturb_rate": rate,
        "seed": args.seed,
        "frame_count": len(frame_results),
        "metric_definition": {
            "cd_cm": "Mean symmetric nearest-neighbor Euclidean distance in centimeters.",
            "hd_cm": "Maximum symmetric nearest-neighbor Euclidean distance in centimeters.",
            "f1_15cm": "Point-set F1 at a 15-centimeter nearest-neighbor threshold.",
        },
        "baseline_summary": baseline_summary,
        "defense_summary": defense_summary,
        "privacy_degradation_ratio_cd": defense_summary["cd_cm"] / baseline_summary["cd_cm"] if baseline_summary["cd_cm"] else None,
        "privacy_degradation_ratio_hd": defense_summary["hd_cm"] / baseline_summary["hd_cm"] if baseline_summary["hd_cm"] else None,
        "f1_drop": baseline_summary["f1_15cm"] - defense_summary["f1_15cm"],
        "map": None,
        "map_status": "unavailable_without_verifiable_checkpoint",
        "map_reason": "The official Voxel R-CNN checkpoint is not yet available from a verifiable source; mAP is not inferred.",
        "frames": frame_results,
    }
    return result


def main():
    args = parse_args()
    rates = args.rate if args.rate else [args.perturb_rate]
    results = [run_single_rate(rate, args) for rate in rates]
    if len(results) == 1:
        result = results[0]
    else:
        result = {
            "run_id": "run-uoc-pilot-001",
            "method": "voxel-occupancy-reconstruction",
            "defense_variant": "random-occupancy-jitter-sweep",
            "seed": args.seed,
            "frame_count": results[0]["frame_count"],
            "metric_definition": results[0]["metric_definition"],
            "sweep": results,
            "map": None,
            "map_status": "unavailable_without_verifiable_checkpoint",
            "map_reason": "The official Voxel R-CNN checkpoint is not yet available from a verifiable source; mAP is not inferred.",
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

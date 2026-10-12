#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
import torch

from pcdet_import import load_voxel_backbone

spconv_backbone = load_voxel_backbone("baselines/local/OpenPCDet")
VoxelBackBone8x = spconv_backbone.VoxelBackBone8x

from easydict import EasyDict


def voxelize(points, point_cloud_range, voxel_size):
    points = points[:, :4]
    mask = np.ones(len(points), dtype=bool)
    for axis, (minimum, maximum) in enumerate(zip(point_cloud_range[:3], point_cloud_range[3:])):
        mask &= points[:, axis] >= minimum
        mask &= points[:, axis] < maximum
    points = points[mask]
    coordinates = np.floor((points[:, :3] - point_cloud_range[:3]) / voxel_size).astype(np.int32)
    keys, inverse = np.unique(coordinates, axis=0, return_inverse=True)
    features = np.zeros((len(keys), 4), dtype=np.float32)
    counts = np.bincount(inverse, minlength=len(keys)).astype(np.float32)
    for channel in range(4):
        features[:, channel] = np.bincount(inverse, weights=points[:, channel], minlength=len(keys))
    features /= np.maximum(counts[:, None], 1.0)
    # OpenPCDet voxel coordinates are [batch, z, y, x].
    indices = np.zeros((len(keys), 4), dtype=np.int32)
    indices[:, 1:] = np.stack([keys[:, 2], keys[:, 1], keys[:, 0]], axis=1)
    return features, indices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    point_cloud_range = np.array([0.0, -40.0, -3.0, 70.4, 40.0, 1.0], dtype=np.float32)
    voxel_size = np.array([0.05, 0.05, 0.1], dtype=np.float32)
    grid_size = (point_cloud_range[3:] - point_cloud_range[:3]) / voxel_size
    grid_size = tuple(int(value) for value in grid_size)
    # OpenPCDet expects sparse shape in zyx order.
    grid_size = tuple(reversed(grid_size))

    points = np.fromfile(args.input, dtype=np.float32).reshape(-1, 4)
    features, indices = voxelize(points, point_cloud_range, voxel_size)
    model = VoxelBackBone8x(EasyDict(), input_channels=4, grid_size=list(grid_size)).cuda()
    source_sparse_shape = list(model.sparse_shape)
    model.sparse_shape = source_sparse_shape[:3]
    model.eval()

    with torch.no_grad():
        batch_dict = {
            "batch_size": 1,
            "voxel_features": torch.from_numpy(features).cuda(),
            "voxel_coords": torch.from_numpy(indices).cuda(),
        }
        output = model(batch_dict)

    multi_scale = output["multi_scale_3d_features"]
    result = {
        "input_path": str(args.input),
        "input_points": int(len(points)),
        "input_voxels": int(len(features)),
        "grid_size": list(grid_size),
        "source_sparse_shape": source_sparse_shape,
        "used_sparse_shape": list(model.sparse_shape),
        "layer_feature_shapes": {
            name: [int(value) for value in tensor.features.shape]
            for name, tensor in multi_scale.items()
        },
        "layer_index_counts": {
            name: int(tensor.indices.shape[0])
            for name, tensor in multi_scale.items()
        },
        "output_feature_shape": [int(value) for value in output["encoded_spconv_tensor"].features.shape],
        "output_index_count": int(output["encoded_spconv_tensor"].indices.shape[0]),
        "all_features_finite": bool(
            all(torch.isfinite(tensor.features).all().item() for tensor in multi_scale.values())
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

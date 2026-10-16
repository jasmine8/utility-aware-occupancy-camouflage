#!/usr/bin/env python3
"""Reproduce occupancy entropy for the 16-frame KITTI UOC pilot.
Uses the same voxelization, three-axis support and <= quantile tie policy as
main/run_utility_aware_pilot.py. No synthetic observations.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np

POINT_CLOUD_RANGE = np.array([0., -40., -3., 70.4, 40., 1.], dtype=np.float32)
VOXEL_SIZE = np.array([0.05, 0.05, 0.1], dtype=np.float32)
GRID_SIZE = np.ceil((POINT_CLOUD_RANGE[3:] - POINT_CLOUD_RANGE[:3]) / VOXEL_SIZE).astype(np.int32)
GRID_COUNT = int(np.prod(GRID_SIZE))
BUDGETS = (0., .05, .10, .15, .20, .25, .30, .40, .50, .75)
FIELDS = ('frame', 'budget', 'original', 'retained', 'actual_removal',
          'p_original', 'p_retained', 'entropy_original', 'entropy_retained')


def binary_entropy(p):
    if p <= 0 or p >= 1:
        return 0.0
    return float(-p * np.log2(p) - (1-p) * np.log2(1-p))


def frame_voxels(path):
    points = np.fromfile(path, dtype=np.float32).reshape(-1, 4)
    lo, hi = POINT_CLOUD_RANGE[:3], POINT_CLOUD_RANGE[3:]
    xyz = points[:, :3]
    xyz = xyz[np.all((xyz >= lo) & (xyz < hi), axis=1)]
    return np.unique(np.floor((xyz - lo) / VOXEL_SIZE).astype(np.int32), axis=0)


def support_scores(voxels):
    # Same values as dense yz/xz/xy occupancy projections, without allocating
    # the ~90-million-element 3D array used by the original pilot.
    projections = []
    for cols in ((1, 2), (0, 2), (0, 1)):
        _, inverse, counts = np.unique(voxels[:, cols], axis=0,
                                       return_inverse=True, return_counts=True)
        projections.append(counts[inverse])
    return projections[0] + projections[1] + projections[2]


def calculate(data_dir):
    paths = sorted(Path(data_dir).glob('*.bin'))
    if not paths:
        raise FileNotFoundError(f'No .bin files found in {data_dir}')
    rows = []
    for path in paths:
        voxels = frame_voxels(path)
        n = len(voxels)
        scores = support_scores(voxels)
        for budget in BUDGETS:
            if budget == 0:
                retained = n  # original zero-removal baseline
            else:
                threshold = np.quantile(scores, budget)
                retained = int(np.count_nonzero(scores > threshold))
            p0, p1 = n / GRID_COUNT, retained / GRID_COUNT
            rows.append(dict(frame=path.stem, budget=budget,
                             original=n, retained=retained,
                             actual_removal=(n-retained)/n,
                             p_original=p0, p_retained=p1,
                             entropy_original=binary_entropy(p0),
                             entropy_retained=binary_entropy(p1)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, default=Path('entropy_output'))
    ap.add_argument('--compare-csv', type=Path)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = calculate(args.data_dir)
    csv_path = args.output_dir / 'entropy_analysis.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for b in BUDGETS:
        subset = [r for r in rows if r['budget'] == b]
        summary.append(dict(removal_rate=b, frame_count=len(subset),
                            actual_removal_mean=float(np.mean([r['actual_removal'] for r in subset])),
                            occupancy_entropy_mean_bits=float(np.mean([r['entropy_retained'] for r in subset])),
                            occupancy_entropy_std_bits=float(np.std([r['entropy_retained'] for r in subset], ddof=1))))
    payload = dict(method='deterministic-low-utility-occupancy-removal',
                   entropy_definition='binary entropy of marginal voxel occupancy probability',
                   grid_size=GRID_SIZE.tolist(), grid_count=GRID_COUNT,
                   frame_count=len(rows)//len(BUDGETS),
                   budgets=list(BUDGETS), summary=summary, frames=rows,
                   map=None, map_status='unavailable_without_verifiable_checkpoint')
    (args.output_dir / 'entropy_analysis.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    with (args.output_dir / 'entropy_summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    if args.compare_csv:
        with args.compare_csv.open(newline='', encoding='utf-8') as f:
            old = list(csv.DictReader(f))
        assert len(old) == len(rows), (len(old), len(rows))
        diffs = []
        for idx, (a, b) in enumerate(zip(old, rows)):
            for field in FIELDS:
                if field == 'frame':
                    equal = a[field] == b[field]
                elif field in ('original', 'retained'):
                    equal = int(a[field]) == b[field]
                else:
                    equal = np.isclose(float(a[field]), b[field], rtol=1e-10, atol=1e-12)
                if not equal:
                    diffs.append((idx, field, a[field], b[field]))
        print('Comparison mismatches:', len(diffs))
        for d in diffs[:10]:
            print(d)
    try:
        import matplotlib.pyplot as plt
        x = [100 * s['removal_rate'] for s in summary]
        y = [s['occupancy_entropy_mean_bits'] for s in summary]
        std = [s['occupancy_entropy_std_bits'] for s in summary]
        fig, ax = plt.subplots(figsize=(6.5, 4.1))
        ax.errorbar(x, y, yerr=std, marker='o', capsize=3, linewidth=1.7)
        ax.set_xlabel('Nominal occupied-voxel removal budget (%)')
        ax.set_ylabel('Binary occupancy entropy (bits)')
        ax.grid(alpha=.25)
        fig.tight_layout()
        fig.savefig(args.output_dir / 'entropy_budget.pdf', bbox_inches='tight')
        fig.savefig(args.output_dir / 'entropy_budget.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
    except ImportError:
        print('matplotlib unavailable: data saved, plot skipped')
    print('Grid:', GRID_SIZE.tolist(), GRID_COUNT, 'Rows:', len(rows))
    print('Baseline:', summary[0])
    print('25% nominal:', next(s for s in summary if s['removal_rate'] == .25))
    print('Saved to:', args.output_dir)


if __name__ == '__main__':
    main()

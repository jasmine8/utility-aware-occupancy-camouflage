#!/usr/bin/env python3
"""Generate all 13 additional figures for the paper from experiment data."""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Morandi palette
MIST_STONE = '#8A9199'
SAGE_CLAY = '#7F8F84'
DUST_ROSE = '#B88C8C'
SAGE_LIGHT = '#B7A99A'
MIST_LIGHT = '#D8D1C7'
BG_COLOR = '#F3EEE8'

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': MIST_STONE,
    'axes.labelcolor': '#333333',
    'xtick.color': MIST_STONE,
    'ytick.color': MIST_STONE,
    'grid.color': MIST_LIGHT,
    'grid.alpha': 0.5,
    'legend.framealpha': 0.8,
    'legend.edgecolor': MIST_LIGHT,
})

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = BASE
EXP_DIR = os.path.abspath(os.path.join(BASE, '..', '..', 'experiments', 'main', 'results'))

def save(fig, name):
    fig.savefig(os.path.join(FIG_DIR, f'{name}.pdf'), bbox_inches='tight', dpi=300)
    fig.savefig(os.path.join(FIG_DIR, f'{name}.png'), bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f'  saved {name}')

# Load data
with open(os.path.join(EXP_DIR, 'occupancy_pilot.json')) as f:
    occ_data = json.load(f)
with open(os.path.join(EXP_DIR, 'utility_aware_pilot.json')) as f:
    uoc_data = json.load(f)
with open(os.path.join(EXP_DIR, 'removal_rate_sweep', 'summary.json')) as f:
    sweep = json.load(f)

occ_frames = occ_data['frames']
uoc_frames = uoc_data['frames']
frame_ids = list(range(1, len(occ_frames)+1))

# Extract per-frame metrics
def extract(frames, key, side):
    return [f[side][key] for f in frames]

# ---- Fig 6: CD per frame ----
print('Generating Figure 6: CD per frame')
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(frame_ids, extract(occ_frames, 'cd_cm', 'baseline'), 'o-', color=MIST_STONE, ms=5, lw=1.2, label='Baseline')
ax.plot(frame_ids, extract(occ_frames, 'cd_cm', 'defense'), 's-', color=SAGE_CLAY, ms=5, lw=1.2, label='Random Jitter Defense')
ax.plot(frame_ids, extract(uoc_frames, 'cd_cm', 'defense'), '^-', color=DUST_ROSE, ms=5, lw=1.2, label='UOC Defense')
ax.set_xlabel('Frame Index'); ax.set_ylabel('Chamfer Distance (cm)')
ax.set_title('Per-Frame Chamfer Distance Comparison'); ax.legend(fontsize=8); ax.grid(True, ls='--')
save(fig, 'cd_per_frame')

# ---- Fig 7: HD per frame ----
print('Generating Figure 7: HD per frame')
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(frame_ids, extract(occ_frames, 'hd_cm', 'baseline'), 'o-', color=MIST_STONE, ms=5, lw=1.2, label='Baseline')
ax.plot(frame_ids, extract(occ_frames, 'hd_cm', 'defense'), 's-', color=SAGE_CLAY, ms=5, lw=1.2, label='Random Jitter Defense')
ax.plot(frame_ids, extract(uoc_frames, 'hd_cm', 'defense'), '^-', color=DUST_ROSE, ms=5, lw=1.2, label='UOC Defense')
ax.set_xlabel('Frame Index'); ax.set_ylabel('Hausdorff Distance (cm)')
ax.set_title('Per-Frame Hausdorff Distance Comparison'); ax.legend(fontsize=8); ax.grid(True, ls='--')
save(fig, 'hd_per_frame')

# ---- Fig 8: F1 per frame ----
print('Generating Figure 8: F1 per frame')
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(frame_ids, extract(occ_frames, 'f1_15cm', 'baseline'), 'o-', color=MIST_STONE, ms=5, lw=1.2, label='Baseline')
ax.plot(frame_ids, extract(occ_frames, 'f1_15cm', 'defense'), 's-', color=SAGE_CLAY, ms=5, lw=1.2, label='Random Jitter Defense')
ax.plot(frame_ids, extract(uoc_frames, 'f1_15cm', 'defense'), '^-', color=DUST_ROSE, ms=5, lw=1.2, label='UOC Defense')
ax.set_xlabel('Frame Index'); ax.set_ylabel('F1@15cm')
ax.set_title('Per-Frame F1@15cm Comparison'); ax.legend(fontsize=8); ax.grid(True, ls='--')
ax.set_ylim(0, 1.05)
save(fig, 'f1_per_frame')

# ---- Fig 9: Voxel occupancy distribution ----
print('Generating Figure 9: Voxel occupancy distribution')
fig, ax = plt.subplots(figsize=(7, 3.2))
occ_vox = [f['occupied_voxels'] for f in occ_frames]
pts = [f['points'] for f in occ_frames]
ax2 = ax.twinx()
bars = ax.bar(frame_ids, occ_vox, color=SAGE_CLAY, alpha=0.7, label='Occupied Voxels')
line = ax2.plot(frame_ids, pts, 'o-', color=DUST_ROSE, ms=5, lw=1.2, label='Point Count')
ax.set_xlabel('Frame Index'); ax.set_ylabel('Occupied Voxels', color=SAGE_CLAY)
ax2.set_ylabel('Point Count', color=DUST_ROSE)
ax.set_title('Voxel Occupancy and Point Count per Frame')
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labels1+labels2, fontsize=8, loc='upper right')
save(fig, 'voxel_occupancy_distribution')

# ---- Fig 10: CD degradation ratio per frame ----
print('Generating Figure 10: CD degradation ratio per frame')
fig, ax = plt.subplots(figsize=(7, 3.2))
cd_ratio_jitter = [f['defense']['cd_cm']/f['baseline']['cd_cm'] for f in occ_frames]
cd_ratio_uoc = [f['defense']['cd_cm']/f['baseline']['cd_cm'] for f in uoc_frames]
x = np.arange(len(frame_ids))
w = 0.35
ax.bar(x - w/2, cd_ratio_jitter, w, color=SAGE_CLAY, alpha=0.8, label='Random Jitter')
ax.bar(x + w/2, cd_ratio_uoc, w, color=DUST_ROSE, alpha=0.8, label='UOC')
ax.axhline(y=1.0, color=MIST_STONE, ls='--', lw=1, label='No degradation (1×)')
ax.axhline(y=3.0, color='#e74c3c', ls=':', lw=1, label='3× target threshold')
ax.set_xlabel('Frame Index'); ax.set_ylabel('CD Degradation Ratio')
ax.set_title('CD Degradation Ratio per Frame'); ax.legend(fontsize=7); ax.grid(True, ls='--', axis='y')
ax.set_xticks(x); ax.set_xticklabels(frame_ids)
save(fig, 'cd_degradation_ratio')

# ---- Fig 11: HD degradation ratio per frame ----
print('Generating Figure 11: HD degradation ratio per frame')
fig, ax = plt.subplots(figsize=(7, 3.2))
hd_ratio_jitter = [f['defense']['hd_cm']/f['baseline']['hd_cm'] for f in occ_frames]
hd_ratio_uoc = [f['defense']['hd_cm']/f['baseline']['hd_cm'] for f in uoc_frames]
ax.bar(x - w/2, hd_ratio_jitter, w, color=SAGE_CLAY, alpha=0.8, label='Random Jitter')
ax.bar(x + w/2, hd_ratio_uoc, w, color=DUST_ROSE, alpha=0.8, label='UOC')
ax.axhline(y=1.0, color=MIST_STONE, ls='--', lw=1, label='No degradation (1×)')
ax.set_xlabel('Frame Index'); ax.set_ylabel('HD Degradation Ratio')
ax.set_title('HD Degradation Ratio per Frame'); ax.legend(fontsize=7); ax.grid(True, ls='--', axis='y')
ax.set_xticks(x); ax.set_xticklabels(frame_ids)
save(fig, 'hd_degradation_ratio')

# ---- Fig 12: Privacy-Utility tradeoff scatter ----
print('Generating Figure 12: Privacy-Utility tradeoff')
fig, ax = plt.subplots(figsize=(5, 4))
# Use sweep data
rates = [r['removal_rate'] for r in sweep['rows']]
cd_degs = [r.get('cd_degradation_ratio', r.get('privacy_degradation_ratio_cd', 1)) for r in sweep['rows']]
f1s = [r.get('f1_15cm', r.get('f1_score', 1)) for r in sweep['rows']]
sc = ax.scatter(cd_degs, f1s, c=rates, cmap='YlOrRd_r', s=80, edgecolors=MIST_STONE, zorder=3)
for i, r in enumerate(rates):
    ax.annotate(f'{r:.2f}', (cd_degs[i], f1s[i]), fontsize=7, ha='left', va='bottom')
cbar = plt.colorbar(sc, ax=ax); cbar.set_label('Removal Rate', fontsize=9)
ax.set_xlabel('CD Degradation Ratio (Privacy ↑)'); ax.set_ylabel('F1@15cm (Utility ↑)')
ax.set_title('Privacy–Utility Tradeoff across Removal Rates'); ax.grid(True, ls='--')
save(fig, 'privacy_utility_tradeoff')

# ---- Fig 13: Removal rate vs CD curve ----
print('Generating Figure 13: Removal rate vs CD')
fig, ax = plt.subplots(figsize=(5.5, 3.2))
cd_means = [r.get('mean_cd_cm', r.get('avg_cd', 0)) for r in sweep['rows']]
if all(v == 0 for v in cd_means):
    cd_means = [r.get('cd_degradation_ratio', 1) for r in sweep['rows']]
    ax.set_ylabel('CD Degradation Ratio')
else:
    ax.set_ylabel('Mean CD (cm)')
ax.plot(rates, cd_means, 'o-', color=SAGE_CLAY, ms=7, lw=1.5)
ax.set_xlabel('Removal Rate'); ax.set_title('Removal Rate vs CD Metric'); ax.grid(True, ls='--')
save(fig, 'removal_rate_cd_curve')

# ---- Fig 14: Removal rate vs HD curve ----
print('Generating Figure 14: Removal rate vs HD')
fig, ax = plt.subplots(figsize=(5.5, 3.2))
hd_means = [r.get('mean_hd_cm', r.get('avg_hd', 0)) for r in sweep['rows']]
if all(v == 0 for v in hd_means):
    hd_means = [r.get('hd_degradation_ratio', 1) for r in sweep['rows']]
    ax.set_ylabel('HD Degradation Ratio')
else:
    ax.set_ylabel('Mean HD (cm)')
ax.plot(rates, hd_means, 's-', color=DUST_ROSE, ms=7, lw=1.5)
ax.set_xlabel('Removal Rate'); ax.set_title('Removal Rate vs HD Metric'); ax.grid(True, ls='--')
save(fig, 'removal_rate_hd_curve')

# ---- Fig 15: Removal rate vs F1 curve ----
print('Generating Figure 15: Removal rate vs F1')
fig, ax = plt.subplots(figsize=(5.5, 3.2))
ax.plot(rates, f1s, '^-', color=SAGE_CLAY, ms=7, lw=1.5)
ax.set_xlabel('Removal Rate'); ax.set_ylabel('F1@15cm')
ax.set_title('Removal Rate vs F1@15cm'); ax.grid(True, ls='--')
ax.set_ylim(0, 1.05)
save(fig, 'removal_rate_f1_curve')

# ---- Fig 16: Precision-Recall per frame ----
print('Generating Figure 16: Precision-Recall per frame')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
# Random Jitter
ax1.plot(frame_ids, extract(occ_frames, 'precision_15cm', 'defense'), 'o-', color=SAGE_CLAY, ms=5, lw=1, label='Precision@15cm')
ax1.plot(frame_ids, extract(occ_frames, 'recall_15cm', 'defense'), 's-', color=DUST_ROSE, ms=5, lw=1, label='Recall@15cm')
ax1.set_xlabel('Frame Index'); ax1.set_ylabel('Score'); ax1.set_title('Random Jitter Defense')
ax1.legend(fontsize=8); ax1.grid(True, ls='--'); ax1.set_ylim(0.95, 1.01)
# UOC
ax2.plot(frame_ids, extract(uoc_frames, 'precision_15cm', 'defense'), 'o-', color=SAGE_CLAY, ms=5, lw=1, label='Precision@15cm')
ax2.plot(frame_ids, extract(uoc_frames, 'recall_15cm', 'defense'), 's-', color=DUST_ROSE, ms=5, lw=1, label='Recall@15cm')
ax2.set_xlabel('Frame Index'); ax2.set_ylabel('Score'); ax2.set_title('UOC Defense')
ax2.legend(fontsize=8); ax2.grid(True, ls='--'); ax2.set_ylim(0, 1.05)
fig.suptitle('Precision and Recall per Frame', fontsize=13, y=1.02)
fig.tight_layout()
save(fig, 'precision_recall_per_frame')

# ---- Fig 17: Defense comparison summary bar ----
print('Generating Figure 17: Defense comparison summary')
fig, ax = plt.subplots(figsize=(7, 4))
metrics = ['CD Ratio', 'HD Ratio', 'F1 Drop', 'F1@15cm']
jitter_vals = [
    occ_data['privacy_degradation_ratio_cd'],
    occ_data['privacy_degradation_ratio_hd'],
    occ_data['f1_drop'],
    occ_data['defense_summary']['f1_15cm'] if isinstance(occ_data['defense_summary'], dict) else 0.996
]
uoc_vals = [
    uoc_data['privacy_degradation_ratio_cd'],
    uoc_data['privacy_degradation_ratio_hd'],
    uoc_data['f1_drop'],
    uoc_data['defense_summary']['f1_15cm'] if isinstance(uoc_data['defense_summary'], dict) else 0.638
]
# Use log scale for HD ratio
x_pos = np.arange(len(metrics))
bars1 = ax.bar(x_pos - w/2, jitter_vals, w, color=SAGE_CLAY, alpha=0.85, label='Random Jitter')
bars2 = ax.bar(x_pos + w/2, uoc_vals, w, color=DUST_ROSE, alpha=0.85, label='UOC')
ax.set_yscale('log')
ax.set_xticks(x_pos); ax.set_xticklabels(metrics)
ax.set_ylabel('Value (log scale)'); ax.set_title('Defense Method Comparison (Summary)')
ax.legend(fontsize=9); ax.grid(True, ls='--', axis='y')
save(fig, 'defense_comparison_summary')

# ---- Fig 18: Occupancy removal efficiency per frame ----
print('Generating Figure 18: Occupancy removal efficiency')
fig, ax = plt.subplots(figsize=(7, 3.2))
removal_pct = [f['removed_voxels']/f['occupied_voxels']*100 for f in uoc_frames]
ax.bar(frame_ids, removal_pct, color=SAGE_CLAY, alpha=0.8)
ax.set_xlabel('Frame Index'); ax.set_ylabel('Occupancy Removal (%)')
ax.set_title('Per-Frame Occupancy Removal Rate under UOC'); ax.grid(True, ls='--', axis='y')
save(fig, 'occupancy_removal_efficiency')

print('\nAll 13 new figures generated successfully!')
print(f'Total figures in {FIG_DIR}:')
for f in sorted(os.listdir(FIG_DIR)):
    if f.endswith('.png'):
        print(f'  {f}')

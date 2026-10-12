# Reproducing the Pilot

This document is the operational companion to the manuscript's reproducibility
appendix. It covers: environment, data acquisition, running the pilot and the
9-budget sweep, verifying against the published numbers, regenerating figures, and
archiving a citable release.

All commands assume the **repository root** as the working directory.

---

## 1. Environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Verified with Python 3.12. Only `numpy` and `scipy` are required for the numbers;
`matplotlib` is needed only for figures.

---

## 2. Data acquisition

### Route A — manifest-driven range fetch (recommended)

`data/kitti_velodyne_subset_manifest.json` records, for each of the 16 frames, the
absolute byte range it occupies inside the public KITTI object Velodyne archive
(`data_object_velodyne.zip`) plus its expected size. This lets the exact subset be
restored with HTTP range requests:

```bash
python experiments/main/fetch_kitti_subset_from_manifest.py \
  --manifest data/kitti_velodyne_subset_manifest.json \
  --output   experiments/main/data/kitti/training/velodyne
```

Expected outcome: 16 files, each printing a size that matches its `expected_size`,
e.g. `000001  1924288 bytes`. A size mismatch aborts the run.

After fetching, the frames can be sanity-checked by re-deriving the baseline: the
unmasked occupancy reconstruction should give mean CD ≈ 3.2683 cm over the 16 frames.

### Route B — original subset downloader

`download_kitti_subset.py` parses the archive's central directory directly. It needs
two inputs that are not shipped with this repository:

- `val.txt` — the KITTI devkit val split. An exact copy of the file used is provided
  at `data/kitti_ImageSets_val.txt`.
- `velodyne-central-directory.bin` — a dump of the archive's ZIP central directory.
  Rebuild it by reading the EOCD record at the end of `data_object_velodyne.zip` and
  extracting the central-directory bytes into a standalone file.

```bash
python experiments/main/download_kitti_subset.py \
  --source-url        https://s3.eu-central-1.amazonaws.com/avg-kitti/data_object_velodyne.zip \
  --central-directory tmp/kitti-remote/velodyne-central-directory.bin \
  --val-list          data/kitti_ImageSets_val.txt \
  --output            experiments/main/data/kitti/training/velodyne \
  --manifest          data/kitti_velodyne_subset_manifest.json \
  --count             16
```

Route A is preferred: it needs neither the central-directory dump nor a full-archive
download, and it verifies every frame against the recorded size.

**Frame subset.** The 16 frames are the first 16 entries of the val split:
`000001 000002 000004 000005 000006 000008 000015 000019 000020 000021 000023
000024 000025 000027 000028 000031`.

---

## 3. Running the pilot

### 3.1 Baseline reconstruction

```bash
python experiments/main/run_occupancy_pilot.py \
  --data-dir experiments/main/data/kitti/training/velodyne \
  --output   experiments/main/results/occupancy_pilot.json \
  --perturb-rate 0.2 --seed 20261003
```

### 3.2 The nine canonical budgets

These nine runs produce exactly the released files:

```bash
for r in 0.05 0.10 0.15 0.20 0.25 0.30 0.40 0.50 0.75; do
  python experiments/main/run_utility_aware_pilot.py \
    --data-dir experiments/main/data/kitti/training/velodyne \
    --output   experiments/main/results/removal_rate_sweep/rate_$r.json \
    --removal-rate $r
done
```

The defense is deterministic (fixed subset, quantile threshold on the utility proxy),
so regenerated outputs are bit-for-bit stable in their numerical fields.

### 3.3 Optional: finer low-budget sweep

```bash
for r in 0.01 0.025 0.05 0.075 0.10 0.15 0.20 0.25; do
  python experiments/main/run_utility_aware_pilot.py \
    --data-dir experiments/main/data/kitti/training/velodyne \
    --output   experiments/main/results/lowbudget_rate_$r.json \
    --removal-rate $r
done
```

---

## 4. Verifying against the published numbers

The committed files are the ground truth. After re-running, compare:

| Quantity | Expected | Source file |
|---|---:|---|
| Baseline CD | 3.2683 cm | `results/removal_rate_sweep/summary.json` → `baseline_cd_cm` |
| Baseline HD | 6.0618 cm | same |
| Selected rate | 0.25 | same → `selected_rate` |
| CD at 0.25 | 12.0130 cm (3.6756×) | same → `rows[4]` |
| HD at 0.25 | 1982.9039 cm (327.1165×) | same |
| F1@15cm at 0.25 | 0.9318 | same |
| F1 drop at 0.25 | 0.0682 | same |

A quick automated check:

```bash
python - <<'PY'
import json, pathlib
s = json.loads(pathlib.Path("experiments/main/results/removal_rate_sweep/summary.json").read_text())
rows = {r["removal_rate"]: r for r in s["rows"]}
print("baseline CD      ", round(s["rows"][0]["baseline_cd_cm"], 4))
print("selected rate    ", s["selected_rate"])
print("CD ratio @0.25   ", round(rows[0.25]["cd_degradation_ratio"], 4))
print("HD ratio @0.25   ", round(rows[0.25]["hd_degradation_ratio"], 4))
print("F1 @0.25         ", round(rows[0.25]["f1_15cm"], 4))
assert abs(rows[0.25]["cd_degradation_ratio"] - 3.675569312743203) < 1e-9
print("OK")
PY
```

If a re-run disagrees with the committed values, treat the committed file as
authoritative and report the discrepancy with both files attached.

---

## 5. Regenerating figures and tables

```bash
python paper/figures/scripts/gen_all_figures.py
```

This reads
`experiments/main/results/occupancy_pilot.json`,
`experiments/main/results/utility_aware_pilot.json`, and
`experiments/main/results/removal_rate_sweep/summary.json`, and writes PDF + PNG into
`paper/figures/`. The scripts under `paper/scripts/` are the manuscript-side
derivation scripts kept for provenance; they expect the surrounding manuscript
workspace and are not required for the numbers.

---

## 6. Archiving a citable release (Zenodo DOI)

A DOI is what makes the statement strongest, and it takes minutes:

1. Push this repository to GitHub (see §7).
2. Create a release, e.g. tag `v1.0.0`.
3. Sign in to Zenodo with GitHub, and enable the repository under
   *Settings → GitHub*.
4. Publish the GitHub release; Zenodo automatically archives it and mints a DOI.
5. Paste the DOI into `CITATION.cff`, `DATA_AVAILABILITY.md`, and the manuscript's
   Data Availability Statement. **Already done for this release:** version DOI
   `10.5281/zenodo.23320736` (v1.0.1); concept DOI `10.5281/zenodo.23320735`.

> **Release hygiene (learned the hard way in this repository).** Tag each release on a
> commit that actually differs from the previous one, and keep `version:` in
> `CITATION.cff` in step with the tag — Zenodo reads that file for the record metadata.
> Here `v1.0.0` and `v1.0.1` were tagged on the *same* commit, so the two archived
> snapshots are byte-identical, and an unfilled `affiliation: "TODO"` from
> `CITATION.cff` propagated into the public Zenodo record. The `affiliation` field is
> filled in the working tree (`School of Software, Henan University of Engineering,
> Zhengzhou 451191, China`) but **the archived snapshots cannot be rewritten** — the
> v1.0.1 archive still carries the placeholder. Fix the public record metadata
> (Zenodo → record → Edit → Creators) and/or cut a fresh release so the archived text
> matches.

---

## 7. Publishing to GitHub

```bash
# 1. attribute the commits to the jasmine8 account (repo-local, no global change)
git config user.name  "Mingzhen Li"
git config user.email "29703039+jasmine8@users.noreply.github.com"

# 2. create an empty repo named utility-aware-occupancy-camouflage on GitHub, then:
git remote add origin git@github.com:jasmine8/utility-aware-occupancy-camouflage.git
git push -u origin main
```

Before pushing, confirm:

- [x] `CITATION.cff` author is filled in — `Mingzhen Li`, School of Software, Henan
      University of Engineering, Zhengzhou 451191, China. The archived v1.0.1 record
      still shows the old `TODO`, so either edit the record metadata or cut a new
      release before acceptance.
- [x] `DATA_AVAILABILITY.md` DOI placeholder replaced — `10.5281/zenodo.23320736`.
- [ ] No `*.bin` frames are staged (`git status` should show none; `.gitignore` covers them).

---

## 8. Third-party licenses

| Component | Used for | License / terms |
|---|---|---|
| KITTI 3D Object Velodyne | evaluation data (16 frames, restored at run time) | KITTI terms of use — non-commercial |
| OpenPCDet | audited backbone route (`smoke_voxel_backbone.py`, configs) | Apache-2.0 |

Neither is redistributed here.

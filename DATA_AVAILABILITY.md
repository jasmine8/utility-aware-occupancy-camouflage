# Data Availability Statement

The manuscript's Data Availability Statement should be consistent with what is
actually released here. Two ready-to-paste variants are given below; both assume
the repository URL is public.

## Variant A — repository with a DOI (recommended)

Use this once the GitHub release has been archived on Zenodo (see
`docs/REPRODUCE.md`, §5) and a DOI exists. In the MDPI submission form, select
*"Data available in a publicly accessible repository"*.

> **Data Availability Statement:** The reconstruction code, the complete
> 9-budget × 16-frame numerical results, and all derived figures and tables are
> openly available in the `utility-aware-occupancy-camouflage` repository at
> https://github.com/jasmine8/utility-aware-occupancy-camouflage and are
> archived on Zenodo at https://doi.org/10.5281/zenodo.23320735 (release v1.0.2; this
> DOI always resolves to the newest archived version). Code is released under
> the MIT License and results under CC BY 4.0. The 16 KITTI Velodyne frames used in
> the pilot are not redistributed (KITTI is distributed under its own non-commercial
> terms of use); a frame manifest recording the exact byte ranges and a fetch script
> are provided so the subset is restored automatically. The evaluation deliberately
> does not report downstream detection mAP, because the official Voxel R-CNN
> checkpoint was unavailable from a verifiable source; the audit of that search is
> included in the repository.

## Variant B — repository, no DOI (superseded)

**Not needed for this submission: a DOI now exists, so use Variant A.** Kept only as a
fallback template in case the DOI ever has to be re-minted. In the MDPI submission
form, select *"Data available in a publicly accessible repository"* and add the
"no DOI yet" clause.

> **Data Availability Statement:** The reconstruction code, the complete
> 9-budget × 16-frame numerical results, and all derived figures and tables are
> openly available in the `utility-aware-occupancy-camouflage` repository at
> https://github.com/jasmine8/utility-aware-occupancy-camouflage (MIT for code,
> CC BY 4.0 for results). The repository has no DOI yet; it will be archived with a
> DOI on publication. The 16 KITTI Velodyne frames are not redistributed — KITTI is
> distributed under its own terms of use — but a byte-range manifest and a fetch
> script are included so the exact subset is restored automatically.

## What is released, precisely

| Released | Path |
|---|---|
| Reconstruction + defense code | `experiments/main/*.py` |
| Nine canonical budget runs (16 frames each) | `experiments/main/results/removal_rate_sweep/` |
| Operating-point selection record | `experiments/main/results/removal_rate_sweep/summary.json` |
| Baseline + random-jitter comparison | `experiments/main/results/occupancy_pilot.json`, `occupancy_rate_sweep.json` |
| Frame manifest (byte ranges) + fetch script | `data/kitti_velodyne_subset_manifest.json`, `experiments/main/fetch_kitti_subset_from_manifest.py` |
| All figures and tables | `paper/figures/`, `paper/tables/` |
| Checkpoint audit | `experiments/main/artifacts/checkpoint_route_audit.json` |

## What is deliberately NOT released

- **Raw KITTI frames** — governed by KITTI's own terms of use (non-commercial);
  restored at run time instead.
- **OpenPCDet source** — Apache-2.0, referenced by URL only.
- **A detector checkpoint / mAP results** — no verifiable official Voxel R-CNN
  checkpoint was found; mAP is therefore reported as unavailable rather than
  estimated.

## Consistency checklist

Before submitting the updated statement, confirm:

- [ ] The manuscript's "we release the full 9-budget, 16-frame numerical results and
      the reconstruction code" sentence and this statement describe the same set.
- [ ] The submission form template matches the wording used here.
- [ ] The repository is public (not private) at the time of submission.
- [ ] The DOI, if minted, resolves.

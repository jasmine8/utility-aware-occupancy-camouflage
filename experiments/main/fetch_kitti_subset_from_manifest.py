#!/usr/bin/env python3
"""Restore the fixed 16-frame KITTI Velodyne subset recorded in the release manifest.

`data/kitti_velodyne_subset_manifest.json` records, for every frame used in the
pilot, the absolute byte range ``[data_start, data_end]`` of that frame inside the
public KITTI object Velodyne archive, together with its expected byte size.

This script issues HTTP range requests against that archive and writes the frames
locally, so the released numbers can be reproduced without downloading the full
multi-gigabyte archive and without a separate central-directory dump.

KITTI is distributed under its own terms of use (non-commercial). This script
downloads the frames at run time; the raw frames are deliberately NOT redistributed
with this repository.
"""

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path


def fetch_range(url, start, end, retries=3, timeout=120):
    """Fetch bytes in [start, end] inclusive, retrying on transient failures."""
    expected = end - start + 1
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
            if len(payload) != expected:
                raise ValueError(f"expected {expected} bytes, got {len(payload)}")
            return payload
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/kitti_velodyne_subset_manifest.json"),
        help="release manifest describing the fixed frame subset",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/main/data/kitti/training/velodyne"),
        help="destination directory for the restored *.bin frames",
    )
    parser.add_argument(
        "--source-url",
        default=None,
        help="override the archive URL recorded in the manifest",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    url = args.source_url or manifest["source_url"]
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"source : {url}")
    print(f"output : {args.output}")
    print()

    for record in manifest["records"]:
        payload = fetch_range(url, record["data_start"], record["data_end"])
        if len(payload) != record["expected_size"]:
            raise ValueError(
                f"size mismatch for {record['sample_id']}: "
                f"{len(payload)} != {record['expected_size']}"
            )
        destination = args.output / f"{record['sample_id']}.bin"
        destination.write_bytes(payload)
        digest = hashlib.md5(payload).hexdigest()
        print(f"{record['sample_id']}  {len(payload):>9} bytes  md5={digest}")

    print(f"\nrestored {len(manifest['records'])} frames -> {args.output}")


if __name__ == "__main__":
    main()

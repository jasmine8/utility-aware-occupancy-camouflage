#!/usr/bin/env python3
import argparse
import json
import struct
import time
import urllib.request
from pathlib import Path


def parse_central_directory(path: Path):
    data = path.read_bytes()
    entries = {}
    offset = 0
    while offset + 46 <= len(data) and data[offset:offset + 4] == b"PK\x01\x02":
        fields = struct.unpack_from("<IHHHHHHIIIHHHHHII", data, offset)
        (
            _signature,
            _version_made,
            _version_needed,
            _flags,
            method,
            _modified_time,
            _modified_date,
            _crc,
            compressed_size,
            uncompressed_size,
            name_length,
            extra_length,
            comment_length,
            _disk_start,
            _internal_attributes,
            _external_attributes,
            local_header_offset,
        ) = fields
        name_start = offset + 46
        name = data[name_start:name_start + name_length].decode("utf-8")
        extra_start = name_start + name_length
        extra = data[extra_start:extra_start + extra_length]
        extra_offset = 0
        while extra_offset + 4 <= len(extra):
            header_id, header_size = struct.unpack_from("<HH", extra, extra_offset)
            if header_id == 1:
                value_offset = extra_offset + 4
                if uncompressed_size == 0xFFFFFFFF:
                    uncompressed_size = struct.unpack_from("<Q", extra, value_offset)[0]
                    value_offset += 8
                if compressed_size == 0xFFFFFFFF:
                    compressed_size = struct.unpack_from("<Q", extra, value_offset)[0]
                    value_offset += 8
                if local_header_offset == 0xFFFFFFFF:
                    local_header_offset = struct.unpack_from("<Q", extra, value_offset)[0]
            extra_offset += 4 + header_size
        entries[name] = {
            "method": method,
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
            "local_header_offset": local_header_offset,
        }
        offset += 46 + name_length + extra_length + comment_length
    if not entries:
        raise ValueError(f"No ZIP entries parsed from {path}")
    return entries


def fetch_range(url: str, start: int, end: int, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"Range": f"bytes={start}-{end}"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
            if len(payload) != end - start + 1:
                raise ValueError(f"Expected {end - start + 1} bytes, got {len(payload)}")
            return payload
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def parse_local_header(payload: bytes, expected_name: str):
    if payload[:4] != b"PK\x03\x04":
        raise ValueError("Invalid local ZIP header")
    fields = struct.unpack_from("<IHHHHHIIIHH", payload, 0)
    name_length = fields[9]
    extra_length = fields[10]
    name = payload[30:30 + name_length].decode("utf-8")
    if name != expected_name:
        raise ValueError(f"ZIP name mismatch: expected {expected_name}, got {name}")
    return 30 + name_length + extra_length


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--central-directory", required=True, type=Path)
    parser.add_argument("--val-list", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--count", type=int, default=16)
    args = parser.parse_args()

    val_ids = [line.strip() for line in args.val_list.read_text().splitlines() if line.strip()]
    selected_ids = val_ids[:args.count]
    entries = parse_central_directory(args.central_directory)
    args.output.mkdir(parents=True, exist_ok=True)

    records = []
    for sample_id in selected_ids:
        entry_name = f"training/velodyne/{sample_id}.bin"
        entry = entries.get(entry_name)
        if entry is None:
            raise ValueError(f"Missing ZIP entry: {entry_name}")
        if entry["method"] != 0:
            raise ValueError(f"Expected stored ZIP entry, got method {entry['method']}")
        local_offset = entry["local_header_offset"]
        header = fetch_range(args.source_url, local_offset, local_offset + 127)
        local_header_size = parse_local_header(header, entry_name)
        data_start = local_offset + local_header_size
        data_end = data_start + entry["compressed_size"] - 1
        payload = fetch_range(args.source_url, data_start, data_end)
        output_path = args.output / f"{sample_id}.bin"
        output_path.write_bytes(payload)
        record = {
            "sample_id": sample_id,
            "entry_name": entry_name,
            "data_start": data_start,
            "data_end": data_end,
            "expected_size": entry["uncompressed_size"],
            "downloaded_size": len(payload),
            "output_path": str(output_path),
        }
        if len(payload) != entry["uncompressed_size"]:
            raise ValueError(f"Size mismatch for {sample_id}: {record}")
        records.append(record)
        print(f"downloaded {sample_id}: {len(payload)} bytes")

    manifest = {
        "source_url": args.source_url,
        "val_list_path": str(args.val_list),
        "central_directory_path": str(args.central_directory),
        "selection_rule": f"first {args.count} entries of val.txt",
        "sample_count": len(records),
        "records": records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote manifest: {args.manifest}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def fmt(value, digits=4):
    return f"{value:.{digits}f}"


def load_budgets(result_root):
    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75]
    return [
        json.loads((result_root / "removal_rate_sweep" / f"rate_{rate:.2f}.json").read_text())
        for rate in rates
    ]


def frame_records(data, frame_name):
    return next(
        item
        for item in data["frames"]
        if item["frame"].replace(".bin", "") == frame_name
    )


def budget_row(data, item):
    baseline = item["baseline"]
    defense = item["defense"]
    return {
        "rate": data["removal_rate"],
        "occupied": item["occupied_voxels"],
        "retained": item["defended_occupied_voxels"],
        "removed": item["removed_voxels"],
        "threshold": item["utility_threshold"],
        "cd": defense["cd_cm"],
        "cd_ratio": defense["cd_cm"] / baseline["cd_cm"],
        "hd": defense["hd_cm"],
        "hd_ratio": defense["hd_cm"] / baseline["hd_cm"],
        "f1": defense["f1_15cm"],
        "f1_drop": baseline["f1_15cm"] - defense["f1_15cm"],
    }


def frame_narrative(frame_name, rows):
    baseline_cd = rows[0]["cd"] / rows[0]["cd_ratio"]
    selected = next(row for row in rows if abs(row["rate"] - 0.25) < 1e-9)
    minimum_cd = min(rows, key=lambda row: row["cd"])
    maximum_cd = max(rows, key=lambda row: row["cd"])
    maximum_f1 = max(rows, key=lambda row: row["f1"])
    minimum_f1 = min(rows, key=lambda row: row["f1"])
    rates_meeting_threshold = [row["rate"] for row in rows if row["cd_ratio"] >= 3.0]

    if rates_meeting_threshold:
        first_threshold = min(rates_meeting_threshold)
        threshold_sentence = (
            f"For this frame, the smallest tested budget with a per-frame CD ratio of at least "
            f"three is {first_threshold:.2f}."
        )
    else:
        threshold_sentence = (
            "No tested budget reaches a threefold per-frame CD ratio for this frame."
        )

    return (
        f"Frame {frame_name} contains {rows[0]['occupied']:,} occupied voxels and has an unmasked "
        f"CD of {fmt(baseline_cd)} cm. Across the nine tested budgets, defended CD ranges from "
        f"{fmt(minimum_cd['cd'])} cm at budget {minimum_cd['rate']:.2f} to {fmt(maximum_cd['cd'])} cm "
        f"at budget {maximum_cd['rate']:.2f}; F1@15cm ranges from {fmt(minimum_f1['f1'])} at budget "
        f"{minimum_f1['rate']:.2f} to {fmt(maximum_f1['f1'])} at budget {maximum_f1['rate']:.2f}. "
        f"At the aggregate selected budget 0.25, this frame has CD {fmt(selected['cd'])} cm, a "
        f"{fmt(selected['cd_ratio'])}$\\times$ ratio, HD {fmt(selected['hd'])} cm, a "
        f"{fmt(selected['hd_ratio'])}$\\times$ ratio, and F1@15cm {fmt(selected['f1'])}. "
        f"{threshold_sentence} This frame-level view is descriptive and does not alter the "
        f"aggregate selection rule."
    )


def frame_section(frame_name, budget_data):
    rows = [budget_row(data, frame_records(data, frame_name)) for data in budget_data]
    lines = [
        rf"\subsection{{Frame {frame_name}}}",
        "",
        frame_narrative(frame_name, rows),
        "",
        rf"\begin{{table*}}[!p]",
        rf"\caption{{Cross-budget results for frame {frame_name}.}}",
        rf"\label{{tab:frame-budget-{frame_name}}}",
        r"\centering",
        r"\small",
        r"\begin{tabular}{rrrrrrrrrrr}",
        r"\hline",
        r"Budget & Occupied & Retained & Removed & Threshold & CD (cm) & CD ratio & HD (cm) & HD ratio & F1@15cm & F1 drop \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(
            rf"{row['rate']:.2f} & {row['occupied']} & {row['retained']} & {row['removed']} & "
            rf"{row['threshold']} & {fmt(row['cd'])} & {fmt(row['cd_ratio'])} & {fmt(row['hd'])} & "
            rf"{fmt(row['hd_ratio'])} & {fmt(row['f1'])} & {fmt(row['f1_drop'])} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_root", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    budgets = load_budgets(args.result_root)
    frame_names = [item["frame"].replace(".bin", "") for item in budgets[0]["frames"]]

    lines = [
        r"\section{Per-Frame Cross-Budget Analysis}",
        "",
        r"This section reports, for each of the 16 frames, how the same scene changes across all "
        r"nine tested removal budgets. The purpose is to complement the per-budget aggregate view "
        r"with a scene-level view. Each table follows the same column order so that a frame can be "
        r"read vertically and a budget can be compared across frames horizontally. The narrative "
        r"reports the unmasked CD, the per-frame CD and F1 ranges, the selected 0.25 operating "
        r"point, and the smallest tested budget that reaches a threefold per-frame CD ratio. "
        r"These frame-level threshold observations are descriptive and do not replace the "
        r"predeclared aggregate selection rule.",
        "",
    ]
    for frame_name in frame_names:
        lines.append(frame_section(frame_name, budgets))

    args.output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
import statistics
from pathlib import Path


def fmt(value, digits=4):
    return f"{value:.{digits}f}"


def load_budget(result_root, rate):
    path = result_root / "removal_rate_sweep" / f"rate_{rate:.2f}.json"
    return json.loads(path.read_text())


def frame_rows(data):
    rows = []
    for item in data["frames"]:
        baseline = item["baseline"]
        defense = item["defense"]
        rows.append(
            {
                "frame": item["frame"].replace(".bin", ""),
                "occupied": item["occupied_voxels"],
                "retained": item["defended_occupied_voxels"],
                "removed": item["removed_voxels"],
                "cd": defense["cd_cm"],
                "cd_ratio": defense["cd_cm"] / baseline["cd_cm"],
                "hd": defense["hd_cm"],
                "hd_ratio": defense["hd_cm"] / baseline["hd_cm"],
                "f1": defense["f1_15cm"],
                "f1_drop": baseline["f1_15cm"] - defense["f1_15cm"],
            }
        )
    return rows


def analysis_rows(data):
    rows = frame_rows(data)
    return [
        {
            "name": "Defended CD (cm)",
            "values": [row["cd"] for row in rows],
        },
        {
            "name": "CD degradation ratio",
            "values": [row["cd_ratio"] for row in rows],
        },
        {
            "name": "Defended HD (cm)",
            "values": [row["hd"] for row in rows],
        },
        {
            "name": "HD degradation ratio",
            "values": [row["hd_ratio"] for row in rows],
        },
        {
            "name": "Defended F1@15cm",
            "values": [row["f1"] for row in rows],
        },
        {
            "name": "F1 drop",
            "values": [row["f1_drop"] for row in rows],
        },
    ]


def narrative(data, previous):
    rows = frame_rows(data)
    defense = data["defense_summary"]
    rate = data["removal_rate"]
    cd_values = [row["cd"] for row in rows]
    hd_values = [row["hd"] for row in rows]
    f1_values = [row["f1"] for row in rows]

    paragraphs = [
        f"At removal budget {rate:.2f}, the mean defended CD is {fmt(defense['cd_cm'])} cm, "
        f"a {fmt(data['privacy_degradation_ratio_cd'])}$\\times$ change from the unmasked baseline. "
        f"The mean defended HD is {fmt(defense['hd_cm'])} cm, a "
        f"{fmt(data['privacy_degradation_ratio_hd'])}$\\times$ change, and mean F1@15cm is "
        f"{fmt(defense['f1_15cm'])}, an absolute drop of {fmt(data['f1_drop'])}."
    ]

    paragraphs.append(
        f"Across the 16 frames, defended CD ranges from {fmt(min(cd_values))} to "
        f"{fmt(max(cd_values))} cm, defended HD ranges from {fmt(min(hd_values))} to "
        f"{fmt(max(hd_values))} cm, and defended F1@15cm ranges from {fmt(min(f1_values))} "
        f"to {fmt(max(f1_values))}. This frame-level range is reported because the aggregate "
        f"mean can conceal substantially weaker or stronger degradation in individual scenes."
    )

    if previous is not None:
        previous_defense = previous["defense_summary"]
        budget_delta = rate - previous["removal_rate"]
        cd_delta = defense["cd_cm"] - previous_defense["cd_cm"]
        f1_delta = previous_defense["f1_15cm"] - defense["f1_15cm"]
        normalized_cd = cd_delta / (budget_delta / 0.01)
        normalized_f1 = f1_delta / (budget_delta / 0.01)
        paragraphs.append(
            f"Relative to the preceding tested budget {previous['removal_rate']:.2f}, the additional "
            f"budget of {budget_delta:.2f} increases mean CD by {fmt(cd_delta)} cm and reduces mean "
            f"F1@15cm by {fmt(f1_delta)}. Normalized per 0.01 removal increase, the changes are "
            f"{fmt(normalized_cd)} cm in CD and {fmt(normalized_f1)} in F1. These marginal values "
            f"describe the tested interval only and should not be extrapolated linearly to untested budgets."
        )

    if abs(rate - 0.25) < 1e-9:
        paragraphs.append(
            "This is the selected operating point because it is the smallest tested budget "
            "whose mean CD degradation reaches the predeclared threefold criterion. The selection "
            "does not imply global optimality or downstream utility preservation."
        )

    return "\n\n".join(paragraphs)


def frame_table(data):
    rate = data["removal_rate"]
    rows = frame_rows(data)
    lines = [
        rf"\subsection{{Removal Budget {rate:.2f}}}",
        "",
        rf"\label{{sec:audit-{rate:.2f}}}",
        "",
        r"\begin{table*}[!p]",
        rf"\caption{{Complete frame audit at removal budget {rate:.2f}.}}",
        rf"\label{{tab:audit-{rate:.2f}}}",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lrrrrrrrrr}",
        r"\hline",
        r"Frame & Occupied & Retained & Removed & CD (cm) & CD ratio & HD (cm) & HD ratio & F1@15cm & F1 drop \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(
            rf"{row['frame']} & {row['occupied']} & {row['retained']} & {row['removed']} & "
            rf"{fmt(row['cd'])} & {fmt(row['cd_ratio'])} & {fmt(row['hd'])} & "
            rf"{fmt(row['hd_ratio'])} & {fmt(row['f1'])} & {fmt(row['f1_drop'])} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def summary_table(data):
    rate = data["removal_rate"]
    rows = analysis_rows(data)
    lines = [
        rf"\begin{{table*}}[!p]",
        rf"\caption{{Frame-level statistics at removal budget {rate:.2f}.}}",
        rf"\label{{tab:stats-{rate:.2f}}}",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Metric & Min & Mean & Max & Sample std. & CV (\%) \\",
        r"\hline",
    ]
    for row in rows:
        values = row["values"]
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        lines.append(
            rf"{row['name']} & {fmt(min(values))} & {fmt(mean)} & {fmt(max(values))} & "
            rf"{fmt(std)} & {fmt(100 * std / mean, 2)} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_root", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75]
    datasets = [load_budget(args.result_root, rate) for rate in rates]

    lines = [
        r"\section{Full Per-Budget Frame Audit}",
        "",
        r"This appendix reports a complete frame-level audit for every tested removal budget. "
        r"The purpose is not to introduce a new claim, but to make the aggregate operating-point "
        r"analysis reproducible and auditable. Each subsection first interprets the budget in "
        r"relation to the aggregate metrics and the preceding tested budget, then reports the "
        r"complete 16-frame table and a compact statistical summary. All values are computed from "
        r"the recorded 16-frame KITTI pilot results.",
        "",
    ]
    for index, data in enumerate(datasets):
        previous = datasets[index - 1] if index > 0 else None
        lines.append(frame_table(data))
        lines.append(narrative(data, previous))
        lines.append("")
        lines.append(summary_table(data))
        lines.append("")

    args.output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()

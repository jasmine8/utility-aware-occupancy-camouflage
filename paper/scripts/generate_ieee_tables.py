#!/usr/bin/env python3
import argparse
import json
import statistics
from pathlib import Path


def format_number(value, digits=4):
    return f"{value:.{digits}f}"


def load_budgets(result_root):
    budgets = []
    for path in sorted((result_root / "removal_rate_sweep").glob("rate_*.json")):
        data = json.loads(path.read_text())
        if "baseline_summary" in data:
            budgets.append(data)
    return budgets


def budget_table(budgets):
    lines = [
        r"\begin{table*}[!t]",
        r"\caption{Removal-budget sensitivity on the fixed 16-frame subset.}",
        r"\label{tab:budget}",
        r"\centering",
        r"\begin{tabular}{rrrrrrr}",
        r"\hline",
        r"Budget & CD (cm) & CD ratio & HD (cm) & HD ratio & F1@15cm & F1 drop \\",
        r"\hline",
    ]
    baseline = budgets[0]["baseline_summary"]
    lines.append(
        rf"Unmasked & {format_number(baseline['cd_cm'])} & 1.0000 & "
        rf"{format_number(baseline['hd_cm'])} & 1.0000 & "
        rf"{format_number(baseline['f1_15cm'])} & 0.0000 \\"
    )
    for data in budgets:
        defense = data["defense_summary"]
        lines.append(
            rf"{data['removal_rate']:.2f} & {format_number(defense['cd_cm'])} & "
            rf"{format_number(data['privacy_degradation_ratio_cd'])} & "
            rf"{format_number(defense['hd_cm'])} & "
            rf"{format_number(data['privacy_degradation_ratio_hd'])} & "
            rf"{format_number(defense['f1_15cm'])} & "
            rf"{format_number(data['f1_drop'])} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def frame_table(result_root):
    data = json.loads((result_root / "removal_rate_sweep" / "rate_0.25.json").read_text())
    lines = [
        r"\begin{table*}[!t]",
        r"\caption{Per-frame results at the selected 0.25 removal budget.}",
        r"\label{tab:frames}",
        r"\centering",
        r"\begin{tabular}{lrrrrrrrr}",
        r"\hline",
        r"Frame & Occupied & Retained & CD (cm) & CD ratio & HD (cm) & HD ratio & F1@15cm & F1 drop \\",
        r"\hline",
    ]
    for item in data["frames"]:
        baseline = item["baseline"]
        defense = item["defense"]
        cd_ratio = defense["cd_cm"] / baseline["cd_cm"]
        hd_ratio = defense["hd_cm"] / baseline["hd_cm"]
        f1_drop = baseline["f1_15cm"] - defense["f1_15cm"]
        frame = item["frame"].replace(".bin", "")
        lines.append(
            rf"{frame} & {item['occupied_voxels']} & {item['defended_occupied_voxels']} & "
            rf"{format_number(defense['cd_cm'])} & {format_number(cd_ratio)} & "
            rf"{format_number(defense['hd_cm'])} & {format_number(hd_ratio)} & "
            rf"{format_number(defense['f1_15cm'])} & {format_number(f1_drop)} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def marginal_table(budgets):
    lines = [
        r"\begin{table*}[!t]",
        r"\caption{Marginal changes between adjacent tested removal budgets. Normalized changes are reported per 0.01 increase in removal budget.}",
        r"\label{tab:marginal}",
        r"\centering",
        r"\begin{tabular}{rrrrrr}",
        r"\hline",
        r"Interval & Budget increase & CD increase (cm) & CD / 0.01 & F1 drop & F1 drop / 0.01 \\",
        r"\hline",
    ]
    for previous, current in zip(budgets, budgets[1:]):
        budget_increase = current["removal_rate"] - previous["removal_rate"]
        cd_increase = current["defense_summary"]["cd_cm"] - previous["defense_summary"]["cd_cm"]
        f1_drop = current["defense_summary"]["f1_15cm"] - previous["defense_summary"]["f1_15cm"]
        steps = budget_increase / 0.01
        lines.append(
            rf"{previous['removal_rate']:.2f}--{current['removal_rate']:.2f} & "
            rf"{budget_increase:.2f} & {format_number(cd_increase)} & "
            rf"{format_number(cd_increase / steps)} & {format_number(-f1_drop)} & "
            rf"{format_number(-f1_drop / steps)} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def summary_table(result_root):
    data = json.loads((result_root / "removal_rate_sweep" / "rate_0.25.json").read_text())
    metric_rows = {
        "Defended CD (cm)": [item["defense"]["cd_cm"] for item in data["frames"]],
        "Defended HD (cm)": [item["defense"]["hd_cm"] for item in data["frames"]],
        "Defended F1@15cm": [item["defense"]["f1_15cm"] for item in data["frames"]],
        "CD degradation ratio": [
            item["defense"]["cd_cm"] / item["baseline"]["cd_cm"]
            for item in data["frames"]
        ],
        "HD degradation ratio": [
            item["defense"]["hd_cm"] / item["baseline"]["hd_cm"]
            for item in data["frames"]
        ],
    }
    lines = [
        r"\begin{table*}[!t]",
        r"\caption{Frame-level statistics at the selected 0.25 removal budget.}",
        r"\label{tab:frame-stats}",
        r"\centering",
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Metric & Min & Mean & Max & Sample std. & CV (\%) \\",
        r"\hline",
    ]
    for name, values in metric_rows.items():
        mean = statistics.mean(values)
        sample_std = statistics.stdev(values)
        coefficient_variation = 100 * sample_std / mean
        lines.append(
            rf"{name} & {format_number(min(values))} & {format_number(mean)} & "
            rf"{format_number(max(values))} & {format_number(sample_std)} & "
            rf"{format_number(coefficient_variation, 2)} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def threshold_table(result_root):
    data = json.loads((result_root / "removal_rate_sweep" / "rate_0.25.json").read_text())
    lines = [
        r"\begin{table*}[!t]",
        r"\caption{Utility-threshold audit at the selected 0.25 removal budget.}",
        r"\label{tab:thresholds}",
        r"\centering",
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Frame & Occupied & Retained & Removed & Actual removal rate & Utility threshold \\",
        r"\hline",
    ]
    for item in data["frames"]:
        actual_rate = item["removed_voxels"] / item["occupied_voxels"]
        frame = item["frame"].replace(".bin", "")
        lines.append(
            rf"{frame} & {item['occupied_voxels']} & {item['defended_occupied_voxels']} & "
            rf"{item['removed_voxels']} & {format_number(actual_rate)} & "
            rf"{item['utility_threshold']} \\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def replace_table(text, label, block):
    label_marker = f"\\label{{{label}}}"
    label_index = text.find(label_marker)
    if label_index == -1:
        raise ValueError(f"missing table label: {label}")
    start = text.rfind("\\begin{table*}", 0, label_index)
    end_marker = "\\end{table*}"
    end = text.find(end_marker, label_index)
    if start == -1 or end == -1:
        raise ValueError(f"malformed table block: {label}")
    end += len(end_marker)
    while end < len(text) and text[end] == "\n":
        end += 1
    return text[:start] + block + text[end:]


def insert_after_section(text, section, block):
    marker = f"\\section{{{section}}}"
    marker_index = text.find(marker)
    if marker_index == -1:
        raise ValueError(f"missing section: {marker}")
    insertion_index = marker_index + len(marker)
    return text[:insertion_index] + "\n\n" + block + text[insertion_index:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_root", type=Path)
    parser.add_argument("tex_path", type=Path)
    args = parser.parse_args()

    budgets = load_budgets(args.result_root)
    if len(budgets) != 9:
        raise ValueError(f"expected 9 budget result files, found {len(budgets)}")

    text = args.tex_path.read_text()
    text = replace_table(text, "tab:budget", budget_table(budgets))
    text = replace_table(text, "tab:frames", frame_table(args.result_root))
    text = insert_after_section(text, "Budget-Selection Sensitivity", marginal_table(budgets))
    text = insert_after_section(text, "Frame-Level Reporting", summary_table(args.result_root))
    text = insert_after_section(text, "Utility Thresholds", threshold_table(args.result_root))
    args.tex_path.write_text(text)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def fmt(value, digits=4):
    return f"{value:.{digits}f}"


def load_budget(result_root, rate):
    return json.loads((result_root / "removal_rate_sweep" / f"rate_{rate:.2f}.json").read_text())


def frame_statistics(data):
    cd = [item["defense"]["cd_cm"] for item in data["frames"]]
    hd = [item["defense"]["hd_cm"] for item in data["frames"]]
    f1 = [item["defense"]["f1_15cm"] for item in data["frames"]]
    return cd, hd, f1


def budget_narrative(data, previous):
    rate = data["removal_rate"]
    defense = data["defense_summary"]
    cd_values, hd_values, f1_values = frame_statistics(data)

    paragraphs = [
        f"At removal budget {rate:.2f}, mean defended CD is {fmt(defense['cd_cm'])} cm, "
        f"corresponding to {fmt(data['privacy_degradation_ratio_cd'])}$\\times$ the unmasked baseline. "
        f"Mean HD is {fmt(defense['hd_cm'])} cm, or {fmt(data['privacy_degradation_ratio_hd'])}$\\times$ "
        f"the baseline. Mean F1@15cm is {fmt(defense['f1_15cm'])}, an absolute drop of {fmt(data['f1_drop'])}."
    ]

    paragraphs.append(
        f"The per-frame range is substantial: defended CD spans {fmt(min(cd_values))}--{fmt(max(cd_values))} cm, "
        f"HD spans {fmt(min(hd_values))}--{fmt(max(hd_values))} cm, and F1@15cm spans "
        f"{fmt(min(f1_values))}--{fmt(max(f1_values))}. Reporting only the mean would hide these "
        f"scene-dependent differences."
    )

    if previous is not None:
        previous_defense = previous["defense_summary"]
        budget_delta = rate - previous["removal_rate"]
        cd_delta = defense["cd_cm"] - previous_defense["cd_cm"]
        f1_delta = previous_defense["f1_15cm"] - defense["f1_15cm"]
        steps = budget_delta / 0.01
        paragraphs.append(
            f"Compared with budget {previous['removal_rate']:.2f}, the added budget is {budget_delta:.2f}. "
            f"Mean CD increases by {fmt(cd_delta)} cm and F1@15cm decreases by {fmt(f1_delta)}. "
            f"Normalized per 0.01 budget, these changes are {fmt(cd_delta / steps)} cm and "
            f"{fmt(f1_delta / steps)}. The marginal interpretation applies only to this tested interval."
        )

    if abs(rate - 0.25) < 1e-9:
        paragraphs.append(
            "This budget is selected because it is the smallest tested setting whose mean CD degradation "
            "reaches the predeclared threefold criterion. It is not claimed to be globally optimal, and "
            "it is not evidence of downstream detection-utility preservation."
        )
    elif rate < 0.25:
        paragraphs.append(
            "The tested CD criterion is not met at this budget. This is important because it shows that "
            "the selected operating point is not an arbitrary choice among equivalent small budgets."
        )
    else:
        paragraphs.append(
            "The CD criterion is met with additional margin, but reconstruction fidelity is lower and more "
            "occupancy evidence is discarded. These larger budgets are useful for sensitivity analysis, "
            "not as the preferred pilot operating point."
        )

    return "\n\n".join(paragraphs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_root", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75]
    datasets = [load_budget(args.result_root, rate) for rate in rates]

    lines = [
        r"\section{Per-Budget Analysis}",
        "",
        r"This section interprets each tested removal budget at the same level of detail as the selected "
        r"operating point. The purpose is to prevent a single aggregate result from obscuring the "
        r"nonlinear relationship between removal budget, privacy degradation, and reconstruction fidelity. "
        r"Each subsection reports the aggregate means, the per-frame range, the marginal change from the "
        r"preceding tested budget, and whether the budget satisfies the predeclared CD criterion. No "
        r"untested budget is inferred or extrapolated.",
        "",
    ]
    for index, data in enumerate(datasets):
        previous = datasets[index - 1] if index > 0 else None
        rate = data["removal_rate"]
        lines.extend(
            [
                rf"\subsection{{Removal Budget {rate:.2f}}}",
                "",
                budget_narrative(data, previous),
                "",
            ]
        )

    args.output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()

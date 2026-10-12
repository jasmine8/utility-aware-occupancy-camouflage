#!/usr/bin/env python3
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
LATEX_ROOT = ROOT / "paper" / "latex"
BUILD_ROOT = ROOT / "paper" / "build"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_metrics(log_path):
    text = log_path.read_text(errors="ignore")
    return {
        "fatal_errors": len(re.findall(r"(?m)^!", text)),
        "undefined_citations": len(re.findall(r"Citation .* undefined", text)),
        "undefined_references": len(re.findall(r"Reference .* undefined", text)),
        "overfull_boxes": len(re.findall(r"Overfull", text)),
        "underfull_boxes": len(re.findall(r"Underfull", text)),
        "rerun_warnings": len(re.findall(r"Rerun to get cross-references right", text)),
        "label_change_warnings": len(re.findall(r"Label\(s\) may have changed", text)),
        "output_line": next(
            (line.strip() for line in text.splitlines() if "Output written on" in line),
            "missing",
        ),
    }


def validate_structure():
    main_path = LATEX_ROOT / "ieee_paper.tex"
    budget_path = LATEX_ROOT / "ieee_budget_analysis.tex"
    frame_path = LATEX_ROOT / "ieee_frame_budget_analysis.tex"
    audit_path = LATEX_ROOT / "ieee_extended_audit.tex"
    bib_path = LATEX_ROOT / "ieee_references.bib"

    paths = {
        "main": main_path,
        "budget_analysis": budget_path,
        "frame_budget_analysis": frame_path,
        "extended_audit": audit_path,
        "bibliography": bib_path,
    }
    for name, path in paths.items():
        assert path.is_file(), f"missing {name}: {path}"

    main = main_path.read_text()
    budget = budget_path.read_text()
    frame = frame_path.read_text()
    audit = audit_path.read_text()
    bibliography = bib_path.read_text()

    assert main.count(r"\documentclass[journal,twocolumn]{IEEEtran}") == 1
    assert main.count(r"\end{document}") == 1
    assert main.count(r"\input{ieee_budget_analysis}") == 1
    assert main.count(r"\input{ieee_frame_budget_analysis}") == 1
    assert main.count(r"\input{ieee_extended_audit}") == 1

    analysis_sections = {
        "budget_analysis": len(re.findall(r"(?m)^\\section\{Per-Budget Analysis\}", budget)),
        "budget_subsections": len(re.findall(r"(?m)^\\subsection\{Removal Budget", budget)),
        "frame_analysis": len(re.findall(r"(?m)^\\section\{Per-Frame Cross-Budget Analysis\}", frame)),
        "frame_subsections": len(re.findall(r"(?m)^\\subsection\{Frame ", frame)),
        "audit": len(re.findall(r"(?m)^\\section\{Full Per-Budget Frame Audit\}", audit)),
        "audit_subsections": len(re.findall(r"(?m)^\\subsection\{Removal Budget", audit)),
    }
    assert analysis_sections == {
        "budget_analysis": 1,
        "budget_subsections": 9,
        "frame_analysis": 1,
        "frame_subsections": 16,
        "audit": 1,
        "audit_subsections": 9,
    }

    bib_entries = re.findall(r"(?m)^@\w+\{([^,]+),", bibliography)
    cited_entries = []
    for citation in re.findall(r"\\cite\{([^}]+)\}", main):
        cited_entries.extend(key.strip() for key in citation.split(","))
    assert len(bib_entries) == 21
    assert len(set(bib_entries)) == 21
    assert len(set(cited_entries)) == 21
    assert not set(cited_entries) - set(bib_entries)
    assert not set(bib_entries) - set(cited_entries)

    assembled = "\n".join([main, budget, frame, audit])
    labels = re.findall(r"\\label\{([^}]+)\}", assembled)
    duplicate_labels = sorted(
        label for label, count in Counter(labels).items() if count > 1
    )
    references = re.findall(r"\\(?:ref|autoref|Cref|cref)\{([^}]+)\}", assembled)
    unresolved_references = sorted(set(references) - set(labels))
    assert not duplicate_labels
    assert not unresolved_references

    graphics = re.findall(r"\\includegraphics\[[^]]*\]\{([^}]+)\}", main)
    assert len(graphics) == 5
    for graphic in graphics:
        assert (LATEX_ROOT / graphic).resolve().is_file(), graphic

    return {
        "status": "ok",
        "layout": "IEEE journal two-column",
        "document_class": "IEEEtran",
        "sections": len(re.findall(r"(?m)^\\section\{", assembled)),
        "subsections": len(re.findall(r"(?m)^\\subsection\{", assembled)),
        "figures": len(graphics),
        "tables": len(re.findall(r"\\begin\{table\*?\}", assembled)),
        "bibliography_entries": len(bib_entries),
        "unique_cited_entries": len(set(cited_entries)),
        "citation_instances": len(cited_entries),
        "labels": len(labels),
        "references": len(references),
        "duplicate_labels": len(duplicate_labels),
        "unresolved_references": len(unresolved_references),
        "analysis_inventory": analysis_sections,
        "source_words": len(assembled.split()),
    }


def main():
    source_pdf = LATEX_ROOT / "ieee_paper.pdf"
    log_path = LATEX_ROOT / "ieee_paper.log"
    bbl_path = LATEX_ROOT / "ieee_paper.bbl"
    assert source_pdf.is_file()
    assert log_path.is_file()
    assert bbl_path.is_file()

    structure = validate_structure()
    compile_metrics = log_metrics(log_path)
    assert compile_metrics["fatal_errors"] == 0
    assert compile_metrics["undefined_citations"] == 0
    assert compile_metrics["undefined_references"] == 0
    assert compile_metrics["rerun_warnings"] == 0
    assert compile_metrics["label_change_warnings"] == 0

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    delivery_pdf = BUILD_ROOT / "paper.pdf"
    shutil.copyfile(source_pdf, delivery_pdf)

    reader = PdfReader(str(delivery_pdf))
    assert len(reader.pages) >= 20, len(reader.pages)
    box = reader.pages[0].mediabox

    checked_at = datetime.now(timezone.utc).isoformat()
    pdf_hash = sha256(delivery_pdf)
    pdf_size = delivery_pdf.stat().st_size

    validation = {
        "schema_version": 1,
        "checked_at": checked_at,
        "structure": structure,
        "compile": compile_metrics,
        "pdf": {
            "path": "paper/build/paper.pdf",
            "pages": len(reader.pages),
            "bytes": pdf_size,
            "sha256": pdf_hash,
            "media_box_inches": [
                round(float(box.width) / 72, 2),
                round(float(box.height) / 72, 2),
            ],
        },
        "ok": True,
    }
    validation_path = BUILD_ROOT / "ieee_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n")

    compile_report = {
        "schema_version": 2,
        "status": "success",
        "checked_at": checked_at,
        "toolchain": {
            "latex": "pdfTeX",
            "bibliography": "BibTeX with IEEEtran.bst",
            "document_class": "IEEEtran",
            "layout": "journal, twocolumn",
        },
        "commands": [
            "pdflatex -interaction=nonstopmode ieee_paper.tex",
            "bibtex ieee_paper",
            "pdflatex -interaction=nonstopmode ieee_paper.tex",
            "pdflatex -interaction=nonstopmode ieee_paper.tex",
        ],
        "inputs": [
            "paper/latex/ieee_paper.tex",
            "paper/latex/ieee_budget_analysis.tex",
            "paper/latex/ieee_frame_budget_analysis.tex",
            "paper/latex/ieee_extended_audit.tex",
            "paper/latex/ieee_references.bib",
            "paper/latex/IEEEtran.cls",
            "paper/latex/IEEEtran.bst",
            "paper/figures/removal_budget_tradeoff.pdf",
            "paper/figures/budget_metric_decomposition.pdf",
            "paper/figures/budget_marginal_cost.pdf",
            "paper/figures/frame_variability.pdf",
            "paper/figures/occupancy_degradation_relation.pdf",
        ],
        "outputs": [
            "paper/build/paper.pdf",
            "paper/build/compile_report.json",
            "paper/build/ieee_validation.json",
        ],
        "pdf_bytes": pdf_size,
        "pdf_sha256": pdf_hash,
        "pdf_pages": len(reader.pages),
        "media_box_inches": [
            round(float(box.width) / 72, 2),
            round(float(box.height) / 72, 2),
        ],
        "validation_summary": {
            "fatal_errors": compile_metrics["fatal_errors"],
            "undefined_citations": compile_metrics["undefined_citations"],
            "undefined_references": compile_metrics["undefined_references"],
            "overfull_boxes": compile_metrics["overfull_boxes"],
            "underfull_boxes": compile_metrics["underfull_boxes"],
            "duplicate_labels": structure["duplicate_labels"],
            "bibliography_entries": structure["bibliography_entries"],
            "unique_cited_entries": structure["unique_cited_entries"],
            "figures": structure["figures"],
            "tables": structure["tables"],
        },
        "evidence_boundary": (
            "Fixed 16-frame KITTI Velodyne pilot; downstream 3D detection mAP remains unverified."
        ),
        "ok": True,
    }
    (BUILD_ROOT / "compile_report.json").write_text(
        json.dumps(compile_report, indent=2) + "\n"
    )

    build_config = {
        "schema_version": 2,
        "title": "Utility-Aware Occupancy Camouflage for Point Cloud Privacy: A Scoped Pilot Study",
        "build_root": "paper/build",
        "layout": "IEEE journal two-column",
        "inputs": {
            "manuscript": "paper/latex/ieee_paper.tex",
            "included_sections": [
                "paper/latex/ieee_budget_analysis.tex",
                "paper/latex/ieee_frame_budget_analysis.tex",
                "paper/latex/ieee_extended_audit.tex",
            ],
            "bibliography": "paper/latex/ieee_references.bib",
            "figures": [
                "paper/figures/removal_budget_tradeoff.pdf",
                "paper/figures/budget_metric_decomposition.pdf",
                "paper/figures/budget_marginal_cost.pdf",
                "paper/figures/frame_variability.pdf",
                "paper/figures/occupancy_degradation_relation.pdf",
            ],
        },
        "outputs": {
            "pdf": "paper/build/paper.pdf",
            "compile_report": "paper/build/compile_report.json",
            "validation_report": "paper/build/ieee_validation.json",
        },
        "preferred_toolchain": {
            "name": "pdflatex-bibtex-ieee",
            "commands": [
                "pdflatex -interaction=nonstopmode ieee_paper.tex",
                "bibtex ieee_paper",
                "pdflatex -interaction=nonstopmode ieee_paper.tex",
                "pdflatex -interaction=nonstopmode ieee_paper.tex",
            ],
            "required_binaries": ["pdflatex", "bibtex"],
            "status": "success",
        },
        "notes": [
            "The authoritative manuscript source is the IEEEtran LaTeX source under paper/latex.",
            "This build does not alter any measured result or evidence boundary.",
        ],
    }
    (ROOT / "paper" / "build_config.json").write_text(
        json.dumps(build_config, indent=2) + "\n"
    )

    print("finalize_validation=ok")
    print(f"pdf_pages={len(reader.pages)}")
    print(f"pdf_bytes={pdf_size}")
    print(f"pdf_sha256={pdf_hash}")
    print(f"fatal_errors={compile_metrics['fatal_errors']}")
    print(f"undefined_citations={compile_metrics['undefined_citations']}")
    print(f"undefined_references={compile_metrics['undefined_references']}")
    print(f"overfull_boxes={compile_metrics['overfull_boxes']}")
    print(f"underfull_boxes={compile_metrics['underfull_boxes']}")
    print(f"bibliography_entries={structure['bibliography_entries']}")
    print(f"figures={structure['figures']}")
    print(f"tables={structure['tables']}")


if __name__ == "__main__":
    main()

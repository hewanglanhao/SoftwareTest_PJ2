import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from utils.experiment import (
    COMPARISON_DIRNAME,
    REPORT_ASSETS_DIRNAME,
    SINGLE_RUN_DIRNAME,
    resolve_output_dir,
)
from utils.object_utils import dump_json


def load_single_run_records(single_dir: Path) -> List[Dict]:
    records = []
    for json_file in sorted(single_dir.glob("sample-*.json")):
        if json_file.stem.endswith("-population"):
            continue
        records.append(json.loads(json_file.read_text(encoding="utf-8")))
    return records


def load_comparison_bundle(comparison_dir: Path) -> Dict:
    raw_results_path = comparison_dir / "raw_results.json"
    if not raw_results_path.exists():
        return {"metadata": {}, "runs": [], "summary": []}
    return json.loads(raw_results_path.read_text(encoding="utf-8"))


def build_report_bundle(single_records: List[Dict], comparison_bundle: Dict) -> Dict:
    return {
        "single_runs": single_records,
        "single_run_count": len(single_records),
        "comparison_metadata": comparison_bundle.get("metadata", {}),
        "comparison_runs": comparison_bundle.get("runs", []),
        "comparison_summary": comparison_bundle.get("summary", []),
    }


def write_csv(path: Path, rows: List[Dict]):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def format_markdown(bundle: Dict) -> str:
    lines = [
        "# Result Summary",
        "",
        "## Single Runs",
        "",
        f"- Total saved single runs: {bundle['single_run_count']}",
    ]

    if bundle["single_runs"]:
        lines.extend([
            "",
            "| sample | schedule | run_time | initial_seed_count | covered_line_count | crash_count | total_paths | total_execs | duration_seconds |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for row in bundle["single_runs"]:
            lines.append(
                "| {sample} | {schedule} | {run_time} | {initial_seed_count} | "
                "{covered_line_count} | {crash_count} | {total_paths} | "
                "{total_execs} | {duration_seconds} |".format(**row)
            )

    lines.extend([
        "",
        "## Comparison Summary",
        "",
        f"- Comparison runs: {len(bundle['comparison_runs'])}",
        f"- Comparison summaries: {len(bundle['comparison_summary'])}",
    ])

    if bundle["comparison_summary"]:
        lines.extend([
            "",
            "| sample | schedule | runs | run_time | initial_seed_count | avg_execs | avg_paths | avg_covered_lines | avg_crashes | avg_duration_seconds |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for row in bundle["comparison_summary"]:
            lines.append(
                "| {sample} | {schedule} | {runs} | {run_time} | {initial_seed_count} | "
                "{avg_execs} | {avg_paths} | {avg_covered_lines} | {avg_crashes} | "
                "{avg_duration_seconds} |".format(**row)
            )

    return "\n".join(lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize fuzzing outputs for reports.")
    parser.add_argument("--input-dir", default="_result",
                        help="Base result directory containing single/ and comparison/")
    parser.add_argument("--output-dir", default=None,
                        help="Directory for summary artifacts; defaults to <input-dir>/report_assets")
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = (
        Path(args.output_dir)
        if args.output_dir is not None
        else resolve_output_dir(str(input_dir), REPORT_ASSETS_DIRNAME)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    single_records = load_single_run_records(input_dir / SINGLE_RUN_DIRNAME)
    comparison_bundle = load_comparison_bundle(input_dir / COMPARISON_DIRNAME)
    report_bundle = build_report_bundle(single_records, comparison_bundle)

    dump_json(str(output_dir / "report_bundle.json"), report_bundle)
    write_csv(output_dir / "single_runs.csv", single_records)
    write_csv(output_dir / "comparison_summary.csv", report_bundle["comparison_summary"])
    (output_dir / "summary.md").write_text(format_markdown(report_bundle), encoding="utf-8")
    print(f"saved report assets to {output_dir.resolve()}")


if __name__ == "__main__":
    main()

import argparse
import csv
import json
import random
import statistics
import time
from pathlib import Path

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer
from main import build_sample
from runner.function_coverage_runner import FunctionCoverageRunner
from schedule.registry import SCHEDULES, create_schedule
from utils.object_utils import load_object


def run_once(sample_id, schedule_name, run_time, seed, max_input_length):
    # 固定随机种子，使不同策略的对比结果更容易复现。
    random.seed(seed)
    target_function, corpus_path = build_sample(sample_id)
    seeds = load_object(corpus_path)
    runner = FunctionCoverageRunner(target_function)
    fuzzer = PathGreyBoxFuzzer(
        seeds=seeds,
        schedule=create_schedule(schedule_name),
        is_print=False,
        max_input_length=max_input_length,
    )

    start_time = time.time()
    fuzzer.runs(runner, run_time=run_time)
    end_time = time.time()

    return {
        "sample": sample_id,
        "schedule": schedule_name,
        "seed": seed,
        "run_time_limit": run_time,
        "duration_seconds": end_time - start_time,
        "total_execs": fuzzer.total_execs,
        "total_paths": fuzzer.total_paths,
        "covered_line_count": len(fuzzer.covered_line),
        "crash_count": len(set(fuzzer.crash_map.values())),
    }


def aggregate_results(rows):
    # 按 sample 和 schedule 聚合多次重复实验，计算平均指标。
    grouped = {}
    for row in rows:
        key = (row["sample"], row["schedule"])
        grouped.setdefault(key, []).append(row)

    summary = []
    for (sample, schedule), items in sorted(grouped.items()):
        summary.append({
            "sample": sample,
            "schedule": schedule,
            "runs": len(items),
            "avg_execs": _mean(items, "total_execs"),
            "avg_paths": _mean(items, "total_paths"),
            "avg_covered_lines": _mean(items, "covered_line_count"),
            "avg_crashes": _mean(items, "crash_count"),
            "avg_duration_seconds": _mean(items, "duration_seconds"),
        })
    return summary


def _mean(rows, key):
    return round(statistics.mean(row[key] for row in rows), 3)


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_text_summary(path, summary):
    lines = [
        "Schedule comparison summary",
        "",
        "Higher covered lines, paths, crashes, and execs are usually better, but they show different trade-offs.",
        "",
    ]
    for row in summary:
        lines.append(
            "sample={sample} schedule={schedule} runs={runs} "
            "avg_execs={avg_execs} avg_paths={avg_paths} "
            "avg_covered_lines={avg_covered_lines} avg_crashes={avg_crashes} "
            "avg_duration_seconds={avg_duration_seconds}".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Compare all seed scheduling strategies.")
    parser.add_argument("--samples", nargs="+", type=int, default=[1, 2, 3, 4],
                        choices=(1, 2, 3, 4), help="Sample ids to run")
    parser.add_argument("--schedules", nargs="+", default=sorted(SCHEDULES),
                        choices=sorted(SCHEDULES), help="Schedules to compare")
    parser.add_argument("--run-time", type=int, default=1,
                        help="Seconds per sample/schedule/repeat")
    parser.add_argument("--repeats", type=int, default=1,
                        help="Repeated runs per sample/schedule")
    parser.add_argument("--seed", type=int, default=2026,
                        help="Base random seed")
    parser.add_argument("--max-input-length", type=int, default=4096,
                        help="Cap generated inputs to keep parser samples stable")
    parser.add_argument("--output-dir", default="_result/schedule_comparison",
                        help="Directory for JSON/CSV/TXT results")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for sample_id in args.samples:
        for schedule_name in args.schedules:
            for repeat in range(args.repeats):
                # 不同 sample/repeat 使用不同 seed，避免每组实验完全相同。
                run_seed = args.seed + sample_id * 1000 + repeat
                row = run_once(
                    sample_id=sample_id,
                    schedule_name=schedule_name,
                    run_time=args.run_time,
                    seed=run_seed,
                    max_input_length=args.max_input_length,
                )
                rows.append(row)
                print(
                    f"sample={sample_id} schedule={schedule_name} "
                    f"execs={row['total_execs']} paths={row['total_paths']} "
                    f"covered={row['covered_line_count']} crashes={row['crash_count']}"
                )

    summary = aggregate_results(rows)
    metadata = {
        "samples": args.samples,
        "schedules": args.schedules,
        "run_time": args.run_time,
        "repeats": args.repeats,
        "seed": args.seed,
        "max_input_length": args.max_input_length,
    }

    (output_dir / "raw_results.json").write_text(
        json.dumps({"metadata": metadata, "runs": rows, "summary": summary}, indent=2),
        encoding="utf-8",
    )
    write_csv(output_dir / "raw_results.csv", rows)
    write_csv(output_dir / "summary.csv", summary)
    write_text_summary(output_dir / "summary.txt", summary)
    print(f"saved results to {output_dir.resolve()}")


if __name__ == "__main__":
    main()

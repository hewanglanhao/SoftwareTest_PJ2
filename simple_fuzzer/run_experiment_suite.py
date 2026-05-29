import argparse
from pathlib import Path

from compare_schedules import aggregate_results, run_once, write_csv, write_text_summary
from main import build_sample
from summarize_results import (
    build_report_bundle,
    format_markdown,
    load_comparison_bundle,
    load_single_run_records,
)
from utils.experiment import (
    COMPARISON_DIRNAME,
    REPORT_ASSETS_DIRNAME,
    SINGLE_RUN_DIRNAME,
    build_experiment_matrix,
    build_experiment_plan,
    build_run_record,
    experiment_run_dir,
    resolve_output_dir,
    serialize_population,
    single_run_stem,
)
from utils.object_utils import dump_json, dump_object, load_object
from utils.result import Result
from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer
from runner.function_coverage_runner import FunctionCoverageRunner
from schedule.registry import SCHEDULES, create_schedule
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Run the full experiment suite for final reports.")
    parser.add_argument("--label", default="official",
                        help="Experiment label used under _result/runs/")
    parser.add_argument("--samples", nargs="+", type=int, default=[1, 2, 3, 4],
                        choices=(1, 2, 3, 4), help="Sample ids to run")
    parser.add_argument("--schedules", nargs="+", default=["uniform", "path", "rare"],
                        choices=sorted(SCHEDULES), help="Schedules to compare")
    parser.add_argument("--run-time", type=int, default=60,
                        help="Seconds per sample/schedule/repeat")
    parser.add_argument("--repeats", type=int, default=3,
                        help="Repeated runs per sample/schedule")
    parser.add_argument("--seed", type=int, default=2026,
                        help="Base random seed")
    parser.add_argument("--max-input-length", type=int, default=4096,
                        help="Cap generated inputs to keep parser samples stable")
    parser.add_argument("--output-dir", default="_result",
                        help="Base result directory")
    parser.add_argument("--capture-single-runs", action="store_true",
                        help="Persist one representative single-run artifact per sample/schedule")
    parser.add_argument("--save-population", action="store_true",
                        help="Persist population snapshots for representative single runs")
    return parser.parse_args()


def save_single_run_artifacts(
    *,
    output_dir: Path,
    sample_id: int,
    schedule_name: str,
    run_time: int,
    max_input_length: int,
    save_population: bool,
):
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
    result = Result(
        fuzzer.covered_line,
        set(fuzzer.crash_map.values()),
        start_time,
        end_time,
        sample=sample_id,
        schedule=schedule_name,
        run_time=run_time,
        initial_seed_count=len(seeds),
        total_execs=fuzzer.total_execs,
        total_paths=fuzzer.total_paths,
    )

    stem = single_run_stem(sample_id, schedule_name)
    dump_object(str(output_dir / f"{stem}.pkl"), result)
    dump_json(str(output_dir / f"{stem}.json"), result.to_dict())
    (output_dir / f"{stem}.txt").write_text(str(result) + "\n", encoding="utf-8")

    if save_population:
        dump_json(
            str(output_dir / f"{stem}-population.json"),
            serialize_population(fuzzer.population),
        )

    return build_run_record(
        sample=sample_id,
        schedule=schedule_name,
        run_time=run_time,
        initial_seed_count=len(seeds),
        total_execs=fuzzer.total_execs,
        total_paths=fuzzer.total_paths,
        covered_line_count=len(fuzzer.covered_line),
        crash_count=len(set(fuzzer.crash_map.values())),
        start_time=start_time,
        end_time=end_time,
    )


def main():
    args = parse_args()
    run_dir = experiment_run_dir(args.output_dir, args.label)
    comparison_dir = resolve_output_dir(str(run_dir), COMPARISON_DIRNAME)
    single_dir = resolve_output_dir(str(run_dir), SINGLE_RUN_DIRNAME)
    report_dir = resolve_output_dir(str(run_dir), REPORT_ASSETS_DIRNAME)

    plan = build_experiment_plan(
        label=args.label,
        samples=args.samples,
        schedules=args.schedules,
        run_time=args.run_time,
        repeats=args.repeats,
        seed=args.seed,
        max_input_length=args.max_input_length,
        capture_single_runs=args.capture_single_runs,
        save_population=args.save_population,
    )
    matrix = build_experiment_matrix(args.samples, args.schedules, args.repeats)
    dump_json(str(run_dir / "experiment_plan.json"), {"plan": plan, "matrix": matrix})

    rows = []
    for sample_id in args.samples:
        for schedule_name in args.schedules:
            for repeat in range(args.repeats):
                run_seed = args.seed + sample_id * 1000 + repeat
                row = run_once(
                    sample_id=sample_id,
                    schedule_name=schedule_name,
                    run_time=args.run_time,
                    seed=run_seed,
                    max_input_length=args.max_input_length,
                )
                row["repeat"] = repeat
                rows.append(row)
                print(
                    f"sample={sample_id} schedule={schedule_name} repeat={repeat} "
                    f"execs={row['total_execs']} paths={row['total_paths']} "
                    f"covered={row['covered_line_count']} crashes={row['crash_count']}"
                )

    summary = aggregate_results(rows)
    comparison_bundle = {
        "metadata": {
            "samples": args.samples,
            "schedules": args.schedules,
            "run_time": args.run_time,
            "repeats": args.repeats,
            "seed": args.seed,
            "max_input_length": args.max_input_length,
            "label": args.label,
            "output_dir": str(run_dir),
        },
        "runs": rows,
        "summary": summary,
    }
    dump_json(str(comparison_dir / "raw_results.json"), comparison_bundle)
    write_csv(comparison_dir / "raw_results.csv", rows)
    write_csv(comparison_dir / "summary.csv", summary)
    write_text_summary(comparison_dir / "summary.txt", summary)

    representative_runs = []
    if args.capture_single_runs:
        for sample_id in args.samples:
            for schedule_name in args.schedules:
                representative_runs.append(
                    save_single_run_artifacts(
                        output_dir=single_dir,
                        sample_id=sample_id,
                        schedule_name=schedule_name,
                        run_time=args.run_time,
                        max_input_length=args.max_input_length,
                        save_population=args.save_population,
                    )
                )
        dump_json(str(single_dir / "single_run_index.json"), representative_runs)

    report_bundle = build_report_bundle(
        load_single_run_records(single_dir),
        load_comparison_bundle(comparison_dir),
    )
    dump_json(str(report_dir / "report_bundle.json"), report_bundle)
    write_csv(report_dir / "single_runs.csv", report_bundle["single_runs"])
    write_csv(report_dir / "comparison_summary.csv", report_bundle["comparison_summary"])
    (report_dir / "summary.md").write_text(format_markdown(report_bundle), encoding="utf-8")

    print(f"saved experiment suite to {run_dir.resolve()}")


if __name__ == "__main__":
    main()

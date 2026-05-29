import argparse
import json
import time

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer
from runner.function_coverage_runner import FunctionCoverageRunner
from schedule.registry import SCHEDULES, create_schedule
from samples.samples import sample1, sample2, sample3, sample4
from utils.experiment import (
    SINGLE_RUN_DIRNAME,
    build_run_record,
    resolve_output_dir,
    serialize_population,
    single_run_stem,
)
from utils.object_utils import dump_json, dump_object, load_object
from utils.result import Result


def build_sample(sample_id: int):
    sample_map = {
        1: (sample1, "corpus/corpus_1"),
        2: (sample2, "corpus/corpus_2"),
        3: (sample3, "corpus/corpus_3"),
        4: (sample4, "corpus/corpus_4"),
    }
    return sample_map[sample_id]


def parse_args():
    parser = argparse.ArgumentParser(description="Run the simple grey-box fuzzer demo.")
    parser.add_argument("--sample", type=int, default=4, choices=(1, 2, 3, 4),
                        help="Target sample program to fuzz")
    parser.add_argument("--run-time", type=int, default=300,
                        help="Fuzzing duration in seconds")
    parser.add_argument("--output-dir", default="_result",
                        help="Base directory used to persist run artifacts")
    parser.add_argument("--schedule", default="path", choices=sorted(SCHEDULES),
                        help="Seed scheduling strategy")
    parser.add_argument("--max-input-length", type=int, default=None,
                        help="Optional cap for generated inputs")
    parser.add_argument("--quiet", action="store_true",
                        help="Disable the status table output")
    parser.add_argument("--save-population", action="store_true",
                        help="Persist a final population snapshot for later analysis")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    target_function, corpus_path = build_sample(args.sample)

    f_runner = FunctionCoverageRunner(target_function)
    seeds = load_object(corpus_path)
    initial_seed_count = len(seeds)

    grey_fuzzer = PathGreyBoxFuzzer(
        seeds=seeds,
        schedule=create_schedule(args.schedule),
        is_print=not args.quiet,
        max_input_length=args.max_input_length,
    )
    start_time = time.time()
    grey_fuzzer.runs(f_runner, run_time=args.run_time)
    end_time = time.time()

    record = build_run_record(
        sample=args.sample,
        schedule=args.schedule,
        run_time=args.run_time,
        initial_seed_count=initial_seed_count,
        total_execs=grey_fuzzer.total_execs,
        total_paths=grey_fuzzer.total_paths,
        covered_line_count=len(grey_fuzzer.covered_line),
        crash_count=len(set(grey_fuzzer.crash_map.values())),
        start_time=start_time,
        end_time=end_time,
    )
    res = Result(
        grey_fuzzer.covered_line,
        set(grey_fuzzer.crash_map.values()),
        start_time,
        end_time,
        sample=args.sample,
        schedule=args.schedule,
        run_time=args.run_time,
        initial_seed_count=initial_seed_count,
        total_execs=grey_fuzzer.total_execs,
        total_paths=grey_fuzzer.total_paths,
    )

    output_dir = resolve_output_dir(args.output_dir, SINGLE_RUN_DIRNAME)
    stem = single_run_stem(args.sample, args.schedule)
    pkl_path = output_dir / f"{stem}.pkl"
    json_path = output_dir / f"{stem}.json"
    txt_path = output_dir / f"{stem}.txt"

    dump_object(str(pkl_path), res)
    dump_json(str(json_path), res.to_dict())
    txt_path.write_text(str(load_object(str(pkl_path))) + "\n", encoding="utf-8")

    if args.save_population:
        population_path = output_dir / f"{stem}-population.json"
        dump_json(str(population_path), serialize_population(grey_fuzzer.population))

    print(f"saved single-run artifacts to {output_dir.resolve()}")
    print(json.dumps(record, ensure_ascii=False, indent=2))

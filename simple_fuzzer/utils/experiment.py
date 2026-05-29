from pathlib import Path
from typing import Any, Dict, Iterable, List


SINGLE_RUN_DIRNAME = "single"
COMPARISON_DIRNAME = "comparison"
REPORT_ASSETS_DIRNAME = "report_assets"
RUNS_DIRNAME = "runs"


def resolve_output_dir(base_output_dir: str, category: str) -> Path:
    output_dir = Path(base_output_dir) / category
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_run_record(
    *,
    sample: int,
    schedule: str,
    run_time: int,
    initial_seed_count: int,
    total_execs: int,
    total_paths: int,
    covered_line_count: int,
    crash_count: int,
    start_time: float,
    end_time: float,
) -> Dict[str, Any]:
    return {
        "sample": sample,
        "schedule": schedule,
        "run_time": run_time,
        "initial_seed_count": initial_seed_count,
        "total_execs": total_execs,
        "total_paths": total_paths,
        "covered_line_count": covered_line_count,
        "crash_count": crash_count,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": round(end_time - start_time, 3),
    }


def single_run_stem(sample: int, schedule: str) -> str:
    return f"sample-{sample}-{schedule}"


def serialize_population(population) -> Dict[str, Any]:
    seeds = [
        {
            "data": seed.data,
            "energy": seed.energy,
            "coverage_size": len(seed.coverage),
        }
        for seed in population
    ]
    return {
        "population_size": len(seeds),
        "seeds": seeds,
    }


def experiment_run_dir(base_output_dir: str, label: str) -> Path:
    runs_root = resolve_output_dir(base_output_dir, RUNS_DIRNAME)
    run_dir = runs_root / label
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_experiment_plan(
    *,
    label: str,
    samples: Iterable[int],
    schedules: Iterable[str],
    run_time: int,
    repeats: int,
    seed: int,
    max_input_length: int,
    capture_single_runs: bool,
    save_population: bool,
) -> Dict[str, Any]:
    return {
        "label": label,
        "samples": list(samples),
        "schedules": list(schedules),
        "run_time": run_time,
        "repeats": repeats,
        "seed": seed,
        "max_input_length": max_input_length,
        "capture_single_runs": capture_single_runs,
        "save_population": save_population,
    }


def build_experiment_matrix(samples: Iterable[int], schedules: Iterable[str], repeats: int) -> List[Dict[str, int | str]]:
    matrix = []
    for sample in samples:
        for schedule in schedules:
            for repeat in range(repeats):
                matrix.append({
                    "sample": sample,
                    "schedule": schedule,
                    "repeat": repeat,
                })
    return matrix

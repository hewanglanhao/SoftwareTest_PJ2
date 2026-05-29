import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from compare_schedules import aggregate_results
from summarize_results import build_report_bundle, format_markdown
from utils.experiment import (
    build_experiment_matrix,
    build_experiment_plan,
    build_run_record,
    experiment_run_dir,
    resolve_output_dir,
    serialize_population,
    single_run_stem,
)
from utils.result import Result
from utils.seed import Seed


class ExperimentOutputTest(unittest.TestCase):

    def test_build_run_record_has_shared_fields(self):
        record = build_run_record(
            sample=4,
            schedule="path",
            run_time=60,
            initial_seed_count=3,
            total_execs=120,
            total_paths=10,
            covered_line_count=9,
            crash_count=2,
            start_time=10.0,
            end_time=16.2,
        )

        self.assertEqual(
            set(record),
            {
                "sample",
                "schedule",
                "run_time",
                "initial_seed_count",
                "total_execs",
                "total_paths",
                "covered_line_count",
                "crash_count",
                "start_time",
                "end_time",
                "duration_seconds",
            },
        )
        self.assertEqual(record["duration_seconds"], 6.2)

    def test_result_to_dict_matches_shared_fields(self):
        result = Result(
            {("target", 1), ("target", 2)},
            {"boom"},
            1.0,
            4.5,
            sample=2,
            schedule="uniform",
            run_time=30,
            initial_seed_count=4,
            total_execs=99,
            total_paths=7,
        )

        data = result.to_dict()
        self.assertEqual(data["sample"], 2)
        self.assertEqual(data["schedule"], "uniform")
        self.assertEqual(data["run_time"], 30)
        self.assertEqual(data["initial_seed_count"], 4)
        self.assertEqual(data["total_execs"], 99)
        self.assertEqual(data["total_paths"], 7)
        self.assertEqual(data["covered_line_count"], 2)
        self.assertEqual(data["crash_count"], 1)
        self.assertEqual(data["duration_seconds"], 3.5)

    def test_aggregate_results_preserves_shared_metadata(self):
        rows = [
            {
                "sample": 1,
                "schedule": "path",
                "run_time": 10,
                "initial_seed_count": 2,
                "total_execs": 100,
                "total_paths": 5,
                "covered_line_count": 8,
                "crash_count": 1,
                "start_time": 0.0,
                "end_time": 10.0,
                "duration_seconds": 10.0,
                "seed": 2026,
            },
            {
                "sample": 1,
                "schedule": "path",
                "run_time": 10,
                "initial_seed_count": 2,
                "total_execs": 120,
                "total_paths": 7,
                "covered_line_count": 9,
                "crash_count": 2,
                "start_time": 0.0,
                "end_time": 10.0,
                "duration_seconds": 10.0,
                "seed": 2027,
            },
        ]

        summary = aggregate_results(rows)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["run_time"], 10)
        self.assertEqual(summary[0]["initial_seed_count"], 2)
        self.assertEqual(summary[0]["avg_execs"], 110)

    def test_output_helpers_create_expected_names(self):
        base_dir = PROJECT_ROOT / "tmp-output-root"
        with patch("pathlib.Path.mkdir") as mocked_mkdir:
            output_dir = resolve_output_dir(str(base_dir), "single")
            self.assertEqual(output_dir, base_dir / "single")
            mocked_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        self.assertEqual(single_run_stem(3, "rare"), "sample-3-rare")

    def test_serialize_population_summarizes_seed_state(self):
        seeds = [
            Seed("alpha", {("target", 1)}),
            Seed("beta", {("target", 2), ("target", 3)}),
        ]
        seeds[0].energy = 0.5
        payload = serialize_population(seeds)

        self.assertEqual(payload["population_size"], 2)
        self.assertEqual(payload["seeds"][0]["data"], "alpha")
        self.assertEqual(payload["seeds"][0]["energy"], 0.5)
        self.assertEqual(payload["seeds"][1]["coverage_size"], 2)

    def test_report_bundle_and_markdown_include_both_sources(self):
        single_records = [
            build_run_record(
                sample=1,
                schedule="path",
                run_time=10,
                initial_seed_count=2,
                total_execs=100,
                total_paths=4,
                covered_line_count=7,
                crash_count=1,
                start_time=0.0,
                end_time=10.0,
            )
        ]
        comparison_bundle = {
            "metadata": {"run_time": 10},
            "runs": [{"sample": 1}],
            "summary": [{
                "sample": 1,
                "schedule": "path",
                "runs": 1,
                "run_time": 10,
                "initial_seed_count": 2,
                "avg_execs": 100,
                "avg_paths": 4,
                "avg_covered_lines": 7,
                "avg_crashes": 1,
                "avg_duration_seconds": 10.0,
            }],
        }

        bundle = build_report_bundle(single_records, comparison_bundle)
        markdown = format_markdown(bundle)

        self.assertEqual(bundle["single_run_count"], 1)
        self.assertIn("## Single Runs", markdown)
        self.assertIn("## Comparison Summary", markdown)
        self.assertIn("| 1 | path | 10 | 2 | 7 | 1 | 4 | 100 | 10.0 |", markdown)

    def test_build_experiment_plan_and_matrix(self):
        plan = build_experiment_plan(
            label="official",
            samples=[1, 2],
            schedules=["uniform", "path"],
            run_time=60,
            repeats=2,
            seed=2026,
            max_input_length=4096,
            capture_single_runs=True,
            save_population=False,
        )
        matrix = build_experiment_matrix([1, 2], ["uniform", "path"], 2)

        self.assertEqual(plan["label"], "official")
        self.assertEqual(plan["samples"], [1, 2])
        self.assertEqual(plan["schedules"], ["uniform", "path"])
        self.assertEqual(len(matrix), 8)
        self.assertEqual(matrix[0], {"sample": 1, "schedule": "uniform", "repeat": 0})
        self.assertEqual(matrix[-1], {"sample": 2, "schedule": "path", "repeat": 1})

    def test_experiment_run_dir_nests_under_runs_root(self):
        base_dir = PROJECT_ROOT / "tmp-output-root"
        with patch("pathlib.Path.mkdir") as mocked_mkdir:
            run_dir = experiment_run_dir(str(base_dir), "official")
            self.assertEqual(run_dir, base_dir / "runs" / "official")
            self.assertEqual(mocked_mkdir.call_count, 2)


if __name__ == "__main__":
    unittest.main()

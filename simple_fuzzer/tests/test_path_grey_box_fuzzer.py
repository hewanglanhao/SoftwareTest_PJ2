import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer
from runner.function_coverage_runner import FunctionCoverageRunner
from schedule.path_power_schedule import PathPowerSchedule


def _simple_target(inp: str) -> str:
    if "hello" in inp:
        return "greeting"
    if "42" in inp:
        return "answer"
    if "test" in inp:
        return "testing"
    return "unknown"


class PathGreyBoxFuzzerTest(unittest.TestCase):

    def setUp(self):
        self.seeds = ["hello", "42", "test", "unknown"]
        self.schedule = PathPowerSchedule()
        self.fuzzer = PathGreyBoxFuzzer(
            seeds=self.seeds,
            schedule=self.schedule,
            is_print=False,
        )

    def test_init_sets_last_path_time(self):
        self.assertAlmostEqual(
            self.fuzzer.last_path_time,
            self.fuzzer.start_time,
            delta=0.1,
        )

    def test_init_sets_total_paths_to_zero(self):
        self.assertEqual(self.fuzzer.total_paths, 0)

    def test_run_populates_path_frequency(self):
        runner = FunctionCoverageRunner(_simple_target)
        for _ in range(10):
            self.fuzzer.run(runner)

        self.assertGreater(len(self.schedule.path_frequency), 0)

    def test_run_updates_total_paths(self):
        runner = FunctionCoverageRunner(_simple_target)
        for _ in range(10):
            self.fuzzer.run(runner)

        self.assertEqual(
            self.fuzzer.total_paths,
            len(self.schedule.path_frequency),
        )

    def test_run_finds_new_paths(self):
        runner = FunctionCoverageRunner(_simple_target)
        initial_paths = self.fuzzer.total_paths
        self.fuzzer.run(runner)
        self.assertGreaterEqual(
            self.fuzzer.total_paths,
            initial_paths,
        )

    def test_print_stats_does_not_raise(self):
        runner = FunctionCoverageRunner(_simple_target)
        for _ in range(5):
            self.fuzzer.run(runner)
        try:
            self.fuzzer.print_stats()
        except Exception:
            self.fail("print_stats raised unexpectedly")

    def test_runs_does_not_raise(self):
        runner = FunctionCoverageRunner(_simple_target)
        try:
            self.fuzzer.runs(runner, run_time=1)
        except Exception:
            self.fail("runs raised unexpectedly")

    def test_recorded_paths_match_population_seeds(self):
        runner = FunctionCoverageRunner(_simple_target)
        for _ in range(20):
            self.fuzzer.run(runner)

        for seed in self.fuzzer.population:
            path_id = hash(frozenset(seed.coverage))
            self.assertIn(path_id, self.schedule.path_frequency)

    def test_all_paths_have_positive_frequency(self):
        runner = FunctionCoverageRunner(_simple_target)
        for _ in range(20):
            self.fuzzer.run(runner)

        for freq in self.schedule.path_frequency.values():
            self.assertGreater(freq, 0)

    def test_total_paths_never_decreases(self):
        runner = FunctionCoverageRunner(_simple_target)
        previous = self.fuzzer.total_paths
        for _ in range(50):
            self.fuzzer.run(runner)
            self.assertGreaterEqual(self.fuzzer.total_paths, previous)
            previous = self.fuzzer.total_paths


if __name__ == "__main__":
    unittest.main()

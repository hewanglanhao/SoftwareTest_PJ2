import time
from typing import List, Tuple, Any

from fuzzer.grey_box_fuzzer import GreyBoxFuzzer
from schedule.power_schedule import PowerSchedule
from runner.function_coverage_runner import FunctionCoverageRunner


class PathGreyBoxFuzzer(GreyBoxFuzzer):
    """Count how often individual paths are exercised."""

    def __init__(self, seeds: List[str], schedule: PowerSchedule, is_print: bool,
                 max_input_length: int = None):
        super().__init__(seeds, schedule, False, max_input_length=max_input_length)
        self.is_print = is_print
        self.last_path_time = self.start_time
        self.total_paths = 0
        self.seen_paths = set()
        if self.is_print:
            print("""
┌───────────────────────┬───────────────────────┬───────────────────────┬───────────────────┬───────────────────┬────────────────┬───────────────────┐
│        Run Time       │     Last New Path     │    Last Uniq Crash    │    Total Execs    │    Total Paths    │  Uniq Crashes  │   Covered Lines   │
├───────────────────────┼───────────────────────┼───────────────────────┼───────────────────┼───────────────────┼────────────────┼───────────────────┤""")

    def print_stats(self):
        if not self.is_print:
            return

        def format_seconds(seconds):
            hours = int(seconds) // 3600
            minutes = int(seconds % 3600) // 60
            remaining_seconds = int(seconds) % 60
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

        template = """│{runtime}│{path_time}│{crash_time}│{total_exec}│{total_path}│{uniq_crash}│{covered_line}│
├───────────────────────┼───────────────────────┼───────────────────────┼───────────────────┼───────────────────┼────────────────┼───────────────────┤"""
        template = template.format(runtime=format_seconds(time.time() - self.start_time).center(23),
                                   path_time=format_seconds(self.last_path_time - self.start_time).center(23),
                                   crash_time=format_seconds(self.last_crash_time - self.start_time).center(23),
                                   total_exec=str(self.total_execs).center(19),
                                   total_path=str(self.total_paths).center(19),
                                   uniq_crash=str(len(set(self.crash_map.values()))).center(16),
                                   covered_line=str(len(self.covered_line)).center(19))
        print(template)

    def run(self, runner: FunctionCoverageRunner) -> Tuple[Any, str]:  # type: ignore
        old_population_size = len(self.population)
        result, outcome = super().run(runner)

        if len(self.population) > old_population_size:
            self.last_path_time = time.time()

        coverage = runner.coverage()
        path_id = hash(frozenset(coverage))
        if path_id not in self.seen_paths:
            # fuzzer 自身维护唯一路径数，方便所有调度策略共享同一套统计输出。
            self.seen_paths.add(path_id)
            self.last_path_time = time.time()

        record_path = getattr(self.schedule, "record_path", None)
        if record_path is not None:
            # 只有需要运行反馈的调度器才实现 record_path，例如 path 和 rare。
            record_path(coverage)

        self.total_paths = len(self.seen_paths)

        return result, outcome

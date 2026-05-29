from typing import Any, Dict, Iterable, Optional, Tuple


class Result:
    def __init__(
        self,
        coverage,
        crashes,
        start_time,
        end_time,
        *,
        sample: Optional[int] = None,
        schedule: Optional[str] = None,
        run_time: Optional[int] = None,
        initial_seed_count: Optional[int] = None,
        total_execs: int = 0,
        total_paths: int = 0,
    ):
        self.covered_line = coverage
        self.crashes = crashes
        self.start_time = start_time
        self.end_time = end_time
        self.sample = sample
        self.schedule = schedule
        self.run_time = run_time
        self.initial_seed_count = initial_seed_count
        self.total_execs = total_execs
        self.total_paths = total_paths

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "covered_line_count": len(self.covered_line),
            "covered_lines": _sorted_locations(self.covered_line),
            "crash_count": len(self.crashes),
            "crashes": sorted(str(crash) for crash in self.crashes),
            "sample": self.sample,
            "schedule": self.schedule,
            "run_time": self.run_time,
            "initial_seed_count": self.initial_seed_count,
            "total_execs": self.total_execs,
            "total_paths": self.total_paths,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": round(self.duration, 3),
        }

    def __str__(self):
        data = self.to_dict()
        return (
            f"Sample: {data['sample']}, Schedule: {data['schedule']}, "
            f"Covered Lines: {data['covered_line_count']}, Crashes: {data['crash_count']}, "
            f"Paths: {data['total_paths']}, Execs: {data['total_execs']}, "
            f"Duration: {data['duration_seconds']}s"
        )


def _sorted_locations(locations: Iterable[Tuple[str, int]]):
    return [
        {"function": function, "line": line}
        for function, line in sorted(locations, key=lambda item: (str(item[0]), item[1]))
    ]

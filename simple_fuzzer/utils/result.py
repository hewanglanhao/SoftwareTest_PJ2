from typing import Any, Dict, Iterable, Tuple


class Result:
    def __init__(self, coverage, crashes, start_time, end_time):
        self.covered_line = coverage
        self.crashes = crashes
        self.start_time = start_time
        self.end_time = end_time

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "covered_line_count": len(self.covered_line),
            "covered_lines": _sorted_locations(self.covered_line),
            "crash_count": len(self.crashes),
            "crashes": sorted(str(crash) for crash in self.crashes),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration,
        }

    def __str__(self):
        return (
            "Covered Lines: "
            + str(self.covered_line)
            + ", Crashes Num: "
            + str(self.crashes)
            + ", Start Time: "
            + str(self.start_time)
            + ", End Time: "
            + str(self.end_time)
        )


def _sorted_locations(locations: Iterable[Tuple[str, int]]):
    return [
        {"function": function, "line": line}
        for function, line in sorted(locations, key=lambda item: (str(item[0]), item[1]))
    ]

from schedule.coverage_power_schedule import CoveragePowerSchedule
from schedule.length_power_schedule import LengthPowerSchedule
from schedule.path_power_schedule import PathPowerSchedule
from schedule.power_schedule import PowerSchedule
from schedule.rare_coverage_schedule import RareCoverageSchedule


# 统一注册所有可比较的调度策略，main.py 和实验脚本都从这里创建实例。
SCHEDULES = {
    "uniform": PowerSchedule,
    "path": PathPowerSchedule,
    "coverage": CoveragePowerSchedule,
    "rare": RareCoverageSchedule,
    "length": LengthPowerSchedule,
}


def create_schedule(name: str):
    try:
        return SCHEDULES[name]()
    except KeyError as exc:
        choices = ", ".join(sorted(SCHEDULES))
        raise ValueError(f"unknown schedule {name!r}; choose from: {choices}") from exc

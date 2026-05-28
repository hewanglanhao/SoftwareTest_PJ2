from typing import Sequence

from schedule.power_schedule import PowerSchedule
from utils.seed import Seed


class CoveragePowerSchedule(PowerSchedule):
    """Prefer seeds that already reached more code locations."""

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            # 覆盖位置越多，说明该 seed 触发的逻辑越丰富，后续更值得继续变异。
            seed.energy = 1.0 + len(seed.coverage)

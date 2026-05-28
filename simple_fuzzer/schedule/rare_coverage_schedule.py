from typing import Dict, Sequence, Set

from schedule.power_schedule import PowerSchedule
from utils.coverage import Location
from utils.seed import Seed


class RareCoverageSchedule(PowerSchedule):
    """Prefer seeds that cover locations seen less often during fuzzing."""

    def __init__(self) -> None:
        self.location_frequency: Dict[Location, int] = {}

    def record_path(self, coverage: Set[Location]) -> None:
        # 记录每个代码位置被命中的次数，用于判断哪些覆盖点更稀有。
        for location in coverage:
            self.location_frequency[location] = self.location_frequency.get(location, 0) + 1

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            if not seed.coverage:
                seed.energy = 1.0
                continue

            # 低频覆盖点贡献更高权重，鼓励继续探索少见区域。
            rarity = sum(
                1.0 / self.location_frequency.get(location, 1)
                for location in seed.coverage
            )
            seed.energy = max(rarity, 0.01)

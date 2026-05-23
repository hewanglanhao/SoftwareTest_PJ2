from typing import Dict, Sequence, Set

from schedule.power_schedule import PowerSchedule
from utils.coverage import Location
from utils.seed import Seed


class PathPowerSchedule(PowerSchedule):

    def __init__(self) -> None:
        super().__init__()
        self.path_frequency: Dict[int, int] = {}

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            path_id = hash(frozenset(seed.coverage))
            freq = self.path_frequency.get(path_id, 1)
            seed.energy = 1.0 / freq if freq > 0 else 1.0

    def record_path(self, coverage: Set[Location]) -> None:
        path_id = hash(frozenset(coverage))
        self.path_frequency[path_id] = self.path_frequency.get(path_id, 0) + 1

import math
from typing import Sequence

from schedule.power_schedule import PowerSchedule
from utils.seed import Seed


class LengthPowerSchedule(PowerSchedule):
    """Prefer compact seeds, which usually execute faster and mutate cheaply."""

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            # 用平方根做温和惩罚：偏向短输入，但不完全排斥长输入。
            seed.energy = 1.0 / math.sqrt(len(seed.data) + 1)

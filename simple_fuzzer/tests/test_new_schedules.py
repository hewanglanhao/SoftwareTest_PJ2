import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schedule.coverage_power_schedule import CoveragePowerSchedule
from schedule.length_power_schedule import LengthPowerSchedule
from schedule.rare_coverage_schedule import RareCoverageSchedule
from schedule.registry import SCHEDULES, create_schedule
from utils.seed import Seed


class NewSchedulesTest(unittest.TestCase):

    def setUp(self):
        self.coverage_a = {("target", 1), ("target", 2), ("target", 3)}
        self.coverage_b = {("target", 1)}

    def test_coverage_schedule_prefers_more_covered_locations(self):
        seed_a = Seed("a", self.coverage_a)
        seed_b = Seed("b", self.coverage_b)
        CoveragePowerSchedule().assign_energy([seed_a, seed_b])
        self.assertGreater(seed_a.energy, seed_b.energy)

    def test_rare_schedule_prefers_rare_locations(self):
        schedule = RareCoverageSchedule()
        schedule.record_path(self.coverage_b)
        schedule.record_path(self.coverage_b)
        schedule.record_path(self.coverage_a)

        rare_seed = Seed("rare", {("target", 3)})
        common_seed = Seed("common", {("target", 1)})
        schedule.assign_energy([rare_seed, common_seed])

        self.assertGreater(rare_seed.energy, common_seed.energy)

    def test_length_schedule_prefers_shorter_inputs(self):
        short_seed = Seed("x", self.coverage_a)
        long_seed = Seed("x" * 100, self.coverage_a)
        LengthPowerSchedule().assign_energy([short_seed, long_seed])
        self.assertGreater(short_seed.energy, long_seed.energy)

    def test_registry_contains_all_comparison_schedules(self):
        self.assertEqual(
            set(SCHEDULES),
            {"uniform", "path", "coverage", "rare", "length"},
        )
        for name in SCHEDULES:
            self.assertIsInstance(create_schedule(name), SCHEDULES[name])

    def test_choose_uses_new_schedule_energy(self):
        random.seed(2026)
        schedule = CoveragePowerSchedule()
        high = Seed("high", self.coverage_a)
        low = Seed("low", self.coverage_b)
        choices = [schedule.choose([high, low]).data for _ in range(200)]
        self.assertGreater(choices.count("high"), choices.count("low"))


if __name__ == "__main__":
    unittest.main()

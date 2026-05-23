import sys
import unittest
from pathlib import Path
from typing import Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schedule.path_power_schedule import PathPowerSchedule
from utils.seed import Seed


class PathPowerScheduleTest(unittest.TestCase):

    def setUp(self):
        self.schedule = PathPowerSchedule()
        self.coverage_a: Set = {("func", 1), ("func", 2)}
        self.coverage_b: Set = {("func", 3), ("func", 4)}
        self.coverage_c: Set = {("func", 1), ("func", 5)}

    def test_record_path_increments_frequency(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        total = sum(self.schedule.path_frequency.values())
        self.assertEqual(total, 3)

    def test_record_path_tracks_unique_paths_separately(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)
        self.schedule.record_path(self.coverage_a)
        self.assertEqual(len(self.schedule.path_frequency), 2)

    def test_record_path_returns_after_each_call(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)

        path_id = hash(frozenset(self.coverage_a))
        self.assertEqual(self.schedule.path_frequency[path_id], 2)

    def test_assign_energy_high_freq_seed_gets_low_energy(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)

        seed_a = Seed("input_a", self.coverage_a)
        seed_b = Seed("input_b", self.coverage_b)

        population = [seed_a, seed_b]
        self.schedule.assign_energy(population)

        self.assertLess(seed_a.energy, seed_b.energy)

    def test_assign_energy_unknown_path_gets_default_energy(self):
        seed = Seed("unknown", self.coverage_a)
        self.schedule.assign_energy([seed])
        self.assertEqual(seed.energy, 1.0)

    def test_assign_energy_zero_frequency_falls_back_to_one(self):
        seed = Seed("zero", self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        path_id = hash(frozenset(self.coverage_a))
        self.schedule.path_frequency[path_id] = 0

        self.schedule.assign_energy([seed])
        self.assertEqual(seed.energy, 1.0)

    def test_assign_energy_empty_population_does_not_raise(self):
        try:
            self.schedule.assign_energy([])
        except Exception:
            self.fail("assign_energy raised on empty population")

    def test_assign_energy_twice_produces_same_result(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)

        seed = Seed("input_a", self.coverage_a)
        self.schedule.assign_energy([seed])
        energy_first = seed.energy

        self.schedule.assign_energy([seed])
        energy_second = seed.energy

        self.assertEqual(energy_first, energy_second)

    def test_assign_energy_all_seeds_get_positive_energy(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)
        self.schedule.record_path(self.coverage_c)

        seeds = [
            Seed("a", self.coverage_a),
            Seed("b", self.coverage_b),
            Seed("c", self.coverage_c),
        ]
        self.schedule.assign_energy(seeds)

        for seed in seeds:
            self.assertGreater(seed.energy, 0)

    def test_record_path_different_coverage_same_path_same_frequency(self):
        self.schedule.record_path({("x", 1)})
        self.schedule.record_path({("x", 1)})
        path_id = hash(frozenset({("x", 1)}))
        self.assertEqual(self.schedule.path_frequency[path_id], 2)

    def test_record_path_empty_coverage(self):
        self.schedule.record_path(set())
        path_id = hash(frozenset())
        self.assertEqual(self.schedule.path_frequency[path_id], 1)

    def test_assign_energy_inversely_proportional_ratio(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)

        seed_a = Seed("a", self.coverage_a)
        seed_b = Seed("b", self.coverage_b)

        self.schedule.assign_energy([seed_a, seed_b])

        self.assertAlmostEqual(seed_a.energy, 1.0 / 2)
        self.assertAlmostEqual(seed_b.energy, 1.0 / 1)

    def test_assign_energy_with_all_paths_seen_once(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)

        seed_a = Seed("a", self.coverage_a)
        seed_b = Seed("b", self.coverage_b)

        self.schedule.assign_energy([seed_a, seed_b])

        self.assertEqual(seed_a.energy, seed_b.energy)

    def test_choose_selects_higher_energy_seed_more_often(self):
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_a)
        self.schedule.record_path(self.coverage_b)

        seed_a = Seed("a", self.coverage_a)
        seed_b = Seed("b", self.coverage_b)

        import random
        random.seed(42)

        population = [seed_a, seed_b]
        self.schedule.assign_energy(population)

        self.assertLess(seed_a.energy, seed_b.energy)

        choices = [self.schedule.choose(population) for _ in range(1000)]
        count_b = sum(1 for c in choices if c.data == "b")
        count_a = 1000 - count_b
        self.assertGreater(count_b, count_a)


if __name__ == "__main__":
    unittest.main()

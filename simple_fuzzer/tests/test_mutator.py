import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.mutator import (  # noqa: E402
    Mutator,
    arithmetic_random_bytes,
    delete_random_block,
    delete_random_character,
    duplicate_random_block,
    flip_random_bits,
    havoc_random_insert,
    havoc_random_replace,
    insert_random_character,
    insert_structure_pair,
    interesting_random_bytes,
    mutate_numeric_token,
    overwrite_with_dictionary_token,
    random_block_swap,
    repeat_interesting_token,
    replace_random_character,
)


class MutatorTest(unittest.TestCase):
    def setUp(self):
        random.seed(2026)
        self.inputs = ["", "a", "abc", "123.abc", "FDUPLAB", "<html></html>", "中文输入"]
        self.mutators = [
            insert_random_character,
            replace_random_character,
            delete_random_character,
            delete_random_block,
            duplicate_random_block,
            insert_structure_pair,
            repeat_interesting_token,
            flip_random_bits,
            arithmetic_random_bytes,
            interesting_random_bytes,
            overwrite_with_dictionary_token,
            mutate_numeric_token,
            havoc_random_insert,
            havoc_random_replace,
            random_block_swap,
        ]

    def test_each_mutator_returns_string_without_exception(self):
        for mutator in self.mutators:
            for value in self.inputs:
                with self.subTest(mutator=mutator.__name__, value=value):
                    self.assertIsInstance(mutator(value), str)

    def test_mutator_keeps_empty_input_usable(self):
        mutator = Mutator()
        outputs = [mutator.mutate("") for _ in range(100)]
        self.assertTrue(all(isinstance(output, str) for output in outputs))
        self.assertTrue(any(output for output in outputs))

    def test_mutator_generates_diverse_outputs(self):
        mutator = Mutator()
        seed = "123.abc"
        outputs = {mutator.mutate(seed) for _ in range(200)}
        self.assertGreaterEqual(len(outputs), 30)
        self.assertTrue(any(output != seed for output in outputs))

    def test_dictionary_mutation_can_inject_branch_tokens(self):
        branch_tokens = ["FDU", "FDUPLAB", "<html>", "{Key}", "NaN"]
        for token in branch_tokens:
            with self.subTest(token=token):
                with patch("utils.mutator.random.choice", return_value=token):
                    self.assertIn(token, overwrite_with_dictionary_token(""))

    def test_mutator_converts_non_string_inputs(self):
        mutator = Mutator()
        for value in [123, 3.14, None, ["FDU"]]:
            with self.subTest(value=value):
                self.assertIsInstance(mutator.mutate(value), str)

    def test_registered_strategies_cover_expected_mutation_families(self):
        strategy_names = {mutator.__name__ for mutator in Mutator().mutators}
        expected_names = {
            "insert_random_character",
            "replace_random_character",
            "delete_random_character",
            "delete_random_block",
            "duplicate_random_block",
            "insert_structure_pair",
            "repeat_interesting_token",
            "flip_random_bits",
            "arithmetic_random_bytes",
            "interesting_random_bytes",
            "overwrite_with_dictionary_token",
            "mutate_numeric_token",
            "havoc_random_insert",
            "havoc_random_replace",
            "random_block_swap",
        }
        self.assertEqual(strategy_names, expected_names)
        self.assertEqual(strategy_names, set(Mutator().strategy_names()))

    def test_mutate_with_strategy_reports_registered_strategy_name(self):
        mutator = Mutator()
        output, strategy_name = mutator.mutate_with_strategy("123.abc")
        self.assertIsInstance(output, str)
        self.assertIn(strategy_name, {strategy.__name__ for strategy in mutator.mutators})

    def test_numeric_mutation_targets_existing_number(self):
        with patch("utils.mutator.NUMERIC_BOUNDARY_TOKENS", ["2147483647"]):
            self.assertEqual(mutate_numeric_token("abc123.def"), "abc2147483647.def")

    def test_numeric_mutation_inserts_boundary_when_no_number_exists(self):
        with patch("utils.mutator.NUMERIC_BOUNDARY_TOKENS", ["NaN"]):
            output = mutate_numeric_token("abc")
        self.assertIn("NaN", output)

    def test_structure_pair_mutation_can_create_html_fragment(self):
        with patch("utils.mutator.STRUCTURE_PAIRS", [("<html>", "</html>")]):
            output = insert_structure_pair("body")
        self.assertIn("<html>", output)
        self.assertIn("</html>", output)

    def test_repeat_token_mutation_can_amplify_branch_token(self):
        with patch("utils.mutator.REPEATABLE_TOKENS", ["FDU"]):
            output = repeat_interesting_token("LAB")
        self.assertIn("FDUFDU", output)

    def test_generate_examples_is_reproducible(self):
        mutator = Mutator()
        examples_1 = mutator.generate_examples("123.abc", count=5, seed=2026)
        examples_2 = mutator.generate_examples("123.abc", count=5, seed=2026)
        self.assertEqual(examples_1, examples_2)
        self.assertEqual(len(examples_1), 5)
        self.assertTrue(all(isinstance(value, str) and isinstance(name, str) for value, name in examples_1))

    def test_generate_examples_rejects_negative_count(self):
        with self.assertRaises(ValueError):
            Mutator().generate_examples("abc", count=-1)

    def test_generate_examples_restores_random_state_when_seeded(self):
        random.seed(99)
        expected = random.random()
        random.seed(99)
        Mutator().generate_examples("abc", count=3, seed=2026)
        self.assertEqual(random.random(), expected)


if __name__ == "__main__":
    unittest.main()

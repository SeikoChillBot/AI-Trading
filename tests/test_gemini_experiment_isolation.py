"""Malformed narrative experiments must not discard otherwise valid Gemini research."""
import unittest
from unittest.mock import patch
from research.ai_reflection import validate_with_experiment_isolation


class ExperimentIsolationTests(unittest.TestCase):
    def test_invalid_experiment_is_dropped_and_remaining_fields_are_validated(self):
        bad = {"asset": "BTCUSD", "title": "short", "hypothesis": "valid hypothesis",
               "experiment": "valid experiment", "rejection_rule": "valid rejection"}
        good = dict(bad, title="A properly descriptive experiment title")
        original = {"summary": "Model authored research", "experiments": [bad, good],
                    "strategy_designs": [{"asset": "ETHUSD"}]}
        def validator(ideas, evidence):
            self.assertEqual(ideas["strategy_designs"], original["strategy_designs"])
            if any(len(x["title"]) < 8 for x in ideas["experiments"]):
                raise ValueError("Missing or oversized experiment field")
            return ideas
        with patch("research.ai_reflection.validate_model_ideas", side_effect=validator):
            result = validate_with_experiment_isolation(original, {"BTCUSD": {}})
        self.assertEqual(result["experiments"], [good])
        self.assertEqual(len(original["experiments"]), 2)

    def test_other_validation_errors_are_not_bypassed(self):
        with patch("research.ai_reflection.validate_model_ideas",
                   side_effect=ValueError("Strategy outside approved research grammar")):
            with self.assertRaisesRegex(ValueError, "Strategy outside"):
                validate_with_experiment_isolation({"experiments": []}, {})

    def test_invalid_assets_are_not_reintroduced(self):
        bad = {"asset": "UNKNOWN", "title": "A proper title",
               "hypothesis": "A valid hypothesis", "experiment": "A valid experiment",
               "rejection_rule": "A valid rejection rule"}
        def validator(ideas, evidence):
            if len(ideas["experiments"]) > 0:
                raise ValueError("Missing or oversized experiment field")
            return ideas
        with patch("research.ai_reflection.validate_model_ideas", side_effect=validator):
            result = validate_with_experiment_isolation({"experiments": [bad]}, {"BTCUSD": {}})
        self.assertEqual(result["experiments"], [])


if __name__ == "__main__":
    unittest.main()

"""Regression checks for sanitized Gemini schema diagnostics."""
import unittest

from research.ai_reflection import schema_rejection_code


class SchemaDiagnosticsTests(unittest.TestCase):
    def test_known_failure_is_classified(self):
        self.assertEqual(
            schema_rejection_code(ValueError("Strategy outside approved research grammar")),
            "invalid_research_schema_design_grammar",
        )

    def test_unknown_failure_never_leaks_content(self):
        sensitive = "private-response-content-123"
        result = schema_rejection_code(ValueError(sensitive))
        self.assertEqual(result, "invalid_research_schema_unknown")
        self.assertNotIn(sensitive, result)

    def test_missing_fields_are_distinct(self):
        self.assertEqual(
            schema_rejection_code(ValueError("Missing or oversized experiment field")),
            "invalid_research_schema_experiment_fields",
        )


if __name__ == "__main__":
    unittest.main()
